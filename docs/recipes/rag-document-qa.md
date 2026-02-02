# RAG: Document Q&A

Build a "chat with your documents" feature using Retrieval-Augmented Generation (RAG).

## Overview

RAG allows users to:

1. Upload PDF/text documents
2. Ask questions about the content
3. Get answers with source citations

**How it works:**

```
Document → Chunk → Embed → Store in Vector DB
                              ↓
Question → Embed → Search → Relevant chunks → LLM → Answer
```

## Dependencies

### Backend (Python)

Add to `backend/pyproject.toml`:

```toml
dependencies = [
    # ... existing deps
    "langchain>=0.1.0",
    "langchain-community>=0.0.10",
    "chromadb>=0.4.0",
    "pypdf>=4.0.0",
    "sentence-transformers>=2.2.0",
]
```

Install:

```bash
cd backend && uv sync
```

### Frontend

```bash
pnpm add react-dropzone
```

## Backend Implementation

### 1. Vector Store Service

Create `backend/app/services/vectorstore.py`:

```python
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


class VectorStoreService:
    def __init__(self, persist_dir: str = "./data/vectorstore"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Use local embeddings (no API key needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        self.vectorstore: Optional[Chroma] = None
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load existing vectorstore or create new one."""
        self.vectorstore = Chroma(
            persist_directory=str(self.persist_dir),
            embedding_function=self.embeddings,
        )

    def add_document(self, file_path: str) -> int:
        """Add a document to the vector store. Returns number of chunks added."""
        path = Path(file_path)

        # Load based on file type
        if path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(path))
        else:
            loader = TextLoader(str(path))

        documents = loader.load()

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Add to vectorstore
        self.vectorstore.add_documents(chunks)

        return len(chunks)

    def search(self, query: str, k: int = 4) -> list[dict]:
        """Search for relevant chunks."""
        results = self.vectorstore.similarity_search_with_score(query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    def clear(self) -> None:
        """Clear all documents from the store."""
        self.vectorstore.delete_collection()
        self._load_or_create()
```

### 2. RAG Routes

Create `backend/app/routes/rag.py`:

```python
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.llm import get_llm_service
from app.services.vectorstore import VectorStoreService

router = APIRouter(prefix="/rag", tags=["rag"])

# Initialize vector store
vectorstore = VectorStoreService()


class QueryRequest(BaseModel):
    question: str
    num_results: int = 4


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    """Upload and index a document."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".pdf", ".txt", ".md"]:
        raise HTTPException(400, "Only PDF, TXT, and MD files are supported")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        num_chunks = vectorstore.add_document(tmp_path)
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_indexed": num_chunks,
        }
    finally:
        Path(tmp_path).unlink()  # Clean up temp file


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Ask a question about uploaded documents."""
    # Search for relevant chunks
    results = vectorstore.search(request.question, k=request.num_results)

    if not results:
        return QueryResponse(
            answer="No relevant documents found. Please upload some documents first.",
            sources=[],
        )

    # Build context from results
    context = "\n\n".join(
        f"[Source {i+1}]: {r['content']}" for i, r in enumerate(results)
    )

    # Generate answer using LLM
    llm = get_llm_service()
    prompt = f"""Answer the question based on the following context.
If the context doesn't contain enough information, say so.
Cite your sources using [Source N] notation.

Context:
{context}

Question: {request.question}

Answer:"""

    answer = await llm.complete(prompt)

    return QueryResponse(answer=answer, sources=results)


@router.delete("/clear")
async def clear_documents() -> dict:
    """Clear all indexed documents."""
    vectorstore.clear()
    return {"status": "success", "message": "All documents cleared"}
```

### 3. Register Routes

In `backend/app/main.py`, add:

```python
from app.routes.rag import router as rag_router

app.include_router(rag_router)
```

## Frontend Implementation

### 1. Document Upload Component

Create `frontend/components/DocumentUpload.tsx`:

