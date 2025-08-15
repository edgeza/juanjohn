'use client';

import { useState, useEffect } from 'react';
import { Bell, TrendingUp, TrendingDown, Minus, Filter, RefreshCw, AlertTriangle, CheckCircle, Clock, Zap, DollarSign, Activity } from 'lucide-react';

interface OptimizationAlert {
  id: number;
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  current_price: number;
  potential_return: number;
  total_return?: number;
  signal_strength: number;
  risk_level: string;
  interval: string;
  optimized_degree?: number | null;
  optimized_kstd?: number | null;
  optimized_lookback?: number | null;
  sharpe_ratio?: number;
  max_drawdown?: number;
  data_points?: number;
  total_available?: number;
  timestamp?: string;
  created_at?: string;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<OptimizationAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'BUY' | 'SELL' | 'HOLD'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [summary, setSummary] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch alerts from the database (bust cache, always get fresh)
      const alertsResponse = await fetch(`http://localhost:8000/api/v1/optimization/alerts?v=${Date.now()}` , { cache: 'no-store' });
      if (!alertsResponse.ok) {
        throw new Error(`Failed to fetch alerts: ${alertsResponse.status}`);
      }
      
      const alertsData: OptimizationAlert[] = await alertsResponse.json();

      // Sort alerts by most recent created_at/timestamp (robust to missing fields)
      const sorted = [...alertsData].sort((a, b) => {
        const aStr: string | undefined = a.created_at ?? a.timestamp;
        const bStr: string | undefined = b.created_at ?? b.timestamp;
        const at = aStr ? new Date(aStr).getTime() : 0;
        const bt = bStr ? new Date(bStr).getTime() : 0;
        return bt - at;
      });

      // Keep only the latest ingestion batch (robust to missing fields)
      const first: OptimizationAlert | undefined = sorted[0];
      const firstDateStr: string | undefined = first?.created_at ?? first?.timestamp;
      const latestMs = firstDateStr ? new Date(firstDateStr).getTime() : 0;
      // Allow a small window to account for per-row timestamp jitter within one batch (2 minutes)
      const latestOnly = sorted.filter(a => {
        const dateStr = a.created_at ?? a.timestamp;
        if (!dateStr) return false;
        const t = new Date(dateStr).getTime();
        return Math.abs(t - latestMs) < 120000;
      });
      setAlerts(latestOnly);

      // Compute overall last updated from the data
      if (latestOnly.length > 0) {
        const firstItem = latestOnly[0] as OptimizationAlert | undefined;
        const latestStr: string | undefined = firstItem?.created_at ?? firstItem?.timestamp;
        setLastUpdated(latestStr ? new Date(latestStr).toISOString() : null);
      } else {
        setLastUpdated(null);
      }
      
