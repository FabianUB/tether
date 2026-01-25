import { getConfig, getApiUrl } from './config.js';
import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  ApiError,
  ModelInfo,
} from './types.js';

/**
 * API client error
 */
export class TetherApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'TetherApiError';
  }
}

/**
 * Fetch wrapper with error handling and timeout
 */
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const config = getConfig();
  const url = getApiUrl(path);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        error: 'Unknown error',
        status_code: response.status,
      }));
      throw new TetherApiError(
        error.error,
        error.status_code || response.status,
        error.detail
      );
    }

    return response.json();
  } catch (error) {
    if (error instanceof TetherApiError) {
      throw error;
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new TetherApiError('Request timeout', 408);
    }
    throw new TetherApiError(
      error instanceof Error ? error.message : 'Network error',
      0
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Check backend health
 */
export async function checkHealth(): Promise<HealthResponse> {
  const config = getConfig();
  return apiFetch<HealthResponse>(config.healthEndpoint);
}

/**
 * Wait for backend to become healthy with retries
 */
export async function waitForBackend(): Promise<boolean> {
  const config = getConfig();

  for (let i = 0; i < config.maxRetries; i++) {
    try {
      const health = await checkHealth();
      if (health.status === 'healthy') {
        return true;
      }
    } catch {
      // Continue retrying
    }
    await new Promise((resolve) => setTimeout(resolve, config.retryDelay));
  }

  return false;
}

/**
 * Send a chat completion request
 */
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get model information
 */
export async function getModelInfo(): Promise<ModelInfo> {
  return apiFetch<ModelInfo>('/model');
}

/**
 * Create a typed API client instance
 */
export function createApiClient() {
  return {
    checkHealth,
    waitForBackend,
    chat,
    getModelInfo,
    fetch: apiFetch,
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
