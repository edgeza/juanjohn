'use client';

import { useState, useEffect } from 'react';
import { Play, StopCircle, RefreshCw, TrendingUp, TrendingDown, Activity, Target, Zap, Settings, BarChart3 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface OptimizationStatus {
  task_id: string;
  status: string;
  progress: number;
  message: string;
}

interface OptimizationHistory {
  id: string;
  symbol: string;
  strategy: string;
  status: string;
  created_at: string;
  completed_at?: string;
  parameters: any;
  results?: any;
}

export default function OptimizationPage() {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationStatus, setOptimizationStatus] = useState<OptimizationStatus | null>(null);
  const [optimizationHistory, setOptimizationHistory] = useState<OptimizationHistory[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Optimization parameters
  const [parameters, setParameters] = useState({
    n_trials: 10,
    n_cores: 4,
    n_assets: 20, // Optimize for more assets
    n_categories: 4,
    days_back: 365
  });

  useEffect(() => {
    fetchOptimizationHistory();
    fetchStrategies();
  }, []);

  // Poll optimization status if running
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isOptimizing && optimizationStatus?.task_id) {
      interval = setInterval(async () => {
        try {
          const status = await apiClient.getOptimizationStatus(optimizationStatus.task_id);
          setOptimizationStatus({
            ...status,
            task_id: optimizationStatus.task_id
          });
          
          if (status.status === 'completed' || status.status === 'failed') {
            setIsOptimizing(false);
            toast.success('Optimization completed!');
            fetchOptimizationHistory(); // Refresh history
          }
        } catch (error) {
          console.error('Error polling optimization status:', error);
        }
      }, 5000); // Poll every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isOptimizing, optimizationStatus?.task_id]);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getAvailableStrategies();
      setStrategies(response.strategies || []);
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setError('Failed to fetch strategies');
    } finally {
      setLoading(false);
    }
  };

  const fetchOptimizationHistory = async () => {
    try {
      const history = await apiClient.getOptimizationHistory(20);
      setOptimizationHistory(history);
    } catch (error) {
      console.error('Error fetching optimization history:', error);
    }
  };

  const startOptimization = async () => {
    try {
      setIsOptimizing(true);
      setError(null);
      
      toast.loading('Starting optimization for all assets...', { id: 'optimization' });
      
      const response = await apiClient.triggerAutonamaOptimization(parameters);
      
      setOptimizationStatus({
        task_id: response.task_id,
        status: 'started',
        progress: 0,
        message: response.message
      });
      
      toast.success('Optimization started successfully!', { id: 'optimization' });
      
    } catch (error: any) {
      console.error('Error starting optimization:', error);
      setError(error.message || 'Failed to start optimization');
      setIsOptimizing(false);
      toast.error('Failed to start optimization', { id: 'optimization' });
    }
  };

  const stopOptimization = async () => {
    try {
      setIsOptimizing(false);
      setOptimizationStatus(null);
      toast.success('Optimization stopped');
    } catch (error) {
      console.error('Error stopping optimization:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'text-green-500';
      case 'running':
      case 'started':
        return 'text-blue-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <TrendingUp className="h-4 w-4" />;
      case 'running':
      case 'started':
        return <Activity className="h-4 w-4 animate-pulse" />;
      case 'failed':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen p-6 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Strategy Optimization
          </h1>
          <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
            Optimize Autonama Channels strategy parameters for all assets
          </p>
        </div>

        {/* Optimization Controls */}
        <div className="card mb-8 glass">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Optimization Parameters
              </h2>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Configure optimization settings for all assets
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isOptimizing ? (
                <button
                  onClick={stopOptimization}
                  className="btn-secondary flex items-center gap-2"
                  disabled={!isOptimizing}
                >
                  <StopCircle className="h-4 w-4" />
                  Stop Optimization
                </button>
              ) : (
                <button
                  onClick={startOptimization}
                  className="btn-primary flex items-center gap-2"
                  disabled={isOptimizing}
                >
                  <Play className="h-4 w-4" />
                  Start Optimization
                </button>
              )}
            </div>
          </div>

          {/* Parameters Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Trials per Asset
              </label>
              <input
                type="number"
                value={parameters.n_trials}
                onChange={(e) => setParameters(prev => ({ ...prev, n_trials: parseInt(e.target.value) || 10 }))}
                className="input-theme w-full"
                min="5"
                max="100"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                CPU Cores
              </label>
              <input
                type="number"
                value={parameters.n_cores}
                onChange={(e) => setParameters(prev => ({ ...prev, n_cores: parseInt(e.target.value) || 4 }))}
                className="input-theme w-full"
                min="1"
                max="16"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Number of Assets
              </label>
              <input
                type="number"
                value={parameters.n_assets}
                onChange={(e) => setParameters(prev => ({ ...prev, n_assets: parseInt(e.target.value) || 20 }))}
                className="input-theme w-full"
                min="1"
                max="50"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Categories
              </label>
              <input
                type="number"
                value={parameters.n_categories}
                onChange={(e) => setParameters(prev => ({ ...prev, n_categories: parseInt(e.target.value) || 4 }))}
                className="input-theme w-full"
                min="1"
                max="10"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Days Back
              </label>
              <input
                type="number"
                value={parameters.days_back}
                onChange={(e) => setParameters(prev => ({ ...prev, days_back: parseInt(e.target.value) || 365 }))}
                className="input-theme w-full"
                min="0"
                max="1095"
              />
            </div>
          </div>

          {/* Status Display */}
          {optimizationStatus && (
            <div className="mt-6 p-4 rounded-lg glass" style={{ backgroundColor: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getStatusIcon(optimizationStatus.status)}
                  <div>
                    <h3 className="font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                      Optimization Status
                    </h3>
                    <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      {optimizationStatus.message}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-semibold ${getStatusColor(optimizationStatus.status)}`}>
                    {optimizationStatus.status.toUpperCase()}
                  </div>
                  {optimizationStatus.progress > 0 && (
                    <div className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      {optimizationStatus.progress}% Complete
                    </div>
                  )}
                </div>
              </div>
              
              {optimizationStatus.progress > 0 && (
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${optimizationStatus.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Optimization History */}
        <div className="card glass">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Optimization History
              </h2>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Recent optimization runs and results
              </p>
            </div>
            <button
              onClick={fetchOptimizationHistory}
              className="btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {optimizationHistory.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
              <p className="transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                No optimization history available
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--glass-border)' }}>
                    <th className="text-left py-3 px-4 font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                      Task ID
                    </th>
                    <th className="text-left py-3 px-4 font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                      Status
                    </th>
                    <th className="text-left py-3 px-4 font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                      Assets
                    </th>
                    <th className="text-left py-3 px-4 font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                      Created
                    </th>
                    <th className="text-left py-3 px-4 font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                      Completed
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {optimizationHistory.map((item) => (
                    <tr key={item.id} className="border-b" style={{ borderColor: 'var(--glass-border)' }}>
                      <td className="py-3 px-4">
                        <code className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                          {item.id.slice(0, 8)}...
                        </code>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                          {getStatusIcon(item.status)}
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        {item.parameters?.n_assets || 'N/A'}
                      </td>
                      <td className="py-3 px-4 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        {item.completed_at ? new Date(item.completed_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 rounded-lg bg-red-50 border border-red-200">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-red-500" />
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}