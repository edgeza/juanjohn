/**
 * Optimization Store - Zustand
 * 
 * Manages optimization jobs, parameters, and history
 */

import { create } from 'zustand';
import { apiClient } from '@/lib/api';
import { toast } from 'react-hot-toast';

export interface OptimizationParams {
  symbol: string;
  timeframe: string;
  strategy: string;
  degree?: number;
  kstd?: number;
}

export interface OptimizationJob {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  result?: any;
  error?: string;
  created_at: string;
  parameters?: OptimizationParams;
}

export interface OptimizationResult {
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  target_price?: number;
  stop_loss?: number;
  take_profit?: number;
  risk_reward_ratio?: number;
  metrics?: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
}

export interface StrategySignal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  price: number;
  target_price?: number;
  stop_loss?: number;
  take_profit?: number;
  risk_reward_ratio?: number;
  timestamp: string;
  description: string;
}

interface OptimizationState {
  // Data
  jobs: OptimizationJob[];
  signals: StrategySignal[];
  currentParams: OptimizationParams;
  
  // Loading states
  isLoading: boolean;
  isLoadingSignals: boolean;
  isStarting: boolean;
  
  // Error states
  error: string | null;
  
  // UI state
  showAdvanced: boolean;
  
  // Actions
  fetchSignals: () => Promise<void>;
  startOptimization: (params: OptimizationParams) => Promise<string | null>;
  getJobStatus: (taskId: string) => Promise<OptimizationJob | null>;
  updateParams: (params: Partial<OptimizationParams>) => void;
  setShowAdvanced: (show: boolean) => void;
  
  // Computed
  runningJobs: () => OptimizationJob[];
  completedJobs: () => OptimizationJob[];
  failedJobs: () => OptimizationJob[];
  
  // Cleanup
  clearError: () => void;
}

export const useOptimizationStore = create<OptimizationState>((set, get) => ({
  // Initial state
  jobs: [],
  signals: [],
  currentParams: {
    symbol: 'BTCUSDT',
    timeframe: '1h',
    strategy: 'polynomial_regression',
    degree: 4,
    kstd: 2.0
  },
  
  isLoading: false,
  isLoadingSignals: false,
  isStarting: false,
  
  error: null,
  showAdvanced: false,
  
  // Actions
  fetchSignals: async () => {
    set({ isLoadingSignals: true });
    
    try {
      const signals = await apiClient.getStrategySignals();
      set({ signals: signals as any, isLoadingSignals: false });
    } catch (error: any) {
      set({ isLoadingSignals: false });
      console.error('Failed to fetch signals:', error);
      // Set mock data for demo
      set({ 
        signals: [
          {
            symbol: 'BTCUSDT',
            signal: 'BUY',
            confidence: 85,
            price: 43250.50,
            target_price: 44500.00,
            stop_loss: 42000.00,
            take_profit: 46000.00,
            risk_reward_ratio: 2.5,
            timestamp: new Date().toISOString(),
            description: 'Strong bullish signal based on technical analysis'
          },
          {
            symbol: 'ETHUSDT',
            signal: 'HOLD',
            confidence: 65,
            price: 2650.25,
            target_price: 2700.00,
            stop_loss: 2600.00,
            take_profit: 2800.00,
            risk_reward_ratio: 1.8,
            timestamp: new Date().toISOString(),
            description: 'Neutral position recommended'
          },
          {
            symbol: 'SOLUSDT',
            signal: 'SELL',
            confidence: 78,
            price: 98.75,
            target_price: 95.00,
            stop_loss: 102.00,
            take_profit: 92.00,
            risk_reward_ratio: 2.0,
            timestamp: new Date().toISOString(),
            description: 'Bearish signal detected'
          }
        ]
      });
    }
  },

  startOptimization: async (params: OptimizationParams) => {
    const runningJobs = get().runningJobs();
    if (runningJobs.length > 0) {
      toast.error('An optimization is already running. Please wait for it to complete.');
      return null;
    }

    set({ isStarting: true, error: null });
    
    try {
      const request = {
        ...params,
        lookback_days: 30,
        optimization_trials: 100
      };
      const response = await apiClient.optimizeStrategy(request);
      
      set({ isStarting: false });
      
      toast.success(`Optimization completed! Signal: ${response.signal}`);
      return 'completed';
      
    } catch (error: any) {
      set({ 
        error: error.message || 'Failed to start optimization', 
        isStarting: false 
      });
      toast.error(`Failed to start optimization: ${error.message}`);
      return null;
    }
  },

  getJobStatus: async (taskId: string) => {
    try {
      // For now, return null as the API doesn't have this endpoint
      console.log(`Getting status for job ${taskId}`);
      return null;
    } catch (error: any) {
      console.error(`Failed to get status for job ${taskId}:`, error);
      return null;
    }
  },

  updateParams: (newParams: Partial<OptimizationParams>) => {
    set(state => ({
      currentParams: { ...state.currentParams, ...newParams }
    }));
  },

  setShowAdvanced: (showAdvanced: boolean) => {
    set({ showAdvanced });
  },

  // Computed
  runningJobs: () => {
    return get().jobs.filter(job => 
      job.status === 'pending' || job.status === 'running'
    );
  },

  completedJobs: () => {
    return get().jobs.filter(job => job.status === 'completed');
  },

  failedJobs: () => {
    return get().jobs.filter(job => job.status === 'failed');
  },

  // Cleanup
  clearError: () => {
    set({ error: null });
  }
}));