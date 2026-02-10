import { useState } from "react";
import Markdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "../hooks/useApi";
import "./ChatMessage.css";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [showThinking, setShowThinking] = useState(false);

  return (
    <div className={`message ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-header">
        <span className="message-role">{isUser ? "You" : "Assistant"}</span>
        {message.timestamp && (
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>
      {message.images && message.images.length > 0 && (
        <div className="message-images">
          {message.images.map((img, index) => (
            <img
              key={index}
              src={`data:image/jpeg;base64,${img}`}
              alt={`Attached ${index + 1}`}
              className="message-image"
            />
          ))}
        </div>
      )}
      {message.thinking && (
        <div className="message-thinking">
          <button
            className="thinking-toggle"
            onClick={() => setShowThinking(!showThinking)}
            aria-expanded={showThinking}
          >
            <span
              className={`thinking-chevron ${showThinking ? "expanded" : ""}`}
            >
              {showThinking ? "\u25BC" : "\u25B6"}
            </span>
            Thinking
          </button>
          {showThinking && (
            <div className="thinking-content">
              <Markdown>{message.thinking}</Markdown>
            </div>
          )}
        </div>
      )}
      <div className="message-content">
        {isUser ? message.content : <Markdown>{message.content}</Markdown>}
      </div>
      {!isUser && (message.input_tokens || message.output_tokens) && (
        <div className="message-usage">
          {message.input_tokens != null && (
            <span>{message.input_tokens} in</span>
          )}
          {message.output_tokens != null && (
            <span>{message.output_tokens} out</span>
          )}
          {message.cost != null && (
            <span>
              ${message.cost < 0.01 ? message.cost.toFixed(4) : message.cost.toFixed(2)}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
