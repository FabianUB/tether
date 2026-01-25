import { useState, useEffect, useCallback, useRef } from 'react';
import { checkHealth, waitForBackend, chat, getModelInfo } from './api-client.js';
import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  ConnectionStatus,
  ChatMessage,
  ModelInfo,
} from './types.js';

/**
 * Hook for managing backend connection status
 */
export function useBackendStatus() {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    const connect = async () => {
      setStatus('connecting');
      setError(null);

      try {
        const ready = await waitForBackend();
        if (!mounted) return;

        if (ready) {
          const healthData = await checkHealth();
          if (!mounted) return;
          setHealth(healthData);
          setStatus('connected');
        } else {
          setStatus('error');
          setError(new Error('Backend failed to become healthy'));
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
    };
  }, []);

  const retry = useCallback(async () => {
    setStatus('connecting');
    setError(null);

    try {
      const ready = await waitForBackend();
      if (ready) {
        const healthData = await checkHealth();
        setHealth(healthData);
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

  return { status, health, error, retry };
}

/**
 * Hook for chat functionality
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useCallback(
    async (content: string, options?: Partial<Omit<ChatRequest, 'message'>>) => {
      const userMessage: ChatMessage = {
        role: 'user',
        content,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await chat({
          message: content,
          history: messages,
          ...options,
        });

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
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

/**
 * Hook for model information
 */
export function useModel() {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchModel = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const info = await getModelInfo();
      setModel(info);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to get model info'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModel();
  }, [fetchModel]);

  return { model, isLoading, error, refetch: fetchModel };
}

/**
 * Hook for API calls with loading state
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: React.DependencyList = []
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const fetcherRef = useRef(fetcher);

  useEffect(() => {
    fetcherRef.current = fetcher;
  }, [fetcher]);

  const execute = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetcherRef.current();
      setData(result);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('API call failed');
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    execute();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, isLoading, error, refetch: execute };
}
