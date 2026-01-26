import type { ConnectionStatus, HealthResponse, ModelsResponse } from '../hooks/useApi';
import './ModelStatus.css';

interface ModelStatusProps {
  status: ConnectionStatus;
  health: HealthResponse | null;
  modelInfo: ModelsResponse | null;
}

export function ModelStatus({ status, health, modelInfo }: ModelStatusProps) {
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
        return health?.model_loaded ? 'Ready' : 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Error';
      case 'disconnected':
        return 'Disconnected';
    }
  };

  const formatBackend = (backend: string) => {
    return backend.charAt(0).toUpperCase() + backend.slice(1);
  };

  return (
    <div className="model-status">
      <span
        className="status-indicator"
        style={{ backgroundColor: getStatusColor() }}
      />
      <span className="status-text">{getStatusText()}</span>
      {modelInfo?.current_model && (
        <span className="model-name" title={`Backend: ${modelInfo.backend}`}>
          {modelInfo.current_model}
        </span>
      )}
      {modelInfo?.backend && (
        <span className="backend-type">
          {formatBackend(modelInfo.backend)}
        </span>
      )}
    </div>
  );
}