```tsx
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface DocumentUploadProps {
  apiUrl: string;
  onUploadComplete?: (result: { filename: string; chunks: number }) => void;
}

export function DocumentUpload({
  apiUrl,
  onUploadComplete,
}: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setUploading(true);
      setError(null);

      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append("file", file);

        try {
          const response = await fetch(`${apiUrl}/rag/upload`, {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Upload failed");
          }

          const result = await response.json();
          onUploadComplete?.({
            filename: result.filename,
            chunks: result.chunks_indexed,
          });
        } catch (err) {
          setError(err instanceof Error ? err.message : "Upload failed");
        }
      }

      setUploading(false);
    },
    [apiUrl, onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "text/markdown": [".md"],
    },
  });

  return (
    <div
      {...getRootProps()}
      style={{
        border: "2px dashed var(--color-border)",
        borderRadius: "8px",
        padding: "2rem",
        textAlign: "center",
        cursor: "pointer",
        backgroundColor: isDragActive
          ? "var(--color-surface-hover)"
          : "transparent",
      }}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <p>Uploading...</p>
      ) : isDragActive ? (
        <p>Drop files here...</p>
      ) : (
        <p>Drag & drop PDF, TXT, or MD files here, or click to select</p>
      )}
      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}
    </div>
  );
}
```

### 2. RAG Chat Component

Create `frontend/components/RAGChat.tsx`:

```tsx
import { useState } from "react";

interface Source {
  content: string;
  metadata: Record<string, unknown>;
  score: number;
}

interface RAGChatProps {
  apiUrl: string;
}

export function RAGChat({ apiUrl }: RAGChatProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setAnswer(null);
    setSources([]);

    try {
      const response = await fetch(`${apiUrl}/rag/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();
      setAnswer(data.answer);
      setSources(data.sources);
    } catch (err) {
      setAnswer("Error: Failed to get answer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents..."
          style={{
            width: "100%",
            padding: "0.75rem",
            borderRadius: "8px",
            border: "1px solid var(--color-border)",
            backgroundColor: "var(--color-surface)",
          }}
        />
      </form>

      {loading && <p>Thinking...</p>}

      {answer && (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "var(--color-surface)",
            borderRadius: "8px",
            marginBottom: "1rem",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Answer</h3>
          <p>{answer}</p>
        </div>
      )}

      {sources.length > 0 && (
        <div>
          <h3>Sources</h3>
          {sources.map((source, i) => (
            <details
              key={i}
              style={{
                padding: "0.5rem",
                backgroundColor: "var(--color-surface)",
                borderRadius: "4px",
                marginBottom: "0.5rem",
              }}
            >
              <summary>
                Source {i + 1} (relevance: {(1 - source.score).toFixed(2)})
              </summary>
              <p style={{ fontSize: "0.9em", whiteSpace: "pre-wrap" }}>
                {source.content}
              </p>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 3. Usage in App

```tsx
import { DocumentUpload } from "./components/DocumentUpload";
import { RAGChat } from "./components/RAGChat";

function App() {
  const apiUrl = "http://localhost:8000";
  const [documents, setDocuments] = useState<string[]>([]);

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}>
      <h1>Document Q&A</h1>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Upload Documents</h2>
        <DocumentUpload
          apiUrl={apiUrl}
          onUploadComplete={(result) => {
            setDocuments((prev) => [...prev, result.filename]);
          }}
        />
        {documents.length > 0 && (
          <p style={{ marginTop: "1rem" }}>
            Indexed: {documents.join(", ")}
          </p>
        )}
      </section>

      <section>
        <h2>Ask Questions</h2>
        <RAGChat apiUrl={apiUrl} />
      </section>
    </div>
  );
}
```

## Configuration Tips

### Chunk Size

Adjust chunk size based on your use case:

```python
# Smaller chunks = more precise retrieval, less context
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

# Larger chunks = more context, might miss specific details
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
```

### Embedding Models

The recipe uses `all-MiniLM-L6-v2` (fast, small). Alternatives:

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| `all-MiniLM-L6-v2` | 80MB | Good | Fast |
| `all-mpnet-base-v2` | 420MB | Better | Medium |
| `instructor-large` | 1.3GB | Best | Slow |

### Persistence

ChromaDB persists automatically to `./data/vectorstore`. To use a different location:

```python
vectorstore = VectorStoreService(persist_dir="./my-custom-path")
```

## Next Steps

- Add support for more file types (DOCX, HTML)
- Implement document deletion
- Add metadata filtering
- Stream the LLM response
- Show chunk highlighting in source documents
