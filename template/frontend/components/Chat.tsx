import { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useApi';
import { ChatMessage } from './ChatMessage';
import './Chat.css';

export function Chat() {
  const [input, setInput] = useState('');
  const [thinkingEnabled, setThinkingEnabled] = useState(true);
  const [pendingImages, setPendingImages] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newImages: string[] = [];
    for (const file of Array.from(files)) {
      if (file.type.startsWith('image/')) {
        const base64 = await fileToBase64(file);
        newImages.push(base64);
      }
    }
    setPendingImages((prev) => [...prev, ...newImages]);

    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // Remove data URL prefix (e.g., "data:image/png;base64,")
        const result = reader.result as string;
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index: number) => {
    setPendingImages((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && pendingImages.length === 0) || isLoading) return;

    const message = input;
    const images = pendingImages.length > 0 ? pendingImages : undefined;
    setInput('');
    setPendingImages([]);

    try {
      await sendMessage(message, { think: thinkingEnabled, images });
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
        {pendingImages.length > 0 && (
          <>
            {thinkingEnabled && (
              <div className="image-warning">
                Thinking mode is not supported with images and will be disabled for this message.
              </div>
            )}
            <div className="pending-images">
              {pendingImages.map((img, index) => (
                <div key={index} className="pending-image">
                  <img src={`data:image/jpeg;base64,${img}`} alt={`Pending ${index + 1}`} />
                  <button
                    type="button"
                    className="remove-image"
                    onClick={() => removeImage(index)}
                    aria-label="Remove image"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
        <div className="chat-input-wrapper">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageSelect}
            accept="image/*"
            multiple
            hidden
          />
          <button
            type="button"
            className="image-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            title="Add image (vision models)"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="chat-input"
          />
          <button type="submit" disabled={isLoading || (!input.trim() && pendingImages.length === 0)}>
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
