/**
 * Tether configuration options
 */
export interface TetherConfig {
  /**
   * Base URL for the Python backend API
   * @default 'http://localhost:8000'
   */
  apiUrl: string;

  /**
   * Health check endpoint path
   * @default '/health'
   */
  healthEndpoint: string;

  /**
   * Maximum number of retry attempts for health checks
   * @default 30
   */
  maxRetries: number;

  /**
   * Delay between retry attempts in milliseconds
   * @default 1000
   */
  retryDelay: number;

  /**
   * Request timeout in milliseconds
   * @default 30000
   */
  timeout: number;
}

const defaultConfig: TetherConfig = {
  apiUrl: 'http://localhost:8000',
  healthEndpoint: '/health',
  maxRetries: 30,
  retryDelay: 1000,
  timeout: 30000,
};

let currentConfig: TetherConfig = { ...defaultConfig };

/**
 * Configure Tether settings
 */
export function configureTether(config: Partial<TetherConfig>): void {
  currentConfig = { ...currentConfig, ...config };
}

/**
 * Get current Tether configuration
 */
export function getConfig(): TetherConfig {
  return { ...currentConfig };
}

/**
 * Reset configuration to defaults
 */
export function resetConfig(): void {
  currentConfig = { ...defaultConfig };
}

/**
 * Get the full API URL for a given path
 */
export function getApiUrl(path: string): string {
  const base = currentConfig.apiUrl.replace(/\/$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
}
