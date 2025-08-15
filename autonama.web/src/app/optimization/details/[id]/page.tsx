'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Target,
  Clock,
  CheckCircle,
  AlertCircle,
  Download,
  RefreshCw,
  DollarSign,
  Percent,
  Activity
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

interface OptimizationResult {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  completed_at?: string;
  parameters: {
    n_trials: number;
    n_assets: number;
    n_cores: number;
    n_categories: number;
    days_back: number;
  };
  results?: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    profit_factor: number;
    optimized_assets: number;
    best_parameters: {
      lookback: number;
      std_dev: number;
      atr_period: number;
      atr_multiplier: number;
    };
    performance_by_asset: Array<{
      symbol: string;
      return: number;
      sharpe: number;
      drawdown: number;
      trades: number;
    }>;
    equity_curve: Array<{
      date: string;
      value: number;
      drawdown: number;
    }>;
  };
  error?: string;
}

export default function OptimizationDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const taskId = params.id as string;

  const fetchOptimizationResult = async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    
    try {
      const response = await fetch(`/api/v1/autonama/optimize/status/${taskId}`);
      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        console.error('Failed to fetch optimization result');
      }
    } catch (error) {
      console.error('Error fetching optimization result:', error);
    } finally {
      setLoading(false);
      if (showRefreshing) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOptimizationResult();
    
    // Auto-refresh if optimization is still running
    const interval = setInterval(() => {
      if (result?.status === 'running' || result?.status === 'pending') {
        fetchOptimizationResult();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [taskId, result?.status]);

  const handleExport = () => {
    if (!result?.results) return;
    
    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `optimization_${taskId.slice(0, 8)}_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="mx-auto max-w-7xl">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="mx-auto max-w-7xl">
          <div className="text-center py-12">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-4 text-lg font-semibold text-gray-900">Optimization Not Found</h3>
            <p className="mt-2 text-gray-600">
              The optimization result could not be loaded.
            </p>
            <button
              onClick={() => router.back()}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              <ArrowLeft className="h-4 w-4" />
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-5 w-5" />
              Back
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Optimization Details
              </h1>
              <p className="text-gray-600">
                Task ID: {taskId.slice(0, 8)}...
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchOptimizationResult(true)}
              disabled={refreshing}
              className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            {result.results && (
              <button
                onClick={handleExport}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              >
                <Download className="h-4 w-4" />
                Export
              </button>
            )}
          </div>
        </div>

        {/* Status Banner */}
        <StatusBanner result={result} />

        {/* Parameters */}
        <ParametersCard parameters={result.parameters} />

        {/* Results */}
        {result.results && (
          <>
            <MetricsOverview results={result.results} />
            <div className="grid gap-8 lg:grid-cols-2">
              <EquityCurveChart data={result.results.equity_curve} />
              <AssetPerformanceChart data={result.results.performance_by_asset} />
            </div>
            <OptimizedParametersCard parameters={result.results.best_parameters} />
          </>
        )}
      </div>
    </div>
  );
}

function StatusBanner({ result }: { result: OptimizationResult }) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          bg: 'bg-green-50 border-green-200',
          text: 'text-green-800',
          icon: <CheckCircle className="h-5 w-5 text-green-600" />
        };
      case 'running':
        return {
          bg: 'bg-blue-50 border-blue-200',
          text: 'text-blue-800',
          icon: <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        };
      case 'failed':
        return {
          bg: 'bg-red-50 border-red-200',
          text: 'text-red-800',
          icon: <AlertCircle className="h-5 w-5 text-red-600" />
        };
      default:
        return {
          bg: 'bg-yellow-50 border-yellow-200',
          text: 'text-yellow-800',
          icon: <Clock className="h-5 w-5 text-yellow-600" />
        };
    }
  };

  const config = getStatusConfig(result.status);

  return (
    <div className={`mb-8 rounded-lg border-2 p-4 ${config.bg}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {config.icon}
          <div>
            <h3 className={`font-semibold ${config.text}`}>
              {result.status.charAt(0).toUpperCase() + result.status.slice(1)}
            </h3>
            <p className="text-sm text-gray-600">
              Started: {new Date(result.created_at).toLocaleString()}
              {result.completed_at && (
                <> • Completed: {new Date(result.completed_at).toLocaleString()}</>
              )}
            </p>
          </div>
        </div>
        
        {result.progress !== undefined && result.status === 'running' && (
          <div className="flex items-center gap-3">
            <div className="w-32 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${result.progress}%` }}
              ></div>
            </div>
            <span className="text-sm font-medium text-gray-700">{result.progress}%</span>
          </div>
        )}
      </div>
      
      {result.error && (
        <div className="mt-3 rounded bg-red-100 p-3">
          <p className="text-sm font-medium text-red-800">Error Details:</p>
          <p className="text-sm text-red-700">{result.error}</p>
        </div>
      )}
    </div>
  );
}

function ParametersCard({ parameters }: { parameters: OptimizationResult['parameters'] }) {
  return (
    <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Optimization Parameters</h2>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="text-center">
          <Target className="mx-auto h-8 w-8 text-blue-600 mb-2" />
          <p className="text-2xl font-bold text-gray-900">{parameters.n_trials}</p>
          <p className="text-sm text-gray-600">Trials per Asset</p>
        </div>
        <div className="text-center">
          <BarChart3 className="mx-auto h-8 w-8 text-green-600 mb-2" />
          <p className="text-2xl font-bold text-gray-900">{parameters.n_assets}</p>
          <p className="text-sm text-gray-600">Assets</p>
        </div>
        <div className="text-center">
          <Activity className="mx-auto h-8 w-8 text-purple-600 mb-2" />
          <p className="text-2xl font-bold text-gray-900">{parameters.n_cores}</p>
          <p className="text-sm text-gray-600">CPU Cores</p>
        </div>
        <div className="text-center">
          <TrendingUp className="mx-auto h-8 w-8 text-orange-600 mb-2" />
          <p className="text-2xl font-bold text-gray-900">{parameters.n_categories}</p>
          <p className="text-sm text-gray-600">Categories</p>
        </div>
        <div className="text-center">
          <Clock className="mx-auto h-8 w-8 text-red-600 mb-2" />
          <p className="text-2xl font-bold text-gray-900">
            {parameters.days_back === 0 ? 'Max' : `${parameters.days_back}d`}
          </p>
          <p className="text-sm text-gray-600">Data Period</p>
        </div>
      </div>
    </div>
  );
}

function MetricsOverview({ results }: { results: NonNullable<OptimizationResult['results']> }) {
  const metrics = [
    {
      title: 'Total Return',
      value: `${(results.total_return * 100).toFixed(2)}%`,
      icon: <DollarSign className="h-6 w-6" />,
      color: results.total_return >= 0 ? 'text-green-600' : 'text-red-600',
      bg: results.total_return >= 0 ? 'bg-green-50' : 'bg-red-50'
    },
    {
      title: 'Sharpe Ratio',
      value: results.sharpe_ratio.toFixed(2),
      icon: <TrendingUp className="h-6 w-6" />,
      color: results.sharpe_ratio >= 1 ? 'text-green-600' : 'text-orange-600',
      bg: results.sharpe_ratio >= 1 ? 'bg-green-50' : 'bg-orange-50'
    },
    {
      title: 'Max Drawdown',
      value: `${(results.max_drawdown * 100).toFixed(2)}%`,
      icon: <TrendingDown className="h-6 w-6" />,
      color: 'text-red-600',
      bg: 'bg-red-50'
    },
    {
      title: 'Win Rate',
      value: `${(results.win_rate * 100).toFixed(1)}%`,
      icon: <Percent className="h-6 w-6" />,
      color: results.win_rate >= 0.5 ? 'text-green-600' : 'text-orange-600',
      bg: results.win_rate >= 0.5 ? 'bg-green-50' : 'bg-orange-50'
    }
  ];

  return (
    <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric, index) => (
        <div key={index} className={`rounded-lg p-6 ${metric.bg}`}>
          <div className="flex items-center gap-3">
            <div className={metric.color}>
              {metric.icon}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">{metric.title}</p>
              <p className={`text-2xl font-bold ${metric.color}`}>{metric.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EquityCurveChart({ data }: { data: Array<{ date: string; value: number; drawdown: number }> }) {
  const chartData = data.map(d => ({
    date: new Date(d.date).toLocaleDateString(),
    value: d.value,
    drawdown: d.drawdown
  }));

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip 
            formatter={(value: number) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#3b82f6" 
            fill="#3b82f6" 
            fillOpacity={0.1}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function AssetPerformanceChart({ data }: { data: Array<{ symbol: string; return: number; sharpe: number; drawdown: number; trades: number }> }) {
  const chartData = data.map(d => ({
    symbol: d.symbol,
    return: (d.return * 100).toFixed(2),
    returnValue: d.return * 100,
    sharpe: d.sharpe.toFixed(2),
    drawdown: (d.drawdown * 100).toFixed(2),
    trades: d.trades
  }));

  return (
    <div className="rounded-lg bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Performance</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="symbol" />
          <YAxis />
          <Tooltip 
            formatter={(value: number, name: string) => {
              if (name === 'returnValue') return [`${value.toFixed(2)}%`, 'Return'];
              return [value, name];
            }}
            labelFormatter={(label) => `Asset: ${label}`}
          />
          <Bar 
            dataKey="returnValue" 
            fill="#22c55e"
            name="Return (%)"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function OptimizedParametersCard({ parameters }: { parameters: { lookback: number; std_dev: number; atr_period: number; atr_multiplier: number } }) {
  return (
    <div className="mt-8 rounded-lg bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Optimized Parameters</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="text-center">
          <p className="text-3xl font-bold text-blue-600">{parameters.lookback}</p>
          <p className="text-sm text-gray-600">Lookback Period</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold text-green-600">{parameters.std_dev.toFixed(2)}</p>
          <p className="text-sm text-gray-600">Standard Deviation</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold text-purple-600">{parameters.atr_period}</p>
          <p className="text-sm text-gray-600">ATR Period</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold text-orange-600">{parameters.atr_multiplier.toFixed(2)}</p>
          <p className="text-sm text-gray-600">ATR Multiplier</p>
        </div>
      </div>
    </div>
  );
}