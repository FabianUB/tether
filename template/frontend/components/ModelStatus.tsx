import { useState } from 'react';
import type { ConnectionStatus, HealthResponse, ModelsResponse, SwitchModelResponse } from '../hooks/useApi';
import './ModelStatus.css';

interface ModelStatusProps {
  status: ConnectionStatus;
  health: HealthResponse | null;
  modelInfo: ModelsResponse | null;
  onModelChange?: (model: string) => Promise<SwitchModelResponse>;
}

export function ModelStatus({ status, health, modelInfo, onModelChange }: ModelStatusProps) {
  const [isSwitching, setIsSwitching] = useState(false);

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
    if (isSwitching) return 'Switching...';
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

  const handleModelChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newModel = event.target.value;
    if (!onModelChange || newModel === modelInfo?.current_model) return;

    setIsSwitching(true);
    try {
      await onModelChange(newModel);
    } catch (error) {
      console.error('Failed to switch model:', error);
    } finally {
      setIsSwitching(false);
    }
  };

  const hasMultipleModels = modelInfo?.models && modelInfo.models.length > 1;

  return (
    <div className="model-status">
      <span
        className="status-indicator"
        style={{ backgroundColor: getStatusColor() }}
      />
      <span className="status-text">{getStatusText()}</span>
      {modelInfo && hasMultipleModels && onModelChange ? (
        <select
          className="model-select"
          value={modelInfo.current_model || ''}
          onChange={handleModelChange}
          disabled={isSwitching || status !== 'connected'}
        >
          {modelInfo.models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      ) : modelInfo?.current_model ? (
        <span className="model-name" title={`Backend: ${modelInfo.backend}`}>
          {modelInfo.current_model}
        </span>
      ) : null}
      {modelInfo?.backend && (
        <span className="backend-type">
          {formatBackend(modelInfo.backend)}
        </span>
      )}
    </div>
  );
}