      // Calculate summary from alerts data
      if (latestOnly.length > 0) {
        const buySignals = latestOnly.filter((a: OptimizationAlert) => a.signal === 'BUY').length;
        const sellSignals = latestOnly.filter((a: OptimizationAlert) => a.signal === 'SELL').length;
        const holdSignals = latestOnly.filter((a: OptimizationAlert) => a.signal === 'HOLD').length;
        const avgPotentialReturn = latestOnly.reduce((sum: number, a: OptimizationAlert) => sum + a.potential_return, 0) / latestOnly.length;
        const avgTotalReturn = latestOnly.reduce((sum: number, a: OptimizationAlert) => sum + (a.total_return || 0), 0) / latestOnly.length;
        
        setSummary({
          total_assets: latestOnly.length,
          buy_signals: buySignals,
          sell_signals: sellSignals,
          hold_signals: holdSignals,
          avg_potential_return: avgPotentialReturn,
          avg_total_return: avgTotalReturn
        });
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, 60000); // Refresh every 60 seconds
      return () => clearInterval(interval);
    }
    
    return undefined;
  }, [autoRefresh]);

  const filteredAlerts = alerts.filter(alert => 
    filter === 'all' || alert.signal === filter
  );

  const getAlertIcon = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return <TrendingUp className="h-6 w-6 text-green-500" />;
      case 'SELL':
        return <TrendingDown className="h-6 w-6 text-red-500" />;
      case 'HOLD':
        return <Minus className="h-6 w-6 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-6 w-6 text-gray-500" />;
    }
  };

  const getAlertColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'border-green-500/30 bg-green-500/5 hover:bg-green-500/10';
      case 'SELL':
        return 'border-red-500/30 bg-red-500/5 hover:bg-red-500/10';
      case 'HOLD':
        return 'border-yellow-500/30 bg-yellow-500/5 hover:bg-yellow-500/10';
      default:
        return 'border-gray-500/30 bg-gray-500/5 hover:bg-gray-500/10';
    }
  };

  const getPotentialReturnColor = (returnValue: number) => {
    if (returnValue >= 20) return 'text-green-500';
    if (returnValue >= 10) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW':
        return 'text-green-500';
      case 'MEDIUM':
        return 'text-yellow-500';
      case 'HIGH':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="mx-auto max-w-7xl">
          <div className="animate-pulse">
            <div className="mb-8 h-8 w-48 rounded bg-gray-200"></div>
            <div className="mb-6 h-12 w-full rounded bg-gray-200"></div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-48 rounded-lg bg-gray-200"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Trading Alerts
              </h1>
              <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Real-time trading signals and optimization alerts
              </p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleString() : '—'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">

          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="mb-8 grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Total Assets</p>
                  <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                    {summary.total_assets}
                  </p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </div>
            
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Buy Signals</p>
                  <p className="text-2xl font-bold text-green-500">
                    {summary.buy_signals}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            </div>
            
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Sell Signals</p>
                  <p className="text-2xl font-bold text-red-500">
                    {summary.sell_signals}
                  </p>
                </div>
                <TrendingDown className="h-8 w-8 text-red-500" />
              </div>
            </div>
            
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Hold Signals</p>
                  <p className="text-2xl font-bold text-yellow-500">
                    {summary.hold_signals}
                  </p>
                </div>
                <Minus className="h-8 w-8 text-yellow-500" />
              </div>
            </div>
            
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Avg Potential Return</p>
                  <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                    {summary.avg_potential_return?.toFixed(2)}%
                  </p>
                </div>
                <Zap className="h-8 w-8 text-yellow-500" />
              </div>
            </div>


          </div>
        )}

        {/* Filters */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Filter className="h-5 w-5" style={{ color: 'var(--text-secondary)' }} />
            <div className="flex space-x-2">
              {(['all', 'BUY', 'SELL', 'HOLD'] as const).map((filterType) => (
                <button
                  key={filterType}
                  onClick={() => setFilter(filterType)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === filterType
                      ? 'bg-blue-500 text-white'
                      : 'border hover:bg-gray-50'
                  }`}
                  style={{ 
                    borderColor: filter !== filterType ? 'var(--border-color)' : undefined,
                    color: filter !== filterType ? 'var(--text-primary)' : undefined
                  }}
                >
                  {filterType === 'all' ? 'All' : filterType}
                </button>
              ))}
            </div>
          </div>
          

        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}

        {/* Alerts Grid - Card Layout */}
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <div className="rounded-lg border p-8 text-center" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <Bell className="mx-auto h-12 w-12" style={{ color: 'var(--text-secondary)' }} />
              <h3 className="mt-4 text-lg font-medium" style={{ color: 'var(--text-primary)' }}>
                No alerts found
              </h3>
              <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                {filter === 'all' 
                  ? 'No alerts available. Try triggering ingestion or refreshing.'
                  : `No ${filter} signals found.`
                }
              </p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filteredAlerts.map((alert: OptimizationAlert) => (
                <div
                  key={alert.id}
                  className={`rounded-lg border-2 p-6 transition-all hover:shadow-lg cursor-pointer ${getAlertColor(alert.signal)}`}
                  style={{ borderColor: 'var(--border-color)' }}
                  onClick={() => window.open(`/assets/${encodeURIComponent(alert.symbol)}`, '_blank')}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {getAlertIcon(alert.signal)}
                      <div>
                        <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                          {alert.symbol}
                        </h3>
                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                          {alert.signal} • <span className={getRiskLevelColor(alert.risk_level)}>{alert.risk_level}</span>
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Price and Returns */}
                  <div className="mb-4">
                    <div className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                      ${alert.current_price.toFixed(4)}
                    </div>
                    <div className="space-y-1">
                      <div className={`text-sm font-medium ${getPotentialReturnColor(alert.potential_return)}`}>
                        {alert.potential_return > 0 ? '+' : ''}{alert.potential_return.toFixed(2)}% potential
                      </div>
                    </div>
                  </div>
                  
                  {/* Metrics Grid */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p style={{ color: 'var(--text-secondary)' }}>Sharpe Ratio</p>
                      <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
                        {alert.sharpe_ratio ? alert.sharpe_ratio.toFixed(2) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p style={{ color: 'var(--text-secondary)' }}>Max Drawdown</p>
                      <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
                        {alert.max_drawdown ? alert.max_drawdown.toFixed(2) + '%' : 'N/A'}
                      </p>
                    </div>
                  </div>
                  
                  {/* Footer */}
                  <div className="mt-4 pt-3 border-t text-xs" style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
                    <div className="flex justify-between">
                      <span>{alert.interval}</span>
                      <span>{alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : ''}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 