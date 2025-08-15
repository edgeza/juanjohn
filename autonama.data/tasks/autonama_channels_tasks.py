"""
Autonama Channels Tasks for TimescaleDB

This module implements Celery tasks for running the Autonama Channels algorithm
with TimescaleDB data integration.
"""

from celery import current_task
from celery_app import celery_app
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import time

from strategies.autonama_channels_core import AutonamaChannelsCore, create_autonama_channels_calculator
from tasks.timescale_data_ingestion import timescale_manager, duckdb_engine

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def calculate_autonama_signals_for_symbol(self, symbol: str, exchange: str = 'binance', 
                                        timeframe: str = '1h', degree: int = 2, kstd: float = 2.0):
    """
    Calculate Autonama Channels signals for a specific symbol.
    
    Args:
        symbol: Symbol to analyze
        exchange: Data exchange source
        timeframe: Data timeframe
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier
    """
    try:
        logger.info(f"Calculating Autonama signals for {symbol}")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'symbol': symbol,
                'status': f'Loading data for {symbol}'
            }
        )
        
        # Load data from TimescaleDB
        data = timescale_manager.get_ohlc_data(symbol, exchange, timeframe, limit=200)
        
        if data.empty:
            logger.warning(f"No data available for {symbol}")
            return {
                'status': 'no_data',
                'symbol': symbol,
                'message': 'No data available'
            }
        
        logger.info(f"Loaded {len(data)} records for {symbol}")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'symbol': symbol,
                'status': f'Calculating channels for {symbol}'
            }
        )
        
        # Create Autonama Channels calculator
        calculator = create_autonama_channels_calculator(degree=degree, kstd=kstd)
        
        # Calculate signals and insights
        result = calculator.compute_signal_and_insights(symbol, data)
        
        if result is None:
            logger.error(f"Failed to calculate signals for {symbol}")
            return {
                'status': 'calculation_failed',
                'symbol': symbol,
                'message': 'Signal calculation failed'
            }
        
        # Store results in TimescaleDB
        success = store_autonama_signals_to_timescale(symbol, result, exchange, timeframe)
        
        if success:
            logger.info(f"Successfully calculated and stored Autonama signals for {symbol}")
            return {
                'status': 'completed',
                'symbol': symbol,
                'signal': result['Signal'],
                'deviation_pct': result['Deviation_Pct'],
                'potential_earnings_pct': result['Potential_Earnings_Pct'],
                'last_price': result['Last_Price'],
                'autonama_channel': result['Autonama_Channel'],
                'autonama_upper': result['Autonama_Upper'],
                'autonama_lower': result['Autonama_Lower']
            }
        else:
            logger.error(f"Failed to store signals for {symbol}")
            return {
                'status': 'storage_failed',
                'symbol': symbol,
                'message': 'Failed to store signals'
            }
        
    except Exception as e:
        logger.error(f"Error calculating Autonama signals for {symbol}: {e}")
        raise


