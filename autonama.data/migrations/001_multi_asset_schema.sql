-- Multi-Asset Database Schema Migration
-- This script adds support for multiple asset types beyond crypto

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create schemas first
CREATE SCHEMA IF NOT EXISTS migrations;
CREATE SCHEMA IF NOT EXISTS trading;

-- Migration tracking table
CREATE TABLE IF NOT EXISTS migrations.schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT CURRENT_USER
);

-- Asset metadata table for comprehensive asset information
CREATE TABLE IF NOT EXISTS trading.asset_metadata (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('crypto', 'stock', 'forex', 'commodity', 'index', 'etf', 'bond')),
    exchange VARCHAR(50) NOT NULL,
    base_currency VARCHAR(10),
    quote_currency VARCHAR(10),
    description TEXT,
    website VARCHAR(500),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DECIMAL(20, 2),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'delisted', 'suspended')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for asset_metadata
CREATE INDEX IF NOT EXISTS idx_asset_metadata_type ON trading.asset_metadata(asset_type);
CREATE INDEX IF NOT EXISTS idx_asset_metadata_exchange ON trading.asset_metadata(exchange);
CREATE INDEX IF NOT EXISTS idx_asset_metadata_status ON trading.asset_metadata(status);
CREATE INDEX IF NOT EXISTS idx_asset_metadata_updated ON trading.asset_metadata(updated_at);

