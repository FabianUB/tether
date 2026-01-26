import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

// Types
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  images?: string[];
  thinking?: string;
  timestamp?: number;
}

export interface ChatRequest {
  message: string;
  images?: string[];
  history?: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  think?: boolean;
}

export interface ChatResponse {
  response: string;
  thinking?: string;
  tokens_used?: number;
  model?: string;
  finish_reason?: 'stop' | 'length' | 'error';
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  model_loaded: boolean;
  version: string;
}

export interface ModelsResponse {
  available: boolean;
  current_model: string | null;
  models: string[];
  backend: string;
  error: string | null;
}

export interface SwitchModelResponse {
  success: boolean;
  previous_model: string | null;
  current_model: string;
  message: string;
}

export type ConnectionStatus = 'connecting' | 'loading-model' | 'connected' | 'disconnected' | 'error';

// Configuration
let API_URL = 'http://127.0.0.1:8000';
const MAX_RETRIES = 30;
const RETRY_DELAY = 1000;
const REQUEST_TIMEOUT = 120000; // 2 minutes for thinking models
const HEALTH_CHECK_INTERVAL = 10000; // Check health every 10 seconds

// Get the API port from Tauri
async function getApiUrl(): Promise<string> {
  try {
    const port = await invoke<number>('get_api_port');
    API_URL = `http://127.0.0.1:${port}`;
    return API_URL;
  } catch {
    // Fallback for development without Tauri
    return API_URL;
  }
}

// API functions
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

async function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

async function fetchModels(): Promise<ModelsResponse> {
  return apiFetch<ModelsResponse>('/models');
}

async function switchModel(model: string): Promise<SwitchModelResponse> {
  return apiFetch<SwitchModelResponse>('/models/switch', {
    method: 'POST',
    body: JSON.stringify({ model }),
  });
}

async function waitForBackend(): Promise<boolean> {
  // First, get the correct API URL from Tauri
  await getApiUrl();

  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const health = await checkHealth();
      if (health.status === 'healthy') {
        return true;
      }
    } catch {
      // Continue retrying
    }
    await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
  }
  return false;
}

async function sendChatRequest(request: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Hooks
export function useBackendStatus() {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelsResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;
    let healthCheckInterval: ReturnType<typeof setInterval> | null = null;

    const connect = async () => {
      setStatus('connecting');
      setError(null);

      try {
        const ready = await waitForBackend();
        if (!mounted) return;

        if (ready) {
          // Backend is reachable, now check model status
          setStatus('loading-model');

          const [healthData, modelsData] = await Promise.all([
            checkHealth(),
            fetchModels().catch(() => null),
          ]);
          if (!mounted) return;
          setHealth(healthData);
          setModelInfo(modelsData);

          // Check if model is loaded
          if (healthData.model_loaded) {
            setStatus('connected');
          } else if (modelsData?.error) {
            setStatus('error');
            setError(new Error(modelsData.error));
          } else {
            // Model not loaded but no error - still connected
            setStatus('connected');
          }

          // Start periodic health checks
          healthCheckInterval = setInterval(async () => {
            if (!mounted) return;
            try {
              const healthData = await checkHealth();
              if (!mounted) return;
              setHealth(healthData);
              // If we were disconnected but now healthy, reconnect
              setStatus((prev) => prev === 'disconnected' ? 'connected' : prev);
            } catch {
              if (!mounted) return;
              setStatus('disconnected');
              setError(new Error('Lost connection to backend'));
            }
          }, HEALTH_CHECK_INTERVAL);
        } else {
          setStatus('error');
          setError(new Error('Backend failed to start. Check terminal for errors.'));
        }
      } catch (err) {
        if (!mounted) return;
        setStatus('error');
        setError(err instanceof Error ? err : new Error('Connection failed'));
      }
    };

    connect();

    return () => {
      mounted = false;
      if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
      }
    };
  }, []);

  const retry = useCallback(async () => {
    setStatus('connecting');
    setError(null);

    try {
      const ready = await waitForBackend();
      if (ready) {
        const [healthData, modelsData] = await Promise.all([
          checkHealth(),
          fetchModels().catch(() => null),
        ]);
        setHealth(healthData);
        setModelInfo(modelsData);
        setStatus('connected');
      } else {
        setStatus('error');
        setError(new Error('Backend failed to become healthy'));
      }
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err : new Error('Connection failed'));
    }
  }, []);

  const changeModel = useCallback(async (model: string) => {
    try {
      const result = await switchModel(model);
      if (result.success) {
        // Refresh model info
        const modelsData = await fetchModels().catch(() => null);
        setModelInfo(modelsData);
      }
      return result;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to switch model');
    }
  }, []);

  return { status, health, modelInfo, error, retry, changeModel };
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useCallback(
    async (content: string, options?: Partial<Omit<ChatRequest, 'message'>>) => {
      const userMessage: ChatMessage = {
        role: 'user',
        content,
        images: options?.images,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await sendChatRequest({
          message: content,
          images: options?.images,
          history: messages,
          ...options,
        });

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          thinking: response.thinking,
          timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
        return response;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Chat failed');
        setError(error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [messages]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    setMessages,
  };
}