@celery_app.task(bind=True)
def calculate_autonama_signals_batch(self, symbols: List[str], exchange: str = 'binance',
                                   timeframe: str = '1h', degree: int = 2, kstd: float = 2.0):
    """
    Calculate Autonama Channels signals for multiple symbols.
    
    Args:
        symbols: List of symbols to analyze
        exchange: Data exchange source
        timeframe: Data timeframe
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier
    """
    try:
        logger.info(f"Starting batch Autonama signals calculation for {len(symbols)} symbols")
        
        results = []
        success_count = 0
        failed_count = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': len(symbols),
                        'symbol': symbol,
                        'status': f'Processing {symbol} ({i}/{len(symbols)})'
                    }
                )
                
                # Calculate signals for individual symbol
                result = calculate_autonama_signals_for_symbol.apply(
                    args=[symbol, exchange, timeframe, degree, kstd]
                ).get()
                
                if result['status'] == 'completed':
                    success_count += 1
                    logger.info(f"✅ {symbol}: {result['signal']} (deviation: {result['deviation_pct']}%)")
                else:
                    failed_count += 1
                    logger.warning(f"❌ {symbol}: {result.get('message', 'Unknown error')}")
                
                results.append(result)
                
                # Small delay between symbols
                time.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing {symbol}: {e}")
                results.append({
                    'status': 'error',
                    'symbol': symbol,
                    'message': str(e)
                })
        
        logger.info(f"Batch calculation completed: {success_count} success, {failed_count} failed")
        
        return {
            'status': 'completed',
            'total_symbols': len(symbols),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in batch Autonama signals calculation: {e}")
        raise


@celery_app.task(bind=True)
def calculate_autonama_signals_all_assets(self, degree: int = 2, kstd: float = 2.0):
    """
    Calculate Autonama Channels signals for all available assets in TimescaleDB.
    
    Args:
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier
    """
    try:
        logger.info("Starting comprehensive Autonama signals calculation for all assets")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Discovering available symbols'
            }
        )
        
        # Get all available symbols from TimescaleDB
        available_symbols = get_available_symbols_from_timescale()
        
        if not available_symbols:
            logger.warning("No symbols found in TimescaleDB")
            return {
                'status': 'no_symbols',
                'message': 'No symbols found in database'
            }
        
        logger.info(f"Found {len(available_symbols)} symbols in TimescaleDB")
        
        # Group symbols by exchange for batch processing
        symbols_by_exchange = {}
        for symbol_info in available_symbols:
            exchange = symbol_info['exchange']
            if exchange not in symbols_by_exchange:
                symbols_by_exchange[exchange] = []
            symbols_by_exchange[exchange].append(symbol_info['symbol'])
        
        all_results = {}
        total_success = 0
        total_failed = 0
        
        for exchange, symbols in symbols_by_exchange.items():
            logger.info(f"Processing {len(symbols)} symbols from {exchange}")
            
            # Update task progress
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Processing {exchange} symbols',
                    'exchange': exchange,
                    'symbol_count': len(symbols)
                }
            )
            
            # Calculate signals for this exchange
            batch_result = calculate_autonama_signals_batch.apply(
                args=[symbols, exchange, '1h', degree, kstd]
            ).get()
            
            all_results[exchange] = batch_result
            total_success += batch_result['success_count']
            total_failed += batch_result['failed_count']
        
        logger.info(f"All assets calculation completed: {total_success} success, {total_failed} failed")
        
        return {
            'status': 'completed',
            'total_success': total_success,
            'total_failed': total_failed,
            'exchanges_processed': len(symbols_by_exchange),
            'results_by_exchange': all_results
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive Autonama signals calculation: {e}")
        raise


@celery_app.task(bind=True)
def generate_autonama_market_overview(self, degree: int = 2, kstd: float = 2.0):
    """
    Generate a market overview using Autonama Channels signals.
    
    Args:
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier
    """
    try:
        logger.info("Generating Autonama Channels market overview")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'status': 'Loading latest signals'
            }
        )
        
        # Get latest signals from TimescaleDB
        latest_signals = get_latest_autonama_signals_from_timescale()
        
        if not latest_signals:
            logger.warning("No Autonama signals found in database")
            return {
                'status': 'no_signals',
                'message': 'No signals found in database'
            }
        
        # Analyze signals
        buy_signals = [s for s in latest_signals if s['signal'] == 'BUY']
        sell_signals = [s for s in latest_signals if s['signal'] == 'SELL']
        hold_signals = [s for s in latest_signals if s['signal'] == 'HOLD']
        
        # Calculate market statistics
        total_symbols = len(latest_signals)
        buy_count = len(buy_signals)
        sell_count = len(sell_signals)
        hold_count = len(hold_signals)
        
        # Find top opportunities
        top_buy_opportunities = sorted(buy_signals, key=lambda x: x['potential_earnings_pct'], reverse=True)[:5]
        top_sell_opportunities = sorted(sell_signals, key=lambda x: x['potential_earnings_pct'], reverse=True)[:5]
        
        # Calculate average metrics
        avg_deviation = sum(abs(s['deviation_pct']) for s in latest_signals) / total_symbols if total_symbols > 0 else 0
        avg_potential_earnings = sum(s['potential_earnings_pct'] for s in latest_signals) / total_symbols if total_symbols > 0 else 0
        
        # Determine market sentiment
        if buy_count > sell_count * 1.5:
            market_sentiment = "Bullish"
        elif sell_count > buy_count * 1.5:
            market_sentiment = "Bearish"
        else:
            market_sentiment = "Neutral"
        
        overview = {
            'status': 'completed',
            'timestamp': datetime.utcnow(),
            'market_sentiment': market_sentiment,
            'total_symbols': total_symbols,
            'signal_distribution': {
                'buy': buy_count,
                'sell': sell_count,
                'hold': hold_count
            },
            'signal_percentages': {
                'buy_pct': round((buy_count / total_symbols) * 100, 1) if total_symbols > 0 else 0,
                'sell_pct': round((sell_count / total_symbols) * 100, 1) if total_symbols > 0 else 0,
                'hold_pct': round((hold_count / total_symbols) * 100, 1) if total_symbols > 0 else 0
            },
            'market_metrics': {
                'avg_deviation_pct': round(avg_deviation, 2),
                'avg_potential_earnings_pct': round(avg_potential_earnings, 2)
            },
            'top_opportunities': {
                'buy': top_buy_opportunities,
                'sell': top_sell_opportunities
            }
        }
        
        logger.info(f"Market overview generated: {market_sentiment} sentiment, {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD")
        
        return overview
        
    except Exception as e:
        logger.error(f"Error generating market overview: {e}")
        raise


