'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Activity, Target, Zap, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';
import { apiClient } from '@/lib/apiClient';

// Utility functions
const getSignalColor = (signal: string) => {
  switch (signal.toLowerCase()) {
    case 'buy': return 'text-green-500';
    case 'sell': return 'text-red-500';
    case 'hold': return 'text-yellow-500';
    default: return 'text-gray-500';
  }
};

const getSignalBgColor = (signal: string) => {
  switch (signal.toLowerCase()) {
    case 'buy': return 'bg-green-500/10 border-green-500/20';
    case 'sell': return 'bg-red-500/10 border-red-500/20';
    case 'hold': return 'bg-yellow-500/10 border-yellow-500/20';
    default: return 'bg-gray-500/10 border-gray-500/20';
  }
};

const formatPrice = (price: number) => {
  if (price >= 1) return `$${price.toFixed(2)}`;
  if (price >= 0.01) return `$${price.toFixed(4)}`;
  return `$${price.toFixed(8)}`;
};

const formatPercentage = (value: number) => {
  return `${value.toFixed(2)}%`;
};

interface SignalData {
  symbol: string;
  signal: string;
  price: number;
  channel_value: number;
  upper_band: number;
  lower_band: number;
  deviation_percent: number;
  channel_range_percent: number;
  timestamp: string;
  confidence_score: number;
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSignal, setSelectedSignal] = useState('all');

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (selectedSignal !== 'all') params.append('signal_type', selectedSignal);
      
      const data = await apiClient.getLiveSignals();
      setSignals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signals');
      // Set mock data for demo
      setSignals([
        {
          symbol: 'BTC/USDT',
          signal: 'BUY',
          price: 43250.50,
          channel_value: 43000.00,
          upper_band: 44500.00,
          lower_band: 41500.00,
          deviation_percent: -0.35,
          channel_range_percent: 6.98,
          timestamp: new Date().toISOString(),
          confidence_score: 0.85
        },
        {
          symbol: 'ETH/USDT',
          signal: 'HOLD',
          price: 2650.75,
          channel_value: 2650.00,
          upper_band: 2750.00,
          lower_band: 2550.00,
          deviation_percent: 0.03,
          channel_range_percent: 7.55,
          timestamp: new Date().toISOString(),
          confidence_score: 0.72
        },
        {
          symbol: 'SOL/USDT',
          signal: 'SELL',
          price: 98.45,
          channel_value: 100.00,
          upper_band: 105.00,
          lower_band: 95.00,
          deviation_percent: -1.55,
          channel_range_percent: 10.20,
          timestamp: new Date().toISOString(),
          confidence_score: 0.78
        },
        {
          symbol: 'ADA/USDT',
          signal: 'BUY',
          price: 0.485,
          channel_value: 0.480,
          upper_band: 0.495,
          lower_band: 0.465,
          deviation_percent: 1.04,
          channel_range_percent: 6.25,
          timestamp: new Date().toISOString(),
          confidence_score: 0.82
        },
        {
          symbol: 'BNB/USDT',
          signal: 'HOLD',
          price: 320.50,
          channel_value: 320.00,
          upper_band: 325.00,
          lower_band: 315.00,
          deviation_percent: 0.16,
          channel_range_percent: 3.13,
          timestamp: new Date().toISOString(),
          confidence_score: 0.65
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSignals();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchSignals();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchSignals, 30000);
    return () => clearInterval(interval);
  }, [selectedCategory, selectedSignal]);

  const getSignalIcon = (signal: string) => {
    switch (signal.toUpperCase()) {
      case 'BUY':
        return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'SELL':
        return <TrendingDown className="h-5 w-5 text-red-500" />;
      case 'HOLD':
        return <Minus className="h-5 w-5 text-yellow-500" />;
      default:
        return <Minus className="h-5 w-5 text-gray-500" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  const filteredSignals = signals.filter(signal => {
    if (selectedSignal !== 'all' && signal.signal !== selectedSignal) return false;
    if (selectedCategory !== 'all') {
      // Simple category filtering based on symbol
      const category = signal.symbol.includes('/') ? 'crypto' : 'stock';
      if (category !== selectedCategory) return false;
    }
    return true;
  });

  const signalSummary = {
    BUY: filteredSignals.filter(s => s.signal === 'BUY').length,
    SELL: filteredSignals.filter(s => s.signal === 'SELL').length,
    HOLD: filteredSignals.filter(s => s.signal === 'HOLD').length,
  };

  return (
    <div className="min-h-screen p-6 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Live Trading Signals
          </h1>
          <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
            Real-time Autonama Channels signals and market analysis
          </p>
        </div>

        {/* Signal Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card glass">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  Buy Signals
                </p>
                <p className="text-2xl font-bold text-green-500">
                  {signalSummary.BUY}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </div>
          
          <div className="card glass">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  Sell Signals
                </p>
                <p className="text-2xl font-bold text-red-500">
                  {signalSummary.SELL}
                </p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-500" />
            </div>
          </div>
          
          <div className="card glass">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  Hold Signals
                </p>
                <p className="text-2xl font-bold text-yellow-500">
                  {signalSummary.HOLD}
                </p>
              </div>
              <Minus className="h-8 w-8 text-yellow-500" />
            </div>
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="card mb-8 glass">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Signal Filters
              </h2>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Filter signals by category and type
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="input-theme w-full"
              >
                <option value="all">All Categories</option>
                <option value="crypto">Cryptocurrency</option>
                <option value="forex">Forex</option>
                <option value="stock">Stocks</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Signal Type
              </label>
              <select
                value={selectedSignal}
                onChange={(e) => setSelectedSignal(e.target.value)}
                className="input-theme w-full"
              >
                <option value="all">All Signals</option>
                <option value="BUY">Buy</option>
                <option value="SELL">Sell</option>
                <option value="HOLD">Hold</option>
              </select>
            </div>
          </div>
        </div>

        {/* Signals List */}
        <div className="card glass">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
              Live Signals
            </h2>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 animate-pulse text-green-500" />
              <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Auto-refreshing
              </span>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner h-8 w-8" />
              <span className="ml-3 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Loading signals...
              </span>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-500" />
              <p className="transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                {error}
              </p>
            </div>
          ) : filteredSignals.length === 0 ? (
            <div className="text-center py-8">
              <Minus className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
              <p className="transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                No signals found for the selected filters
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredSignals.map((signal, index) => (
                <div key={index} className={`card p-6 hover:glass-hover transition-all duration-300 ${getSignalBgColor(signal.signal)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      {getSignalIcon(signal.signal)}
                      <span className={`font-semibold ${getSignalColor(signal.signal)}`}>
                        {signal.signal}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className={`font-semibold ${getConfidenceColor(signal.confidence_score)}`}>
                        {(signal.confidence_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        Confidence
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        Symbol:
                      </span>
                      <span className="font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                        {signal.symbol}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        Current Price:
                      </span>
                      <span className="font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                        {formatPrice(signal.price)}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        Channel Value:
                      </span>
                      <span className="font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                        {formatPrice(signal.channel_value)}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        Deviation:
                      </span>
                      <span className={`font-medium ${signal.deviation_percent >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {formatPercentage(signal.deviation_percent)}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        Channel Range:
                      </span>
                      <span className="font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                        {formatPercentage(signal.channel_range_percent)}
                      </span>
                    </div>

                    <div className="pt-3 border-t" style={{ borderColor: 'var(--glass-border)' }}>
                      <div className="flex justify-between items-center text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                        <span>Upper: {formatPrice(signal.upper_band)}</span>
                        <span>Lower: {formatPrice(signal.lower_band)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                    Updated: {new Date(signal.timestamp).toLocaleTimeString()}
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