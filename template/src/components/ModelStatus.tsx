import type { ConnectionStatus, HealthResponse } from '../hooks/useApi';
import './ModelStatus.css';

interface ModelStatusProps {
  status: ConnectionStatus;
  health: HealthResponse | null;
}

export function ModelStatus({ status, health }: ModelStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'var(--color-success)';
      case 'connecting':
        return 'var(--color-warning)';
      case 'error':
      case 'disconnected':
        return 'var(--color-error)';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return health?.model_loaded ? 'Model Ready' : 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Error';
      case 'disconnected':
        return 'Disconnected';
    }
  };

  return (
    <div className="model-status">
      <span
        className="status-indicator"
        style={{ backgroundColor: getStatusColor() }}
      />
      <span className="status-text">{getStatusText()}</span>
      {health && (
        <span className="version">v{health.version}</span>
      )}
    </div>
  );
}
