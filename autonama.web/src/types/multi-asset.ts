/**
 * Multi-Asset Type Definitions
 * 
 * TypeScript interfaces and types for the multi-asset trading system
 */

// Asset Types
export enum AssetType {
  CRYPTO = 'crypto',
  STOCK = 'stock',
  FOREX = 'forex',
  COMMODITY = 'commodity'
}

export enum Exchange {
  BINANCE = 'binance',
  NASDAQ = 'nasdaq',
  NYSE = 'nyse',
  FOREX = 'forex',
  COMMODITY = 'commodity'
}

// Asset Information Interface
export interface AssetInfo {
  symbol: string;
  name?: string;
  asset_type: AssetType;
  exchange: Exchange;
  base_currency?: string;
  quote_currency?: string;
  current_price?: number;
  price_change_24h?: number;
  volume_24h?: number;
  last_updated?: string;
}

// OHLC Data Interface
export interface OHLCData {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Technical Indicators
export interface RSIIndicator {
  values: number[];
  current: number;
  overbought_level: number;
  oversold_level: number;
  signal: 'overbought' | 'oversold' | 'neutral';
}

export interface MACDIndicator {
  macd_line: number[];
  signal_line: number[];
  histogram: number[];
  current_macd: number;
  current_signal: number;
  signal: 'bullish' | 'bearish';
}

export interface BollingerBands {
  upper_band: number[];
  middle_band: number[];
  lower_band: number[];
  current_price: number;
  bandwidth: number;
  signal: 'overbought' | 'oversold' | 'neutral';
}

export interface MovingAverage {
  values: number[];
  current: number;
}

export interface VolumeProfile {
  profile: Array<{
    price_low: number;
    price_high: number;
    volume: number;
  }>;
  poc: {
    price_low: number;
    price_high: number;
    volume: number;
  };
}

export interface TechnicalIndicators {
  rsi?: RSIIndicator;
  macd?: MACDIndicator;
  bollinger_bands?: BollingerBands;
  sma?: Record<string, MovingAverage>;
  ema?: Record<string, MovingAverage>;
  volume_profile?: VolumeProfile;
}

// Analytics Interfaces
export interface CorrelationMatrix {
  [symbol: string]: {
    [symbol: string]: number | null;
  };
}

export interface CorrelationAnalysis {
  correlation_matrix: CorrelationMatrix;
  statistics: {
    average_correlation: number;
    max_correlation: number;
    min_correlation: number;
    data_points: number;
  };
}

export interface PortfolioMetrics {
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  data_points: number;
}

export interface PortfolioAnalysis {
  portfolio: Record<string, number>;
  metrics: PortfolioMetrics;
  daily_returns: number[];
}

// API Request/Response Types
export interface IndicatorRequest {
  symbol: string;
  indicators: string[];
  timeframe?: string;
  lookback_days?: number;
}

export interface CorrelationRequest {
  symbols: string[];
  lookback_days?: number;
  method?: 'pearson' | 'spearman' | 'kendall';
}

export interface PortfolioRequest {
  portfolio: Record<string, number>;
  lookback_days?: number;
}

export interface TaskResponse {
  task_id: string;
  status: 'started' | 'pending' | 'completed' | 'failed';
  result?: any;
  error?: string;
  message?: string;
}

export interface IngestionResponse extends TaskResponse {
  asset_type?: string;
  symbols?: string[];
  pairs?: string[];
}

// Asset Configuration
export interface AssetConfig {
  symbol: string;
  asset_type: AssetType;
  exchange: Exchange;
  priority?: number;
  enabled?: boolean;
}

// Market Data Interfaces
export interface MarketSummary {
  total_assets: number;
  asset_breakdown: Record<AssetType, number>;
  total_market_cap?: number;
  total_volume_24h?: number;
  top_gainers: AssetInfo[];
  top_losers: AssetInfo[];
  most_active: AssetInfo[];
}

export interface PriceAlert {
  id: string;
  symbol: string;
  asset_type: AssetType;
  condition: 'above' | 'below';
  target_price: number;
  current_price: number;
  created_at: string;
  triggered_at?: string;
  active: boolean;
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
  volume?: number;
}

export interface CandlestickData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartConfig {
  symbol: string;
  timeframe: string;
  indicators: string[];
  chart_type: 'candlestick' | 'line' | 'area';
  show_volume: boolean;
}

// Portfolio Types
export interface PortfolioPosition {
  symbol: string;
  asset_type: AssetType;
  quantity: number;
  average_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  weight: number;
}

export interface Portfolio {
  id: string;
  name: string;
  description?: string;
  positions: PortfolioPosition[];
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  created_at: string;
  updated_at: string;
}

// Watchlist Types
export interface WatchlistItem {
  symbol: string;
  asset_type: AssetType;
  added_at: string;
  notes?: string;
}

export interface Watchlist {
  id: string;
  name: string;
  items: WatchlistItem[];
  created_at: string;
  updated_at: string;
}

// Filter and Search Types
export interface AssetFilter {
  asset_types?: AssetType[];
  exchanges?: Exchange[];
  min_price?: number;
  max_price?: number;
  min_volume?: number;
  max_volume?: number;
  search_term?: string;
}

export interface SortConfig {
  field: keyof AssetInfo;
  direction: 'asc' | 'desc';
}

// API Response Wrappers
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'price_update' | 'indicator_update' | 'alert' | 'system';
  data: any;
  timestamp: string;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

// Component Props Types
export interface AssetListProps {
  assets: AssetInfo[];
  loading?: boolean;
  error?: string;
  onAssetSelect?: (asset: AssetInfo) => void;
  filter?: AssetFilter;
  sort?: SortConfig;
}

export interface ChartProps {
  symbol: string;
  data: CandlestickData[];
  indicators?: TechnicalIndicators;
  config?: ChartConfig;
  height?: number;
  loading?: boolean;
}

export interface PortfolioProps {
  portfolio: Portfolio;
  onPositionUpdate?: (position: PortfolioPosition) => void;
  onPortfolioUpdate?: (portfolio: Portfolio) => void;
}

// State Management Types
export interface MultiAssetState {
  assets: {
    crypto: AssetInfo[];
    stocks: AssetInfo[];
    forex: AssetInfo[];
    commodities: AssetInfo[];
  };
  selectedAsset: AssetInfo | null;
  ohlcData: Record<string, OHLCData[]>;
  indicators: Record<string, TechnicalIndicators>;
  correlations: CorrelationAnalysis | null;
  portfolios: Portfolio[];
  watchlists: Watchlist[];
  alerts: PriceAlert[];
  loading: {
    assets: boolean;
    ohlc: boolean;
    indicators: boolean;
    analytics: boolean;
  };
  errors: {
    assets: string | null;
    ohlc: string | null;
    indicators: string | null;
    analytics: string | null;
  };
}

// Action Types for Redux
export interface AssetAction {
  type: string;
  payload?: any;
}

// Utility Types
export type AssetSymbol = string;
export type Timestamp = string;
export type Price = number;
export type Volume = number;
export type Percentage = number;
