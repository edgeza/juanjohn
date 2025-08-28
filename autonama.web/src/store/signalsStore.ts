/**
 * Signals Store - Zustand
 * 
 * Manages live signals, WebSocket connections, and signal-related operations
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import apiClient from '@/lib/apiClient';
import toast from 'react-hot-toast';

// Types
export interface Signal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  price: number;
  channel_value: number;
  upper_band: number;
  lower_band: number;
  deviation_percent: number;
  channel_range_percent: number;
  timestamp: string;
  confidence_score: number;
}

export interface MarketOverview {
  signals_summary: Record<string, { count: number; avg_confidence: number }>;
  top_performers: Array<{
    symbol: string;
    current_price: number;
    change_percent_24h: number;
  }>;
  market_stats: {
    total_assets: number;
    total_data_points: number;
    last_update: string;
  };
  timestamp: string;
}

interface WebSocketState {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastMessage: any;
  reconnectAttempts: number;
}

interface SignalsState {
  // Data
  signals: Signal[];
  marketOverview: MarketOverview | null;
  realtimeSignals: Signal[];
  
  // Loading states
  isLoading: boolean;
  isLoadingOverview: boolean;
  
  // Error states
  error: string | null;
  overviewError: string | null;
  
  // Filters
  selectedCategory: string;
  selectedSignal: string;
  autoRefresh: boolean;
  
  // WebSocket state
  websocket: WebSocketState;
  
  // Actions
  fetchSignals: (category?: string, signalType?: string, limit?: number) => Promise<void>;
  fetchMarketOverview: () => Promise<void>;
  setSelectedCategory: (category: string) => void;
  setSelectedSignal: (signal: string) => void;
  setAutoRefresh: (enabled: boolean) => void;
  
  // WebSocket actions
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  updateWebSocketState: (state: Partial<WebSocketState>) => void;
  handleWebSocketMessage: (message: any) => void;
  
  // Computed
  filteredSignals: () => Signal[];
  signalsSummary: () => Record<string, number>;
  
  // Cleanup
  clearError: () => void;
}

// WebSocket connection
let websocketConnection: WebSocket | null = null;

export const useSignalsStore = create<SignalsState>()(
  devtools(
    (set, get) => ({
      // Initial state
      signals: [],
      marketOverview: null,
      realtimeSignals: [],
      isLoading: false,
      isLoadingOverview: false,
      error: null,
      overviewError: null,
      selectedCategory: 'all',
      selectedSignal: 'all',
      autoRefresh: true,
      websocket: {
        isConnected: false,
        connectionStatus: 'disconnected',
        lastMessage: null,
        reconnectAttempts: 0,
      },

      // Actions
      fetchSignals: async (category?: string, signalType?: string, limit = 50) => {
        set({ isLoading: true, error: null });
        
        try {
          const params = new URLSearchParams();
          if (category && category !== 'all') params.append('category', category);
          if (signalType && signalType !== 'all') params.append('signal_type', signalType);
          params.append('limit', limit.toString());
          
          const signals = await apiClient.get<Signal[]>(
            `/v1/data/signals?${params}`
          );
          
          set({ signals, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.message || 'Failed to fetch signals', 
            isLoading: false 
          });
          toast.error('Failed to load signals');
        }
      },

      fetchMarketOverview: async () => {
        set({ isLoadingOverview: true, overviewError: null });
        
        try {
          const overview = await apiClient.get<MarketOverview>(
            '/v1/data/market-overview'
          );
          set({ marketOverview: overview, isLoadingOverview: false });
        } catch (error: any) {
          set({ 
            overviewError: error.message || 'Failed to fetch market overview', 
            isLoadingOverview: false 
          });
        }
      },

      setSelectedCategory: (selectedCategory: string) => {
        set({ selectedCategory });
        // Refetch signals with new filter
        get().fetchSignals(selectedCategory, get().selectedSignal);
      },

      setSelectedSignal: (selectedSignal: string) => {
        set({ selectedSignal });
        // Refetch signals with new filter
        get().fetchSignals(get().selectedCategory, selectedSignal);
      },

      setAutoRefresh: (autoRefresh: boolean) => {
        set({ autoRefresh });
      },

      // WebSocket actions
      connectWebSocket: () => {
        const wsUrl = apiClient.getWebSocketUrl('/v1/ws/signals');
        
        try {
          set(state => ({
            websocket: { ...state.websocket, connectionStatus: 'connecting' }
          }));
          
          websocketConnection = new WebSocket(wsUrl);
          
          websocketConnection.onopen = () => {
            console.log('🔌 Signals WebSocket connected');
            set(state => ({
              websocket: {
                ...state.websocket,
                isConnected: true,
                connectionStatus: 'connected',
                reconnectAttempts: 0,
              }
            }));
            toast.success('Live signals connected');
          };
          
          websocketConnection.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);
              get().handleWebSocketMessage(message);
            } catch (error) {
              console.error('Failed to parse WebSocket message:', error);
            }
          };
          
          websocketConnection.onclose = () => {
            console.log('🔌 Signals WebSocket disconnected');
            set(state => ({
              websocket: {
                ...state.websocket,
                isConnected: false,
                connectionStatus: 'disconnected',
              }
            }));
            
            // Auto-reconnect logic
            const { reconnectAttempts } = get().websocket;
            if (reconnectAttempts < 5) {
              setTimeout(() => {
                set(state => ({
                  websocket: {
                    ...state.websocket,
                    reconnectAttempts: reconnectAttempts + 1,
                  }
                }));
                get().connectWebSocket();
              }, Math.pow(2, reconnectAttempts) * 1000); // Exponential backoff
            }
          };
          
          websocketConnection.onerror = (error) => {
            console.error('🔌 Signals WebSocket error:', error);
            set(state => ({
              websocket: { ...state.websocket, connectionStatus: 'error' }
            }));
          };
          
        } catch (error) {
          console.error('Failed to connect WebSocket:', error);
          set(state => ({
            websocket: { ...state.websocket, connectionStatus: 'error' }
          }));
        }
      },

      disconnectWebSocket: () => {
        if (websocketConnection) {
          websocketConnection.close();
          websocketConnection = null;
        }
        set(state => ({
          websocket: {
            ...state.websocket,
            isConnected: false,
            connectionStatus: 'disconnected',
          }
        }));
      },

      updateWebSocketState: (newState: Partial<WebSocketState>) => {
        set(state => ({
          websocket: { ...state.websocket, ...newState }
        }));
      },

      handleWebSocketMessage: (message: any) => {
        set(state => ({
          websocket: { ...state.websocket, lastMessage: message }
        }));
        
        if (message.type === 'initial_signals' || message.type === 'signals_update') {
          set({ realtimeSignals: message.data });
        } else if (message.type === 'test_message') {
          console.log('✅ WebSocket test message received:', message.data);
          // Don't update realtimeSignals for test messages
        }
      },

      // Computed
      filteredSignals: () => {
        const { signals, realtimeSignals, selectedCategory, selectedSignal } = get();
        const displaySignals = realtimeSignals.length > 0 ? realtimeSignals : signals;
        
        return displaySignals.filter(signal => {
          const matchesCategory = selectedCategory === 'all' || signal.symbol.includes(selectedCategory.toUpperCase());
          const matchesSignal = selectedSignal === 'all' || signal.signal === selectedSignal;
          return matchesCategory && matchesSignal;
        });
      },

      signalsSummary: () => {
        const signals = get().filteredSignals();
        return signals.reduce((acc: Record<string, number>, signal) => {
          acc[signal.signal] = (acc[signal.signal] || 0) + 1;
          return acc;
        }, {});
      },

      clearError: () => {
        set({ error: null, overviewError: null });
      },
    }),
    {
      name: 'signals-store',
    }
  )
);