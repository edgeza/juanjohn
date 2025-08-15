'use client';

import { useState, useCallback } from 'react';
import { getPublicApiBase } from '@/lib/runtimeEnv';
import { AssetType } from '@/types/multi-asset';
import type { 
  AssetInfo, 
  OHLCData, 
  TechnicalIndicators,
  CorrelationAnalysis,
  PortfolioAnalysis,
  TaskResponse
} from '@/types/multi-asset';

interface MultiAssetDataState {
  assets: {
    crypto: AssetInfo[];
    stocks: AssetInfo[];
    forex: AssetInfo[];
    commodities: AssetInfo[];
  };
  ohlcData: Record<string, OHLCData[]>;
  indicators: Record<string, TechnicalIndicators>;
  correlations: CorrelationAnalysis | null;
  portfolioAnalysis: PortfolioAnalysis | null;
  loading: {
    assets: boolean;
    ohlc: boolean;
    indicators: boolean;
    analytics: boolean;
  };
  error: {
    assets: string | null;
    ohlc: string | null;
    indicators: string | null;
    analytics: string | null;
  };
}

const initialState: MultiAssetDataState = {
  assets: {
    crypto: [],
    stocks: [],
    forex: [],
    commodities: []
  },
  ohlcData: {},
  indicators: {},
  correlations: null,
  portfolioAnalysis: null,
  loading: {
    assets: false,
    ohlc: false,
    indicators: false,
    analytics: false
  },
  error: {
    assets: null,
    ohlc: null,
    indicators: null,
    analytics: null
  }
};

