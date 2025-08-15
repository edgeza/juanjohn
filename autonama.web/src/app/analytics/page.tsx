'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import dynamic from 'next/dynamic';
import { ModernCharts } from '@/components/analytics/ModernCharts';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface AnalyticsData {
  signal_distribution: {
    BUY: number;
    SELL: number;
    HOLD: number;
  };
  performance_metrics: {
    avg_potential_return: number;
    best_buy_signal: { symbol: string; return: number };
    best_sell_signal: { symbol: string; return: number };
    top_performer: { symbol: string; return: number };
  };
  return_distribution: {
    ranges: string[];
    counts: number[];
  };
  price_vs_return_data: Array<{
    symbol: string;
    price: number;
    potential_return: number;
    signal: string;
  }>;
  total_assets: number;
}

interface AssetAnalytics {
  symbol: string;
  signal: string;
  current_price: number;
  potential_return: number;
  total_return: number;
  signal_strength: number;
  risk_level: string;
  sharpe_ratio: number;
  max_drawdown: number;
  optimized_degree?: number;
  optimized_kstd?: number;
  optimized_lookback?: number;
  data_points: number;
  total_available: number;
  interval: string;
  timestamp: string;
}

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<string>('BTCUSDT');
  const [assetAnalytics, setAssetAnalytics] = useState<AssetAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalyticsData();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAnalyticsData, 300000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedAsset) {
      fetchAssetAnalytics(selectedAsset);
    }
  }, [selectedAsset]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/data/analytics-dashboard');
      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }
      const data = await response.json();
      console.log('[Analytics] Fetched data:', data);
      setAnalyticsData(data);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      console.error('[Analytics] Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssetAnalytics = async (symbol: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/data/analytics/${symbol}`);
      if (!response.ok) {
        throw new Error('Failed to fetch asset analytics');
      }
      const data = await response.json();
      console.log('[Analytics] Asset data for', symbol, ':', data);
      setAssetAnalytics(data);
    } catch (err) {
      console.error('[Analytics] Error fetching asset analytics:', err);
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY': return 'bg-green-100 text-green-800 border-green-200';
      case 'SELL': return 'bg-red-100 text-red-800 border-red-200';
      case 'HOLD': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'bg-green-100 text-green-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'HIGH': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <Button onClick={fetchAnalyticsData}>Retry</Button>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No analytics data available</p>
      </div>
    );
  }

  // Prepare chart data with theme support
  const isDark = typeof window !== 'undefined' && document.documentElement.classList.contains('dark');
  const textColor = isDark ? '#E5E7EB' : '#374151';
  const bgColor = isDark ? '#1F2937' : '#FFFFFF';
  const gridColor = isDark ? '#374151' : '#E5E7EB';

  const signalDistributionData = [
    {
      values: [analyticsData.signal_distribution.BUY, analyticsData.signal_distribution.SELL, analyticsData.signal_distribution.HOLD],
      labels: ['BUY', 'SELL', 'HOLD'],
      type: 'pie',
      marker: {
        colors: ['#10B981', '#EF4444', '#F59E0B']
      },
      textinfo: 'label+percent',
      textposition: 'outside',
      textfont: { color: textColor }
    }
  ];

  const returnDistributionData = [
    {
      x: analyticsData.return_distribution.ranges,
      y: analyticsData.return_distribution.counts,
      type: 'bar',
      marker: {
        color: '#3B82F6',
        line: { color: '#1E40AF', width: 1 }
      },
      text: analyticsData.return_distribution.counts,
      textposition: 'auto',
      textfont: { color: textColor }
    }
  ];

  const priceVsReturnData = [
    {
      x: analyticsData.price_vs_return_data.map(d => d.price),
      y: analyticsData.price_vs_return_data.map(d => d.potential_return),
      mode: 'markers',
      type: 'scatter',
      marker: {
        color: analyticsData.price_vs_return_data.map(d => 
          d.signal === 'BUY' ? '#10B981' : d.signal === 'SELL' ? '#EF4444' : '#F59E0B'
        ),
        size: 10,
        line: { width: 1, color: '#374151' }
      },
      text: analyticsData.price_vs_return_data.map(d => d.symbol),
      hovertemplate: '<b>%{text}</b><br>Price: $%{x:,.2f}<br>Potential Return: %{y:.2f}%<br>Signal: %{marker.color}<extra></extra>',
      hoverlabel: { bgcolor: bgColor, bordercolor: gridColor, font: { color: textColor } }
    }
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>Analytics & Performance</h1>
          {lastUpdated && (
            <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Last updated: {lastUpdated}
            </p>
          )}
        </div>
        <Button onClick={fetchAnalyticsData} variant="outline">
          Refresh Data
        </Button>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="glass-effect">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-secondary">Top Performer</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {analyticsData.performance_metrics.top_performer.symbol}
            </div>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {analyticsData.performance_metrics.top_performer.return}%
            </p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-secondary">Best BUY Signal</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {analyticsData.performance_metrics.best_buy_signal.symbol}
            </div>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {analyticsData.performance_metrics.best_buy_signal.return}%
            </p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-secondary">Best SELL Signal</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {analyticsData.performance_metrics.best_sell_signal.symbol}
            </div>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {analyticsData.performance_metrics.best_sell_signal.return}%
            </p>
          </CardContent>
        </Card>

        <Card className="glass-effect">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-secondary">Avg Potential Return</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {analyticsData.performance_metrics.avg_potential_return}%
            </div>
            <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              Across {analyticsData.total_assets} assets
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <Tabs value="overview" onValueChange={() => {}} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
          <TabsTrigger value="asset-analysis">Asset Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <ModernCharts
            signalDistribution={analyticsData.signal_distribution}
            returnDistribution={analyticsData.return_distribution}
            priceReturnData={analyticsData.price_vs_return_data}
            isDark={isDark}
          />
        </TabsContent>

        <TabsContent value="distribution" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Signal Distribution by Return Range */}
            <Card>
              <CardHeader>
                <CardTitle>Signal Distribution by Return Range</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.return_distribution.ranges.map((range, index) => (
                    <div key={range} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{range}</span>
                      <Badge variant="secondary">
                        {analyticsData.return_distribution.counts[index]} assets
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Performance Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Performance Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Assets Analyzed:</span>
                    <Badge variant="outline">{analyticsData.total_assets}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>BUY Signals:</span>
                    <Badge className="bg-green-100 text-green-800">
                      {analyticsData.signal_distribution.BUY}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>SELL Signals:</span>
                    <Badge className="bg-red-100 text-red-800">
                      {analyticsData.signal_distribution.SELL}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>HOLD Signals:</span>
                    <Badge className="bg-yellow-100 text-yellow-800">
                      {analyticsData.signal_distribution.HOLD}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="asset-analysis" className="space-y-6">
          {/* Asset Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Asset Analysis</CardTitle>
              <p className="text-sm text-gray-600">Select Asset for Detailed Analysis</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <Select value={selectedAsset} onValueChange={setSelectedAsset}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select asset" />
                    </SelectTrigger>
                    <SelectContent>
                      {analyticsData.price_vs_return_data.map((asset) => (
                        <SelectItem key={asset.symbol} value={asset.symbol}>
                          {asset.symbol}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {assetAnalytics && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Signal</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Badge className={getSignalColor(assetAnalytics.signal)}>
                          {assetAnalytics.signal}
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Current Price</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-bold">
                          ${assetAnalytics.current_price.toFixed(2)}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Potential Return</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className={`text-lg font-bold ${
                          assetAnalytics.potential_return > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {assetAnalytics.potential_return.toFixed(2)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Risk Level</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Badge className={getRiskColor(assetAnalytics.risk_level)}>
                          {assetAnalytics.risk_level}
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Sharpe Ratio</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-bold">
                          {assetAnalytics.sharpe_ratio.toFixed(2)}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Max Drawdown</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-bold text-red-600">
                          {assetAnalytics.max_drawdown.toFixed(2)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Signal Strength</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-bold">
                          {(assetAnalytics.signal_strength * 100).toFixed(1)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Data Points</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-lg font-bold">
                          {assetAnalytics.data_points}
                        </div>
                        <p className="text-xs text-gray-600">
                          of {assetAnalytics.total_available} available
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 
 
 