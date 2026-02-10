import { useBackendStatus } from "./hooks/useApi";
import { Chat } from "./components/Chat";
import { ModelStatus } from "./components/ModelStatus";
import { ApiKeyForm } from "./components/ApiKeyForm";
import "./App.css";

function App() {
  const { status, health, modelInfo, error, retry, changeModel, submitApiKey } =
    useBackendStatus();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Tether App</h1>
        <ModelStatus
          status={status}
          health={health}
          modelInfo={modelInfo}
          onModelChange={changeModel}
        />
      </header>

      <main className="app-main">
        {status === "connecting" && (
          <div className="loading">
            <div className="spinner" />
            <p>Connecting to backend...</p>
          </div>
        )}

        {status === "loading-model" && (
          <div className="loading">
            <div className="spinner" />
            <p>Loading model...</p>
            <p className="loading-hint">
              This may take a moment for large models
            </p>
          </div>
        )}

        {status === "disconnected" && (
          <div className="error disconnected">
            <p>Connection lost</p>
            <p className="error-detail">The backend is no longer responding</p>
            <button onClick={retry}>Reconnect</button>
          </div>
        )}

        {status === "needs-api-key" && (
          <ApiKeyForm modelInfo={modelInfo} onSubmit={submitApiKey} />
        )}

        {status === "error" && (
          <div className="error">
            <p>Failed to connect</p>
            {error && <p className="error-detail">{error.message}</p>}
            <button onClick={retry}>Retry</button>
          </div>
        )}

        {status === "connected" && <Chat />}
      </main>
    </div>
  );
}

export default App;
