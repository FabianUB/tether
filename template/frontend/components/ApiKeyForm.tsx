import { useState } from "react";
import type { ModelsResponse } from "../hooks/useApi";
import "./ApiKeyForm.css";

interface BackendInfo {
  name: string;
  placeholder: string;
  helpUrl: string;
  helpText: string;
}

const BACKEND_INFO: Record<string, BackendInfo> = {
  openai: {
    name: "OpenAI",
    placeholder: "sk-...",
    helpUrl: "https://platform.openai.com/api-keys",
    helpText: "Get an API key",
  },
  gemini: {
    name: "Google Gemini",
    placeholder: "AI...",
    helpUrl: "https://aistudio.google.com/apikey",
    helpText: "Get an API key",
  },
};

interface ApiKeyFormProps {
  modelInfo: ModelsResponse | null;
  onSubmit: (apiKey: string) => Promise<void>;
}

export function ApiKeyForm({ modelInfo, onSubmit }: ApiKeyFormProps) {
  const [apiKey, setApiKey] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const backend = modelInfo?.backend || "openai";
  const info = BACKEND_INFO[backend] || BACKEND_INFO.openai;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await onSubmit(apiKey.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set API key");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="api-key-form-container">
      <form className="api-key-form" onSubmit={handleSubmit}>
        <h2>API Key Required</h2>
        <p className="api-key-description">
          Enter your {info.name} API key to get started.
        </p>
        <a
          className="api-key-help-link"
          href={info.helpUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          {info.helpText}
        </a>
        <input
          type="password"
          className="api-key-input"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder={info.placeholder}
          autoFocus
          disabled={isSubmitting}
        />
        {error && <p className="api-key-error">{error}</p>}
        <button
          type="submit"
          className="api-key-submit"
          disabled={!apiKey.trim() || isSubmitting}
        >
          {isSubmitting ? "Connecting..." : "Connect"}
        </button>
        <p className="api-key-hint">
          Stored in memory only — not saved to disk.
        </p>
      </form>
    </div>
  );
}