-- Enhanced OHLC data table with additional fields
CREATE TABLE IF NOT EXISTS trading.ohlc_data_enhanced (
    id BIGSERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open DECIMAL(20, 8) NOT NULL CHECK (open > 0),
    high DECIMAL(20, 8) NOT NULL CHECK (high > 0),
    low DECIMAL(20, 8) NOT NULL CHECK (low > 0),
    close DECIMAL(20, 8) NOT NULL CHECK (close > 0),
    volume DECIMAL(30, 8) NOT NULL CHECK (volume >= 0),
    volume_quote DECIMAL(30, 8),
    trades_count INTEGER,
    vwap DECIMAL(20, 8),
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT ohlc_enhanced_pkey PRIMARY KEY (symbol, timestamp, timeframe),
    CONSTRAINT ohlc_enhanced_price_logic CHECK (high >= open AND high >= close AND high >= low AND low <= open AND low <= close),
    CONSTRAINT ohlc_enhanced_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Note: TimescaleDB hypertable creation removed for standard PostgreSQL compatibility
-- The table will work as a regular PostgreSQL table for time-series data

-- Convert ohlc_data_enhanced to hypertable
SELECT create_hypertable('trading.ohlc_data_enhanced'::regclass, 'timestamp'::name,
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for ohlc_data_enhanced
CREATE INDEX IF NOT EXISTS idx_ohlc_enhanced_symbol_time ON trading.ohlc_data_enhanced(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlc_enhanced_timeframe ON trading.ohlc_data_enhanced(timeframe);
CREATE INDEX IF NOT EXISTS idx_ohlc_enhanced_source ON trading.ohlc_data_enhanced(source);
CREATE INDEX IF NOT EXISTS idx_ohlc_enhanced_volume ON trading.ohlc_data_enhanced(volume DESC);

-- Current prices table for real-time price tracking
CREATE TABLE IF NOT EXISTS trading.current_prices (
    symbol VARCHAR(20) PRIMARY KEY,
    price DECIMAL(20, 8) NOT NULL CHECK (price > 0),
    bid DECIMAL(20, 8),
    ask DECIMAL(20, 8),
    spread DECIMAL(20, 8),
    volume_24h DECIMAL(30, 8),
    change_24h DECIMAL(20, 8),
    change_percent_24h DECIMAL(10, 4),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL,
    
    CONSTRAINT current_prices_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Create indexes for current_prices
CREATE INDEX IF NOT EXISTS idx_current_prices_timestamp ON trading.current_prices(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_current_prices_change ON trading.current_prices(change_percent_24h DESC);
CREATE INDEX IF NOT EXISTS idx_current_prices_volume ON trading.current_prices(volume_24h DESC);

-- Market data table for additional market information
CREATE TABLE IF NOT EXISTS trading.market_data (
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    open_interest DECIMAL(30, 8),
    funding_rate DECIMAL(10, 6),
    next_funding_time TIMESTAMPTZ,
    mark_price DECIMAL(20, 8),
    index_price DECIMAL(20, 8),
    premium_rate DECIMAL(10, 6),
    estimated_settle_price DECIMAL(20, 8),
    source VARCHAR(50) NOT NULL,
    
    CONSTRAINT market_data_pkey PRIMARY KEY (symbol, timestamp),
    CONSTRAINT market_data_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Convert market_data to hypertable
SELECT create_hypertable('trading.market_data'::regclass, 'timestamp'::name,
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Technical indicators table
CREATE TABLE IF NOT EXISTS trading.technical_indicators (
    id BIGSERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    indicator_value JSONB NOT NULL,
    parameters JSONB,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT tech_indicators_pkey PRIMARY KEY (symbol, timestamp, timeframe, indicator_name),
    CONSTRAINT tech_indicators_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Convert technical_indicators to hypertable
SELECT create_hypertable('trading.technical_indicators'::regclass, 'timestamp'::name,
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for technical_indicators
CREATE INDEX IF NOT EXISTS idx_tech_indicators_symbol_name ON trading.technical_indicators(symbol, indicator_name);
CREATE INDEX IF NOT EXISTS idx_tech_indicators_timeframe ON trading.technical_indicators(timeframe);

-- Asset statistics table for pre-calculated statistics
CREATE TABLE IF NOT EXISTS trading.asset_statistics (
    symbol VARCHAR(20) NOT NULL,
    period VARCHAR(10) NOT NULL, -- '24h', '7d', '30d', etc.
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    highest_high DECIMAL(20, 8),
    lowest_low DECIMAL(20, 8),
    period_open DECIMAL(20, 8),
    period_close DECIMAL(20, 8),
    price_change DECIMAL(20, 8),
    price_change_percent DECIMAL(10, 4),
    total_volume DECIMAL(30, 8),
    average_volume DECIMAL(30, 8),
    max_volume DECIMAL(30, 8),
    total_trades INTEGER,
    volatility DECIMAL(10, 6),
    average_range DECIMAL(20, 8),
    max_range DECIMAL(20, 8),
    bullish_candles INTEGER,
    bearish_candles INTEGER,
    doji_candles INTEGER,
    total_candles INTEGER,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT asset_stats_pkey PRIMARY KEY (symbol, period, period_start),
    CONSTRAINT asset_stats_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Create indexes for asset_statistics
CREATE INDEX IF NOT EXISTS idx_asset_stats_symbol_period ON trading.asset_statistics(symbol, period);
CREATE INDEX IF NOT EXISTS idx_asset_stats_calculated ON trading.asset_statistics(calculated_at DESC);

-- Data sources tracking table
CREATE TABLE IF NOT EXISTS trading.data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'api', 'websocket', 'file'
    base_url VARCHAR(500),
    rate_limit_requests INTEGER,
    rate_limit_period INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    last_request TIMESTAMPTZ,
    total_requests BIGINT DEFAULT 0,
    successful_requests BIGINT DEFAULT 0,
    failed_requests BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default data sources
INSERT INTO trading.data_sources (name, type, base_url, rate_limit_requests, rate_limit_period) VALUES
    ('binance', 'api', 'https://api.binance.com', 1200, 60),
    ('twelvedata', 'api', 'https://api.twelvedata.com', 8, 60),
    ('alpha_vantage', 'api', 'https://www.alphavantage.co', 5, 60),
    ('yahoo_finance', 'api', 'https://query1.finance.yahoo.com', 2000, 3600),
    ('ccxt', 'api', NULL, 60, 60)
ON CONFLICT (name) DO NOTHING;

-- Portfolio management tables
CREATE TABLE IF NOT EXISTS trading.portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    base_currency VARCHAR(10) DEFAULT 'USD',
    initial_balance DECIMAL(20, 2) NOT NULL CHECK (initial_balance >= 0),
    current_balance DECIMAL(20, 2) NOT NULL CHECK (current_balance >= 0),
    total_value DECIMAL(20, 2) NOT NULL CHECK (total_value >= 0),
    total_invested DECIMAL(20, 2) DEFAULT 0,
    total_pnl DECIMAL(20, 2) DEFAULT 0,
    total_pnl_percent DECIMAL(10, 4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Positions table
CREATE TABLE IF NOT EXISTS trading.positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(30, 8) NOT NULL CHECK (quantity != 0),
    average_cost DECIMAL(20, 8) NOT NULL CHECK (average_cost > 0),
    current_price DECIMAL(20, 8),
    market_value DECIMAL(20, 2),
    unrealized_pnl DECIMAL(20, 2),
    realized_pnl DECIMAL(20, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'partial')),
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT positions_portfolio_fkey FOREIGN KEY (portfolio_id) REFERENCES trading.portfolios(id) ON DELETE CASCADE,
    CONSTRAINT positions_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Create indexes for positions
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON trading.positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON trading.positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON trading.positions(status);

-- Transactions table
CREATE TABLE IF NOT EXISTS trading.transactions (
    id UUID DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('buy', 'sell', 'deposit', 'withdrawal', 'dividend', 'interest', 'fee', 'transfer_in', 'transfer_out')),
    quantity DECIMAL(30, 8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20, 8) NOT NULL CHECK (price > 0),
    total_amount DECIMAL(20, 2) NOT NULL CHECK (total_amount > 0),
    fee DECIMAL(20, 2) DEFAULT 0 CHECK (fee >= 0),
    timestamp TIMESTAMPTZ NOT NULL,
    order_id UUID,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT transactions_pkey PRIMARY KEY (id, timestamp),
    CONSTRAINT transactions_portfolio_fkey FOREIGN KEY (portfolio_id) REFERENCES trading.portfolios(id) ON DELETE CASCADE,
    CONSTRAINT transactions_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Convert to hypertable
SELECT create_hypertable('trading.transactions'::regclass, 'timestamp'::name,
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Create indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio ON trading.transactions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON trading.transactions(symbol);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON trading.transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON trading.transactions(timestamp DESC);

-- Orders table
CREATE TABLE IF NOT EXISTS trading.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit', 'trailing_stop')),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('buy', 'sell')),
    quantity DECIMAL(30, 8) NOT NULL CHECK (quantity > 0),
    price DECIMAL(20, 8),
    stop_price DECIMAL(20, 8),
    filled_quantity DECIMAL(30, 8) DEFAULT 0 CHECK (filled_quantity >= 0),
    average_fill_price DECIMAL(20, 8),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partially_filled', 'cancelled', 'rejected', 'expired')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    CONSTRAINT orders_portfolio_fkey FOREIGN KEY (portfolio_id) REFERENCES trading.portfolios(id) ON DELETE CASCADE,
    CONSTRAINT orders_symbol_fkey FOREIGN KEY (symbol) REFERENCES trading.asset_metadata(symbol) ON DELETE CASCADE
);

-- Create indexes for orders
CREATE INDEX IF NOT EXISTS idx_orders_portfolio ON trading.orders(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_orders_symbol ON trading.orders(symbol);
CREATE INDEX IF NOT EXISTS idx_orders_status ON trading.orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON trading.orders(created_at DESC);

-- Create continuous aggregates for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS trading.hourly_ohlc
WITH (timescaledb.continuous) AS
SELECT 
    symbol,
    time_bucket('1 hour', timestamp) AS hour,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume,
    count(*) AS trades_count,
    avg(close) AS avg_price
FROM trading.ohlc_data_enhanced
WHERE timeframe = '1m'
GROUP BY symbol, hour
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('trading.hourly_ohlc',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Data retention policies
SELECT add_retention_policy('trading.ohlc_data_enhanced', INTERVAL '2 years', if_not_exists => TRUE);
SELECT add_retention_policy('trading.market_data', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('trading.technical_indicators', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('trading.transactions', INTERVAL '7 years', if_not_exists => TRUE);

-- Insert sample asset metadata
INSERT INTO trading.asset_metadata (symbol, name, asset_type, exchange, base_currency, quote_currency) VALUES
    ('BTC/USDT', 'Bitcoin / Tether USD', 'crypto', 'binance', 'BTC', 'USDT'),
    ('ETH/USDT', 'Ethereum / Tether USD', 'crypto', 'binance', 'ETH', 'USDT'),
    ('ADA/USDT', 'Cardano / Tether USD', 'crypto', 'binance', 'ADA', 'USDT'),
    ('BNB/USDT', 'Binance Coin / Tether USD', 'crypto', 'binance', 'BNB', 'USDT'),
    ('SOL/USDT', 'Solana / Tether USD', 'crypto', 'binance', 'SOL', 'USDT'),
    ('AAPL', 'Apple Inc.', 'stock', 'nasdaq', 'USD', NULL),
    ('GOOGL', 'Alphabet Inc.', 'stock', 'nasdaq', 'USD', NULL),
    ('MSFT', 'Microsoft Corporation', 'stock', 'nasdaq', 'USD', NULL),
    ('TSLA', 'Tesla Inc.', 'stock', 'nasdaq', 'USD', NULL),
    ('EUR/USD', 'Euro / US Dollar', 'forex', 'forex', 'EUR', 'USD'),
    ('GBP/USD', 'British Pound / US Dollar', 'forex', 'forex', 'GBP', 'USD'),
    ('USD/JPY', 'US Dollar / Japanese Yen', 'forex', 'forex', 'USD', 'JPY')
ON CONFLICT (symbol) DO UPDATE SET
    name = EXCLUDED.name,
    asset_type = EXCLUDED.asset_type,
    exchange = EXCLUDED.exchange,
    updated_at = NOW();

-- Record migration
INSERT INTO migrations.schema_migrations (version, description) VALUES
    ('001', 'Multi-asset database schema with enhanced OHLC, portfolio management, and technical indicators')
ON CONFLICT (version) DO NOTHING;

-- Grant permissions (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA trading TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA trading TO postgres;

COMMIT;
