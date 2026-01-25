# Chat App Example

A simple chat application built with Tether demonstrating local LLM integration.

## Overview

This example shows how to build a chat interface that connects to a local LLM using llama-cpp-python. The app features:

- Real-time chat interface
- Backend connection status indicator
- Conversation history
- Configurable model parameters

## Quick Start

### Option 1: Use create-tether-app

```bash
npx create-tether-app chat-app --template local-llm
cd chat-app
pnpm install
```

### Option 2: Clone and modify the template

Copy the `template/` directory from this repo and customize it.

## Setup

### 1. Download a Model

Download a GGUF model from Hugging Face. Recommended starter models:

- [TinyLlama-1.1B-Chat](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) - Small, fast
- [Mistral-7B-Instruct](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) - Good quality
- [Llama-2-7B-Chat](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF) - Balanced

```bash
# Example: Download TinyLlama
mkdir -p models
cd models
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 2. Configure Environment

Create `.env` file:

```env
TETHER_LLM_BACKEND=local
TETHER_MODEL_PATH=./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
TETHER_CONTEXT_LENGTH=2048
```

### 3. Install Dependencies

```bash
# Node.js dependencies
pnpm install

# Python dependencies
cd src-python && uv sync
```

### 4. Run Development Server

```bash
# Terminal 1: Frontend
pnpm dev

# Terminal 2: Backend
pnpm python:dev
```

Open `http://localhost:1420` in your browser.

## Features Demonstrated

### Backend Status Hook

```tsx
const { status, health, error, retry } = useBackendStatus();
```

Shows connection state and model loading status.

### Chat Hook

```tsx
const { messages, isLoading, sendMessage, clearMessages } = useChat();
```

Manages conversation state and API calls.

### LLM Service Abstraction

```python
service = get_llm_service()
await service.initialize()
response = await service.complete(prompt)
```

Provides unified interface for different LLM backends.

## Customization Ideas

### Add System Prompt

Modify `src-python/app/routes/chat.py`:

```python
SYSTEM_PROMPT = "You are a helpful assistant."

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {body.message}\nAssistant:"
    response = await llm.complete(prompt)
    return ChatResponse(response=response)
```

### Add Conversation Memory

The chat already sends history. To improve context:

```python
def format_history(messages: list[ChatMessage]) -> str:
    return "\n".join(
        f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
        for m in messages[-10:]  # Last 10 messages
    )
```

### Add Typing Indicator

In the frontend:

```tsx
{isLoading && (
  <div className="typing-indicator">
    <span></span>
    <span></span>
    <span></span>
  </div>
)}
```

### Add Model Selection

Allow users to choose models:

```tsx
const [model, setModel] = useState('default');

await sendMessage(text, { model });
```

## Building for Production

```bash
# Build Python backend
pnpm python:build

# Build complete app
pnpm tauri:build
```

## Troubleshooting

### Model not loading

1. Check model path in `.env`
2. Verify file exists and is readable
3. Check Python terminal for errors

### Slow responses

1. Use a smaller/quantized model
2. Reduce `max_tokens`
3. Enable GPU acceleration

### Out of memory

1. Use Q4_K_M or smaller quantization
2. Reduce `TETHER_CONTEXT_LENGTH`
3. Use a smaller model

## Next Steps

- Add streaming responses (future Tether feature)
- Implement RAG with local embeddings
- Add voice input/output
- Create a custom UI theme
