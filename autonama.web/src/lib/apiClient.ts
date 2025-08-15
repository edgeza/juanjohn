/**
 * Centralized API Client for Autonama Dashboard
 * 
 * This client provides a unified interface for all API calls with:
 * - Automatic error handling
 * - Request/response interceptors
 * - Type safety
 * - Retry logic
 * - Loading states
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// Types
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export interface RequestConfig extends AxiosRequestConfig {
  showErrorToast?: boolean;
  showSuccessToast?: boolean;
  retries?: number;
}

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ Response Error:', error);
        
        // Handle common error scenarios
        if (error.response?.status === 401) {
          this.handleUnauthorized();
        }
        
        return Promise.reject(this.formatError(error));
      }
    );
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  private handleUnauthorized() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      // Redirect to login or show auth modal
      toast.error('Session expired. Please log in again.');
    }
  }

  private formatError(error: any): ApiError {
    if (error.response) {
      return {
        message: error.response.data?.message || error.response.data?.detail || 'An error occurred',
        status: error.response.status,
        code: error.response.data?.code,
      };
    } else if (error.request) {
      return {
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
      };
    } else {
      return {
        message: error.message || 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
      };
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    retries: number = 2,
    delay: number = 1000
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      if (retries > 0) {
        console.log(`🔄 Retrying request... (${retries} attempts left)`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.retryRequest(requestFn, retries - 1, delay * 2);
      }
      throw error;
    }
  }

  // Generic request method
  async request<T = any>(config: RequestConfig): Promise<T> {
    const {
      showErrorToast = true,
      showSuccessToast = false,
      retries = 0,
      ...axiosConfig
    } = config;

    try {
      const requestFn = () => this.client.request<T>(axiosConfig);
      const response = retries > 0 
        ? await this.retryRequest(requestFn, retries)
        : await requestFn();

      if (showSuccessToast && response.data) {
        toast.success('Request completed successfully');
      }

      return response.data;
    } catch (error: any) {
      if (showErrorToast) {
        toast.error(error.message || 'Request failed');
      }
      throw error;
    }
  }

  // HTTP Methods
  async get<T = any>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  async post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  async put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  async patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  }

  async delete<T = any>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }

  // WebSocket URL helper
  getWebSocketUrl(path: string): string {
    return this.baseURL.replace(/^http/, 'ws') + path;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.get('/health', { showErrorToast: false });
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export for use in stores and components
export default apiClient;