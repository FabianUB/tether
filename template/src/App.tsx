import { useBackendStatus } from './hooks/useApi';
import { Chat } from './components/Chat';
import { ModelStatus } from './components/ModelStatus';
import './App.css';

function App() {
  const { status, health, error, retry } = useBackendStatus();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Tether App</h1>
        <ModelStatus status={status} health={health} />
      </header>

      <main className="app-main">
        {status === 'connecting' && (
          <div className="loading">
            <div className="spinner" />
            <p>Connecting to backend...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="error">
            <p>Failed to connect to backend</p>
            {error && <p className="error-detail">{error.message}</p>}
            <button onClick={retry}>Retry</button>
          </div>
        )}

        {status === 'connected' && <Chat />}
      </main>
    </div>
  );
}

export default App;
