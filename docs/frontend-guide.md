# Frontend Guide

This guide covers building the React frontend for your Tether application. No Rust or Python knowledge is required.

## Overview

The frontend is a standard React application using:

- **React 18** - UI library
- **Vite** - Build tool with fast HMR
- **TypeScript** - Type safety

The frontend communicates with the Python backend via HTTP requests to `localhost:8000`.

## Project Structure

```
src/
├── components/           # React components
│   ├── Chat.tsx          # Chat interface
│   ├── Chat.css
│   ├── ChatMessage.tsx   # Individual message
│   ├── ChatMessage.css
│   ├── ModelStatus.tsx   # Backend status indicator
│   └── ModelStatus.css
├── hooks/
│   └── useApi.ts         # API communication hooks
├── App.tsx               # Main application
├── App.css
├── main.tsx              # Entry point
└── index.css             # Global styles
```

## Core Concepts

### Backend Connection

The `useBackendStatus` hook handles connecting to the Python backend:

```tsx
import { useBackendStatus } from "./hooks/useApi";

function App() {
  const { status, health, error, retry } = useBackendStatus();

  if (status === "connecting") {
    return <div>Connecting to backend...</div>;
  }

  if (status === "error") {
    return (
      <div>
        <p>Connection failed: {error?.message}</p>
        <button onClick={retry}>Retry</button>
      </div>
    );
  }

  return (
    <div>Connected! Model: {health?.model_loaded ? "Ready" : "Not loaded"}</div>
  );
}
```

### Chat Interface

The `useChat` hook provides chat functionality:

```tsx
import { useChat } from "./hooks/useApi";

function ChatComponent() {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();

  const handleSend = async (text: string) => {
    try {
      await sendMessage(text);
    } catch (err) {
      console.error("Failed to send:", err);
    }
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i} className={msg.role}>
          {msg.content}
        </div>
      ))}
      {isLoading && <div>Thinking...</div>}
      {/* Input form here */}
    </div>
  );
}
```

## API Types

The `useApi.ts` file exports TypeScript types for API communication:

```typescript
interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
}

interface ChatRequest {
  message: string;
  history?: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

interface ChatResponse {
  response: string;
  tokens_used?: number;
  model?: string;
  finish_reason?: "stop" | "length" | "error";
}

interface HealthResponse {
  status: "healthy" | "unhealthy";
  model_loaded: boolean;
  version: string;
}
```

## Making Custom API Calls

You can make direct API calls using the fetch helper:

```typescript
// In your component or hook
const API_URL = "http://localhost:8000";

async function customApiCall<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

// Usage
const data = await customApiCall<MyType>("/my-endpoint", {
  method: "POST",
  body: JSON.stringify({ key: "value" }),
});
```

## Styling

The template uses CSS variables for theming:

```css
:root {
  --color-bg: #0f0f0f;
  --color-surface: #1a1a1a;
  --color-border: #333;
  --color-text: #f0f0f0;
  --color-primary: #646cff;
  --color-success: #4ade80;
  --color-error: #f87171;
  --radius: 8px;
}
```

You can customize these in `src/index.css`.

## Adding New Components

1. Create the component file:

```tsx
// src/components/MyComponent.tsx
interface MyComponentProps {
  title: string;
}

export function MyComponent({ title }: MyComponentProps) {
  return <div className="my-component">{title}</div>;
}
```

2. Create the CSS file:

```css
/* src/components/MyComponent.css */
.my-component {
  padding: 1rem;
  background: var(--color-surface);
  border-radius: var(--radius);
}
```

3. Import in your component:

```tsx
import { MyComponent } from "./components/MyComponent";
import "./components/MyComponent.css";
```

## Tauri Integration (Optional)

While most communication happens via HTTP, you can also use Tauri's IPC:

```typescript
import { invoke } from "@tauri-apps/api/core";

// Get the API port (useful if using dynamic ports)
const port = await invoke<number>("get_api_port");

// Restart the backend
await invoke("restart_backend");
```

## Best Practices

1. **Keep components small** - Break down complex UIs into smaller components
2. **Use TypeScript** - Define interfaces for all data structures
3. **Handle loading states** - Always show feedback during async operations
4. **Handle errors gracefully** - Display user-friendly error messages
5. **Use CSS variables** - Keep styling consistent with the theme

## Common Issues

### Backend not connecting

- Make sure the Python backend is running (`pnpm python:dev`)
- Check that port 8000 is not in use
- Look for errors in the Python terminal

### Slow development rebuild

- Ensure `src-tauri/` and `src-python/` are in the Vite ignore list
- Use separate terminals for frontend and backend development

### TypeScript errors

- Run `pnpm typecheck` to see all errors
- Check that API types match the backend response
