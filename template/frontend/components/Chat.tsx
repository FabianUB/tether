import { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useApi';
import { ChatMessage } from './ChatMessage';
import './Chat.css';

export function Chat() {
  const [input, setInput] = useState('');
  const [thinkingEnabled, setThinkingEnabled] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input;
    setInput('');

    try {
      await sendMessage(message, { think: thinkingEnabled });
    } catch {
      // Error is already handled in the hook
    }
  };

  return (
    <div className="chat">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Start a conversation</p>
            <p className="chat-hint">
              Type a message below to begin chatting with the AI
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}

        {isLoading && (
          <div className="chat-loading">
            <div className="spinner" />
            <span>Thinking...</span>
          </div>
        )}

        {error && (
          <div className="chat-error">
            <p>Error: {error.message}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <div className="chat-input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="chat-input"
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </div>
        <div className="chat-options">
          <label className="thinking-toggle">
            <input
              type="checkbox"
              checked={thinkingEnabled}
              onChange={(e) => setThinkingEnabled(e.target.checked)}
              disabled={isLoading}
            />
            <span className="toggle-label">Thinking (supported models)</span>
          </label>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearMessages}
              className="clear-button"
            >
              Clear Chat
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
