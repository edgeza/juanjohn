'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, TrendingUp, TrendingDown, Minus, Activity, Bell, Zap, DollarSign, BarChart3, Target, AlertTriangle } from 'lucide-react';
import PriceChart from '@/components/charts/PriceChart';
import Link from 'next/link';

interface AssetAnalytics {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  current_price: number;
  potential_return: number;
  total_return: number;
  signal_strength: number;
  risk_level: string;
  sharpe_ratio: number;
  max_drawdown: number;
  optimized_degree: number | null;
  optimized_kstd: number | null;
  optimized_lookback: number | null;
  data_points: number;
  total_available: number;
  interval: string;
  timestamp: string;
}

export default function AssetAnalyticsPage() {
  const params = useParams();
  const symbol = decodeURIComponent(params.symbol as string);
  
  const [analytics, setAnalytics] = useState<AssetAnalytics | null>(null);
  const [historicalData, setHistoricalData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssetAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch analytics for this specific asset
      const { getPublicApiBase } = await import('@/lib/runtimeEnv');
      const apiBase = getPublicApiBase();
      const analyticsResponse = await fetch(`${apiBase}/api/v1/data/analytics/${encodeURIComponent(symbol)}`);
      if (!analyticsResponse.ok) {
        throw new Error(`Failed to fetch analytics: ${analyticsResponse.status}`);
      }
      const analyticsData = await analyticsResponse.json();
      setAnalytics(analyticsData);
      
      // Fetch historical data for charts
      const historicalResponse = await fetch(`${apiBase}/api/v1/data/historical/${encodeURIComponent(symbol)}?days=30`);
      if (historicalResponse.ok) {
        const historicalData = await historicalResponse.json();
        setHistoricalData(historicalData);
      }
    } catch (err) {
      console.error('Error fetching asset analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      fetchAssetAnalytics();
    }
  }, [symbol]);

  const getSignalIcon = (signal: string) => {
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

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'border-green-500/30 bg-green-500/5';
      case 'SELL':
        return 'border-red-500/30 bg-red-500/5';
      case 'HOLD':
        return 'border-yellow-500/30 bg-yellow-500/5';
      default:
        return 'border-gray-500/30 bg-gray-500/5';
    }
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
            <div className="grid gap-6 md:grid-cols-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-48 rounded-lg bg-gray-200"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="mx-auto max-w-7xl">
          <div className="rounded-lg border border-red-200 bg-red-50 p-6">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <span className="text-red-800">{error}</span>
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
          <div className="flex items-center space-x-4 mb-4">
            <Link href="/assets" className="flex items-center space-x-2 text-sm hover:underline" style={{ color: 'var(--text-secondary)' }}>
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Assets</span>
            </Link>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {symbol} Analytics
              </h1>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Detailed analysis and optimization results
              </p>
            </div>
            
            {analytics && (
              <div className={`rounded-lg border-2 p-4 ${getSignalColor(analytics.signal)}`}>
                <div className="flex items-center space-x-3">
                  {getSignalIcon(analytics.signal)}
                  <div>
                    <p className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                      {analytics.signal} Signal
                    </p>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                      Risk: <span className={getRiskLevelColor(analytics.risk_level)}>{analytics.risk_level}</span>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {analytics ? (
          <div className="space-y-8">
            {/* Price and Returns Section */}
            <div className="grid gap-6 md:grid-cols-2">
              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <DollarSign className="h-6 w-6 text-blue-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Current Price</h3>
                </div>
                <div className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                  ${analytics.current_price.toFixed(4)}
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Last updated: {new Date(analytics.timestamp).toLocaleString()}
                </p>
              </div>

              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <Zap className="h-6 w-6 text-yellow-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Returns</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--text-secondary)' }}>Potential Return:</span>
                    <span className={`font-bold ${analytics.potential_return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {analytics.potential_return > 0 ? '+' : ''}{analytics.potential_return.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--text-secondary)' }}>Total Return:</span>
                    <span className={`font-bold ${analytics.total_return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {analytics.total_return > 0 ? '+' : ''}{analytics.total_return.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Price Chart */}
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <div className="flex items-center space-x-3 mb-4">
                <BarChart3 className="h-6 w-6 text-blue-500" />
                <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Price Chart</h3>
              </div>
              {historicalData?.data ? (
                <PriceChart 
                  symbol={symbol} 
                  data={{
                    labels: historicalData.data.map((item: any) => item.date),
                    prices: historicalData.data.map((item: any) => item.close),
                    upperBand: historicalData.data.map((item: any) => item.high),
                    lowerBand: historicalData.data.map((item: any) => item.low),
                    signal: analytics?.signal
                  }}
                />
              ) : (
                <div className="flex items-center justify-center h-80">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--text-secondary)' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>Loading price chart...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Performance Metrics */}
            <div className="grid gap-6 md:grid-cols-3">
              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <BarChart3 className="h-6 w-6 text-green-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Sharpe Ratio</h3>
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                  {analytics.sharpe_ratio?.toFixed(2) || 'N/A'}
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Risk-adjusted return measure
                </p>
              </div>

              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <Target className="h-6 w-6 text-red-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Max Drawdown</h3>
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                  {analytics.max_drawdown?.toFixed(2) || 'N/A'}%
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Maximum historical loss
                </p>
              </div>

              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <Activity className="h-6 w-6 text-blue-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Signal Strength</h3>
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                  {analytics.signal_strength.toFixed(2)}
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Confidence in signal
                </p>
              </div>
            </div>

            {/* Additional Analytics */}
            <div className="grid gap-6 md:grid-cols-2">
              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <Zap className="h-6 w-6 text-yellow-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Data Coverage</h3>
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                  {analytics.data_points}/{analytics.total_available}
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Data points analyzed
                </p>
              </div>

              <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="flex items-center space-x-3 mb-4">
                  <Bell className="h-6 w-6 text-purple-500" />
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Risk Level</h3>
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                  {analytics.risk_level}
                </div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Risk assessment
                </p>
              </div>
            </div>



            {/* Analysis Details */}
            <div className="rounded-lg border p-6 shadow-sm" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
              <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Analysis Details</h3>
              
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Interval</h4>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {analytics.interval}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Risk Level</h4>
                  <p className={`text-sm font-medium ${getRiskLevelColor(analytics.risk_level)}`}>
                    {analytics.risk_level}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Analysis Date</h4>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {new Date(analytics.timestamp).toLocaleDateString()}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Analysis Time</h4>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {new Date(analytics.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border p-8 text-center" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
            <AlertTriangle className="mx-auto h-12 w-12" style={{ color: 'var(--text-secondary)' }} />
            <h3 className="mt-4 text-lg font-medium" style={{ color: 'var(--text-primary)' }}>
              No analytics found
            </h3>
            <p className="mt-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              No optimization data available for {symbol}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}