def store_autonama_signals_to_timescale(symbol: str, signals: Dict[str, Any], 
                                      exchange: str, timeframe: str) -> bool:
    """
    Store Autonama Channels signals to TimescaleDB.
    
    Args:
        symbol: Symbol name
        signals: Signal data dictionary
        exchange: Exchange name
        timeframe: Data timeframe
        
    Returns:
        Success status
    """
    try:
        with timescale_manager.engine.connect() as conn:
            # Create autonama_signals table if it doesn't exist
            create_table_query = """
                CREATE TABLE IF NOT EXISTS analytics.autonama_signals (
                    symbol VARCHAR(50) NOT NULL,
                    exchange VARCHAR(50) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    signal VARCHAR(10) NOT NULL,
                    last_price DECIMAL(20,8),
                    autonama_channel DECIMAL(20,8),
                    autonama_upper DECIMAL(20,8),
                    autonama_lower DECIMAL(20,8),
                    deviation_pct DECIMAL(10,4),
                    potential_earnings_pct DECIMAL(10,4),
                    channel_range_pct DECIMAL(10,4),
                    spread_pct DECIMAL(10,4),
                    trend VARCHAR(20),
                    trend_strength DECIMAL(10,4),
                    volatility VARCHAR(20),
                    volatility_value DECIMAL(10,4),
                    market_regime VARCHAR(30),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (symbol, exchange, timeframe, timestamp)
                );
                
                SELECT create_hypertable('analytics.autonama_signals', 'timestamp', 
                                       if_not_exists => TRUE);
            """
            
            conn.execute(create_table_query)
            
            # Insert signal data
            insert_query = """
                INSERT INTO analytics.autonama_signals 
                (symbol, exchange, timeframe, timestamp, signal, last_price, autonama_channel, 
                 autonama_upper, autonama_lower, deviation_pct, potential_earnings_pct, 
                 channel_range_pct, spread_pct, trend, trend_strength, volatility, 
                 volatility_value, market_regime)
                VALUES (%(symbol)s, %(exchange)s, %(timeframe)s, %(timestamp)s, %(signal)s, 
                        %(last_price)s, %(autonama_channel)s, %(autonama_upper)s, %(autonama_lower)s,
                        %(deviation_pct)s, %(potential_earnings_pct)s, %(channel_range_pct)s, 
                        %(spread_pct)s, %(trend)s, %(trend_strength)s, %(volatility)s, 
                        %(volatility_value)s, %(market_regime)s)
                ON CONFLICT (symbol, exchange, timeframe, timestamp) 
                DO UPDATE SET 
                    signal = EXCLUDED.signal,
                    last_price = EXCLUDED.last_price,
                    autonama_channel = EXCLUDED.autonama_channel,
                    autonama_upper = EXCLUDED.autonama_upper,
                    autonama_lower = EXCLUDED.autonama_lower,
                    deviation_pct = EXCLUDED.deviation_pct,
                    potential_earnings_pct = EXCLUDED.potential_earnings_pct,
                    channel_range_pct = EXCLUDED.channel_range_pct,
                    spread_pct = EXCLUDED.spread_pct,
                    trend = EXCLUDED.trend,
                    trend_strength = EXCLUDED.trend_strength,
                    volatility = EXCLUDED.volatility,
                    volatility_value = EXCLUDED.volatility_value,
                    market_regime = EXCLUDED.market_regime,
                    created_at = NOW()
            """
            
            conn.execute(insert_query, {
                'symbol': symbol,
                'exchange': exchange,
                'timeframe': timeframe,
                'timestamp': signals.get('Timestamp', datetime.utcnow()),
                'signal': signals.get('Signal'),
                'last_price': signals.get('Last_Price'),
                'autonama_channel': signals.get('Autonama_Channel'),
                'autonama_upper': signals.get('Autonama_Upper'),
                'autonama_lower': signals.get('Autonama_Lower'),
                'deviation_pct': signals.get('Deviation_Pct'),
                'potential_earnings_pct': signals.get('Potential_Earnings_Pct'),
                'channel_range_pct': signals.get('Channel_Range_Pct'),
                'spread_pct': signals.get('Spread_Pct'),
                'trend': signals.get('Trend'),
                'trend_strength': signals.get('Trend_Strength'),
                'volatility': signals.get('Volatility'),
                'volatility_value': signals.get('Volatility_Value'),
                'market_regime': signals.get('Market_Regime')
            })
            
            conn.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Error storing Autonama signals to TimescaleDB: {e}")
        return False