export const useMultiAssetData = () => {
  const [state, setState] = useState<MultiAssetDataState>(initialState);

  // Helper function to update state
  const updateState = useCallback((updates: Partial<MultiAssetDataState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Helper function to update loading state
  const setLoading = useCallback((key: keyof MultiAssetDataState['loading'], value: boolean) => {
    setState(prev => ({
      ...prev,
      loading: { ...prev.loading, [key]: value }
    }));
  }, []);

  // Helper function to update error state
  const setError = useCallback((key: keyof MultiAssetDataState['error'], value: string | null) => {
    setState(prev => ({
      ...prev,
      error: { ...prev.error, [key]: value }
    }));
  }, []);

  // API base URL
  const API_BASE = getPublicApiBase();

  // Fetch assets by type
  const fetchAssets = useCallback(async (assetType: AssetType, limit = 50, offset = 0) => {
    setLoading('assets', true);
    setError('assets', null);

    try {
      const endpoint = `${API_BASE}/v1/multi-asset/assets/${assetType}?limit=${limit}&offset=${offset}`;
      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch ${assetType} assets: ${response.statusText}`);
      }

      const assets: AssetInfo[] = await response.json();
      
      updateState({
        assets: {
          ...state.assets,
          [assetType]: assets
        }
      });

      return assets;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError('assets', errorMessage);
      throw error;
    } finally {
      setLoading('assets', false);
    }
  }, [state.assets]);

  // Fetch all assets
  const fetchAllAssets = useCallback(async () => {
    setLoading('assets', true);
    setError('assets', null);

    try {
      const response = await fetch(`${API_BASE}/v1/multi-asset/assets/all`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch all assets: ${response.statusText}`);
      }

      const allAssets: AssetInfo[] = await response.json();
      
      // Group assets by type
      const groupedAssets = allAssets.reduce((acc, asset) => {
        const type = asset.asset_type;
        if (!acc[type]) acc[type] = [];
        acc[type].push(asset);
        return acc;
      }, {} as Record<AssetType, AssetInfo[]>);

      updateState({
        assets: {
          crypto: groupedAssets[AssetType.CRYPTO] || [],
          stocks: groupedAssets[AssetType.STOCK] || [],
          forex: groupedAssets[AssetType.FOREX] || [],
          commodities: groupedAssets[AssetType.COMMODITY] || []
        }
      });

      return allAssets;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError('assets', errorMessage);
      throw error;
    } finally {
      setLoading('assets', false);
    }
  }, []);

  // Fetch OHLC data for a symbol
  const fetchOHLCData = useCallback(async (
    symbol: string, 
    startDate?: string, 
    endDate?: string, 
    limit = 1000
  ) => {
    setLoading('ohlc', true);
    setError('ohlc', null);

    try {
      let endpoint = `${API_BASE}/v1/multi-asset/ohlc/${symbol}?limit=${limit}`;
      
      if (startDate) endpoint += `&start_date=${startDate}`;
      if (endDate) endpoint += `&end_date=${endDate}`;

      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch OHLC data for ${symbol}: ${response.statusText}`);
      }

      const ohlcData: OHLCData[] = await response.json();
      
      updateState({
        ohlcData: {
          ...state.ohlcData,
          [symbol]: ohlcData
        }
      });

      return ohlcData;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError('ohlc', errorMessage);
      throw error;
    } finally {
      setLoading('ohlc', false);
    }
  }, [state.ohlcData]);

  // Fetch technical indicators
  const fetchIndicators = useCallback(async (
    symbol: string,
    indicators: string[],
    timeframe = '1h',
    lookbackDays = 30
  ) => {
    setLoading('indicators', true);
    setError('indicators', null);

    try {
      const response = await fetch(`${API_BASE}/v1/multi-asset/indicators/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          indicators,
          timeframe,
          lookback_days: lookbackDays
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to calculate indicators for ${symbol}: ${response.statusText}`);
      }

      const taskResponse: TaskResponse = await response.json();
      
      // Poll for results
      const result = await pollTaskResult(taskResponse.task_id);
      
      if (result.success && result.indicators) {
        updateState({
          indicators: {
            ...state.indicators,
            [symbol]: result.indicators
          }
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError('indicators', errorMessage);
      throw error;
    } finally {
      setLoading('indicators', false);
    }
  }, [state.indicators]);

  // Calculate correlation matrix
  const calculateCorrelation = useCallback(async (
    symbols: string[],
    lookbackDays = 30,
    method = 'pearson'
  ) => {
    setLoading('analytics', true);
    setError('analytics', null);

    try {
      const response = await fetch(`${API_BASE}/v1/multi-asset/analytics/correlation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbols,
          lookback_days: lookbackDays,
          method
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to calculate correlation: ${response.statusText}`);
      }

      const taskResponse: TaskResponse = await response.json();
      
      // Poll for results
      const result = await pollTaskResult(taskResponse.task_id);
      
      if (result.success) {
        updateState({
          correlations: result
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError('analytics', errorMessage);
      throw error;
    } finally {
      setLoading('analytics', false);
    }
  }, []);

  // Analyze portfolio
  const analyzePortfolio = useCallback(async (
    portfolio: Record<string, number>,
    lookbackDays = 30
  ) => {
    setLoading('analytics', true);
    setError('analytics', null);

    try {
      const response = await fetch(`${API_BASE}/v1/multi-asset/analytics/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          portfolio,
          lookback_days: lookbackDays
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to analyze portfolio: ${response.statusText}`);
      }

      const taskResponse: TaskResponse = await response.json();
      
      // Poll for results
      const result = await pollTaskResult(taskResponse.task_id);
      
      if (result.success) {
        updateState({
          portfolioAnalysis: result
        });
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError('analytics', errorMessage);
      throw error;
    } finally {
      setLoading('analytics', false);
    }
  }, []);

  // Trigger data ingestion
  const triggerDataIngestion = useCallback(async (assetType: AssetType, symbols?: string[]) => {
    try {
      let endpoint = `${API_BASE}/v1/multi-asset/ingestion/`;
      
      switch (assetType) {
        case AssetType.CRYPTO:
          endpoint += 'crypto';
          break;
        case AssetType.STOCK:
          endpoint += 'stocks';
          break;
        case AssetType.FOREX:
          endpoint += 'forex';
          break;
        case AssetType.COMMODITY:
          endpoint += 'commodities';
          break;
      }

      const body = symbols ? { symbols } : {};
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger ${assetType} ingestion: ${response.statusText}`);
      }

      const taskResponse: TaskResponse = await response.json();
      return taskResponse;
    } catch (error) {
      console.error('Data ingestion error:', error);
      throw error;
    }
  }, []);

  // Trigger all asset types ingestion
  const triggerAllIngestion = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/v1/multi-asset/ingestion/all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger all asset ingestion: ${response.statusText}`);
      }

      const taskResponse: TaskResponse = await response.json();
      return taskResponse;
    } catch (error) {
      console.error('All asset ingestion error:', error);
      throw error;
    }
  }, []);

  // Poll task result
  const pollTaskResult = useCallback(async (taskId: string, maxAttempts = 30, interval = 2000) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await fetch(`${API_BASE}/v1/multi-asset/analytics/status/${taskId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to get task status: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.status === 'completed') {
          return result.result;
        } else if (result.status === 'failed') {
          throw new Error(result.error || 'Task failed');
        }
        
        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, interval));
      } catch (error) {
        if (attempt === maxAttempts - 1) {
          throw error;
        }
      }
    }
    
    throw new Error('Task polling timeout');
  }, []);

  // Get task status
  const getTaskStatus = useCallback(async (taskId: string) => {
    try {
      const response = await fetch(`${API_BASE}/v1/multi-asset/ingestion/status/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get task status: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Task status error:', error);
      throw error;
    }
  }, []);

  return {
    // State
    assets: state.assets,
    ohlcData: state.ohlcData,
    indicators: state.indicators,
    correlations: state.correlations,
    portfolioAnalysis: state.portfolioAnalysis,
    loading: state.loading,
    error: state.error,

    // Actions
    fetchAssets,
    fetchAllAssets,
    fetchOHLCData,
    fetchIndicators,
    calculateCorrelation,
    analyzePortfolio,
    triggerDataIngestion,
    triggerAllIngestion,
    getTaskStatus,
    
    // Utilities
    pollTaskResult
  };
};
