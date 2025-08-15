// API client for Autonama Dashboard

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface AssetSummary {
  symbol: string;
  name: string;
  category: string;
  price: number;
  change_24h: number;
  change_percent_24h: number;
  volume_24h: number;
  last_updated: string;
}

export interface OptimizationRequest {
  symbol: string;
  strategy: string;
  timeframe: string;
  lookback_days: number;
  optimization_trials: number;
}

export interface OptimizationResult {
  symbol: string;
  strategy: string;
  signal: string;
  confidence: number;
  current_price: number;
  target_price?: number;
  stop_loss?: number;
  take_profit?: number;
  risk_reward_ratio?: number;
  expected_return?: number;
  optimization_metrics: Record<string, any>;
  timestamp: string;
}

export interface StrategySignal {
  symbol: string;
  signal: string;
  confidence: number;
  price: number;
  target_price?: number;
  stop_loss?: number;
  take_profit?: number;
  timestamp: string;
  description: string;
}

export interface AlertCreate {
  symbol: string;
  condition: string;
  price: number;
  timeframe: string;
  enabled: boolean;
}

export interface AlertResponse {
  id: number;
  symbol: string;
  condition: string;
  price: number;
  timeframe: string;
  enabled: boolean;
  triggered: boolean;
  triggered_at?: string;
  created_at: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
  has_access: boolean;
  is_admin: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    // Try to get token from localStorage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    console.log('[API Client] Request to:', endpoint);
    console.log('[API Client] Token available:', this.token ? 'Yes' : 'No');
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
      console.log('[API Client] Authorization header set');
    } else {
      console.log('[API Client] No Authorization header set');
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    console.log('[API Client] Response status:', response.status);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.log('[API Client] Request failed:', errorData);
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Authentication
  async login(credentials: UserLogin): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    console.log('[API Client] Login successful, setting token:', response.access_token ? 'Present' : 'Missing');
    this.token = response.access_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', response.access_token);
      console.log('[API Client] Token stored in localStorage');
      // Set cookie for middleware with proper settings
      document.cookie = `auth_token=${response.access_token}; path=/; max-age=86400; SameSite=Lax; secure=false`;
      console.log('[API Client] Token stored in cookie');
    }
    
    return response;
  }

  async register(userData: { username: string; email: string; password: string }): Promise<UserResponse> {
    return this.request<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<UserResponse> {
    // Always check localStorage for the latest token
    if (typeof window !== 'undefined') {
      const latestToken = localStorage.getItem('auth_token');
      console.log('[API Client] getCurrentUser - localStorage token:', latestToken ? 'Present' : 'Missing');
      console.log('[API Client] getCurrentUser - instance token:', this.token ? 'Present' : 'Missing');
      if (latestToken && latestToken !== this.token) {
        console.log('[API Client] Updating instance token from localStorage');
        this.token = latestToken;
      }
    }
    return this.request<UserResponse>('/auth/me');
  }

  // Admin
  async adminListUsers(): Promise<Array<{ id: number; username: string; email: string; has_access: boolean; is_admin: boolean; created_at: string }>> {
    return this.request('/auth/admin/users');
  }

  async adminGrant(username: string): Promise<{ message: string; username: string }> {
    return this.request(`/auth/admin/users/${encodeURIComponent(username)}/grant`, { method: 'POST' });
  }

  async adminRevoke(username: string): Promise<{ message: string; username: string }> {
    return this.request(`/auth/admin/users/${encodeURIComponent(username)}/revoke`, { method: 'POST' });
  }

  // Billing
  async createCheckoutSession(username: string, successUrl?: string, cancelUrl?: string): Promise<{ id: string; url?: string }> {
    return this.request('/billing/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({ username, success_url: successUrl, cancel_url: cancelUrl }),
    });
  }

  logout(): void {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      // Remove cookie for middleware
      document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
    }
  }

  // Assets
  async getAssets(): Promise<AssetSummary[]> {
    return this.request<AssetSummary[]>('/data/assets');
  }

  async getAssetBySymbol(symbol: string): Promise<AssetSummary> {
    return this.request<AssetSummary>(`/data/assets/${encodeURIComponent(symbol)}`);
  }

  // Optimization - Fixed endpoints
  async optimizeStrategy(request: OptimizationRequest): Promise<OptimizationResult> {
    return this.request<OptimizationResult>('/optimize/optimize', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getStrategySignals(symbols?: string): Promise<StrategySignal[]> {
    const params = symbols ? `?symbols=${encodeURIComponent(symbols)}` : '';
    return this.request<StrategySignal[]>(`/optimize/signals${params}`);
  }

  async getAvailableStrategies(): Promise<{ strategies: Array<{ name: string; description: string; parameters: Record<string, string> }> }> {
    return this.request('/optimize/strategies');
  }

  async checkOptimizationHealth(): Promise<{ status: string; message: string; timestamp: string }> {
    return this.request('/optimize/health');
  }

  // Autonama Optimization - New endpoints
  async triggerAutonamaOptimization(parameters: {
    n_trials?: number;
    n_cores?: number;
    n_assets?: number;
    n_categories?: number;
    days_back?: number;
  }): Promise<{ task_id: string; status: string; message: string }> {
    return this.request('/autonama/optimize/run', {
      method: 'POST',
      body: JSON.stringify(parameters),
    });
  }

  async getOptimizationStatus(taskId: string): Promise<{ status: string; progress: number; message: string }> {
    return this.request(`/autonama/optimize/status/${taskId}`);
  }

  async getOptimizationHistory(limit?: number): Promise<any[]> {
    const params = limit ? `?limit=${limit}` : '';
    return this.request(`/autonama/optimize/history${params}`);
  }

  // Signals - New endpoints
  async getLiveSignals(): Promise<any[]> {
    return this.request('/data/signals');
  }

  async getSignalsBySymbol(symbol: string): Promise<any[]> {
    return this.request(`/data/signals?symbol=${encodeURIComponent(symbol)}`);
  }

  async triggerSignalCalculation(parameters: {
    degree?: number;
    kstd?: number;
  }): Promise<{ task_id: string; status: string; message: string }> {
    return this.request('/autonama/signals/calculate', {
      method: 'POST',
      body: JSON.stringify(parameters),
    });
  }

  // Alerts
  async createAlert(alert: AlertCreate): Promise<AlertResponse> {
    return this.request<AlertResponse>('/auth/alerts', {
      method: 'POST',
      body: JSON.stringify(alert),
    });
  }

  async getAlerts(): Promise<AlertResponse[]> {
    return this.request<AlertResponse[]>('/auth/alerts');
  }

  async updateAlert(alertId: number, updates: Partial<AlertCreate>): Promise<AlertResponse> {
    return this.request<AlertResponse>(`/auth/alerts/${alertId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteAlert(alertId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/auth/alerts/${alertId}`, {
      method: 'DELETE',
    });
  }

  async checkAlerts(): Promise<{ triggered_alerts: any[]; total_alerts: number }> {
    return this.request('/auth/alerts/check');
  }

  // WebSocket connection for real-time data
  getWebSocketUrl(): string {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    return `${wsUrl}/ws`;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// Utility functions
export const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(price);
};

export const formatPercentage = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

export const formatVolume = (volume: number): string => {
  if (volume >= 1e9) {
    return `${(volume / 1e9).toFixed(2)}B`;
  } else if (volume >= 1e6) {
    return `${(volume / 1e6).toFixed(2)}M`;
  } else if (volume >= 1e3) {
    return `${(volume / 1e3).toFixed(2)}K`;
  }
  return volume.toFixed(2);
};

export const getSignalColor = (signal: string): string => {
  switch (signal.toUpperCase()) {
    case 'BUY':
      return 'text-green-500';
    case 'SELL':
      return 'text-red-500';
    case 'HOLD':
      return 'text-yellow-500';
    default:
      return 'text-gray-500';
  }
};

export const getSignalBgColor = (signal: string): string => {
  switch (signal.toUpperCase()) {
    case 'BUY':
      return 'bg-green-500/10 border-green-500/20';
    case 'SELL':
      return 'bg-red-500/10 border-red-500/20';
    case 'HOLD':
      return 'bg-yellow-500/10 border-yellow-500/20';
    default:
      return 'bg-gray-500/10 border-gray-500/20';
  }
};