def get_available_symbols_from_timescale() -> List[Dict[str, str]]:
    """
    Get all available symbols from TimescaleDB.
    
    Returns:
        List of symbol information dictionaries
    """
    try:
        with timescale_manager.engine.connect() as conn:
            query = """
                SELECT DISTINCT symbol, exchange
                FROM trading.ohlc_data
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY symbol, exchange
            """
            
            result = conn.execute(query)
            symbols = [{'symbol': row[0], 'exchange': row[1]} for row in result]
            
        return symbols
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        return []


def get_latest_autonama_signals_from_timescale() -> List[Dict[str, Any]]:
    """
    Get latest Autonama signals from TimescaleDB.
    
    Returns:
        List of latest signal dictionaries
    """
    try:
        with timescale_manager.engine.connect() as conn:
            query = """
                SELECT DISTINCT ON (symbol, exchange) 
                    symbol, exchange, signal, last_price, autonama_channel, autonama_upper, 
                    autonama_lower, deviation_pct, potential_earnings_pct, channel_range_pct,
                    trend, market_regime, timestamp
                FROM analytics.autonama_signals
                ORDER BY symbol, exchange, timestamp DESC
            """
            
            result = conn.execute(query)
            signals = []
            
            for row in result:
                signals.append({
                    'symbol': row[0],
                    'exchange': row[1],
                    'signal': row[2],
                    'last_price': float(row[3]) if row[3] else 0,
                    'autonama_channel': float(row[4]) if row[4] else 0,
                    'autonama_upper': float(row[5]) if row[5] else 0,
                    'autonama_lower': float(row[6]) if row[6] else 0,
                    'deviation_pct': float(row[7]) if row[7] else 0,
                    'potential_earnings_pct': float(row[8]) if row[8] else 0,
                    'channel_range_pct': float(row[9]) if row[9] else 0,
                    'trend': row[10],
                    'market_regime': row[11],
                    'timestamp': row[12]
                })
            
        return signals
        
    except Exception as e:
        logger.error(f"Error getting latest Autonama signals: {e}")
        return []