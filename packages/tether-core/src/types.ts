/**
 * Chat message structure
 */
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: number;
}

/**
 * Chat completion request
 */
export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

/**
 * Chat completion response
 */
export interface ChatResponse {
  response: string;
  tokens_used?: number;
  model?: string;
  finish_reason?: 'stop' | 'length' | 'error';
}

/**
 * Health check response from backend
 */
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  model_loaded: boolean;
  version: string;
  uptime_seconds?: number;
}

/**
 * Model information
 */
export interface ModelInfo {
  name: string;
  loaded: boolean;
  type: 'local' | 'openai' | 'custom';
  context_length?: number;
}

/**
 * API error response
 */
export interface ApiError {
  error: string;
  detail?: string;
  status_code: number;
}

/**
 * Backend connection status
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * Streaming chunk for future streaming support
 */
export interface StreamChunk {
  content: string;
  done: boolean;
  error?: string;
}
