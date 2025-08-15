# from celery import current_task
# from celery_app import celery_app
# import pandas as pd
# import numpy as np
# import ta
# from typing import List, Dict, Any
# import logging
# from utils.database import db_manager

# logger = logging.getLogger(__name__)

# @celery_app.task(bind=True)
# def calculate_all_indicators(self, symbols: List[str] = None):
#     """Calculate technical indicators for all symbols"""
#     try:
#         if symbols is None:
#             # Get symbols from cache or database
#             symbols = db_manager.get_cached_data('available_symbols')
#             if not symbols:
#                 symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
#         total_symbols = len(symbols)
#         processed = 0
        
#         for symbol in symbols:
#             try:
#                 current_task.update_state(
#                     state='PROGRESS',
#                     meta={'current': processed, 'total': total_symbols, 'symbol': symbol}
#                 )
                
#                 # Calculate indicators for symbol
#                 calculate_symbol_indicators(symbol)
#                 processed += 1
                
#             except Exception as e:
#                 logger.error(f"Error calculating indicators for {symbol}: {str(e)}")
#                 continue
        
#         return {
#             'status': 'completed',
#             'symbols_processed': processed,
#             'total_symbols': total_symbols
#         }
        
#     except Exception as e:
#         logger.error(f"Error in calculate_all_indicators: {str(e)}")
#         raise


# def calculate_symbol_indicators(symbol: str, lookback_days: int = 30):
#     """Calculate technical indicators for a specific symbol"""
#     try:
#         # Load recent market data
#         query = """
#         SELECT timestamp, open, high, low, close, volume
#         FROM market_data
#         WHERE symbol = :symbol
#         AND timestamp >= NOW() - INTERVAL ':days days'
#         ORDER BY timestamp
#         """
        
#         params = {'symbol': symbol, 'days': lookback_days}
#         df = db_manager.execute_postgres_query(query, params)
        
#         if df.empty or len(df) < 20:  # Need minimum data for indicators
#             logger.warning(f"Insufficient data for {symbol}")
#             return
        
#         # Calculate indicators using DuckDB for performance
#         indicators_df = calculate_indicators_duckdb(df, symbol)
        
#         if not indicators_df.empty:
#             # Store indicators in TimescaleDB
#             db_manager.insert_dataframe_to_postgres(
#                 indicators_df, 
#                 'technical_indicators', 
#                 if_exists='append'
#             )
            
#             # Cache latest indicators
#             cache_key = f"indicators:{symbol}:latest"
#             latest_indicators = indicators_df.tail(1).to_dict('records')[0]
#             db_manager.cache_data(cache_key, latest_indicators, expire=600)  # 10 minutes
            
#             logger.info(f"Calculated indicators for {symbol}: {len(indicators_df)} records")
        
#     except Exception as e:
#         logger.error(f"Error calculating indicators for {symbol}: {str(e)}")
#         raise


# def calculate_indicators_duckdb(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
#     """Calculate technical indicators using DuckDB for performance"""
#     try:
#         # Load data into DuckDB
#         duck_conn = db_manager.get_duckdb_connection()
#         duck_conn.register('market_data_temp', df)
        
#         # Calculate indicators using SQL
#         indicators_query = """
#         WITH base_data AS (
#             SELECT 
#                 timestamp,
#                 close,
#                 high,
#                 low,
#                 volume,
#                 -- Simple Moving Averages
#                 AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as sma_10,
#                 AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
#                 AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as sma_50,
                
#                 -- Exponential Moving Averages (approximation)
#                 close as ema_12_base,
#                 close as ema_26_base,
                
#                 -- Bollinger Bands components
#                 AVG(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as bb_middle,
#                 STDDEV(close) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as bb_std,
                
#                 -- RSI components
#                 CASE WHEN close > LAG(close) OVER (ORDER BY timestamp) 
#                      THEN close - LAG(close) OVER (ORDER BY timestamp) 
#                      ELSE 0 END as gain,
#                 CASE WHEN close < LAG(close) OVER (ORDER BY timestamp) 
#                      THEN LAG(close) OVER (ORDER BY timestamp) - close 
#                      ELSE 0 END as loss
#             FROM market_data_temp
#         ),
#         indicators AS (
#             SELECT 
#                 timestamp,
#                 close,
#                 sma_10,
#                 sma_20,
#                 sma_50,
                
#                 -- Bollinger Bands
#                 bb_middle,
#                 bb_middle + (2 * bb_std) as bb_upper,
#                 bb_middle - (2 * bb_std) as bb_lower,
                
#                 -- RSI (simplified calculation)
#                 CASE WHEN AVG(loss) OVER (ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) = 0 
#                      THEN 100
#                      ELSE 100 - (100 / (1 + (
#                          AVG(gain) OVER (ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) /
#                          AVG(loss) OVER (ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
#                      )))
#                 END as rsi_14,
                
#                 -- MACD (simplified)
#                 sma_10 - sma_20 as macd_line,
                
#                 -- Volume indicators
#                 AVG(volume) OVER (ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as volume_sma_20
                
#             FROM base_data
#         )
#         SELECT 
#             timestamp,
#             sma_10,
#             sma_20,
#             sma_50,
#             bb_upper,
#             bb_middle,
#             bb_lower,
#             rsi_14,
#             macd_line,
#             volume_sma_20
#         FROM indicators
#         WHERE timestamp >= (SELECT MAX(timestamp) - INTERVAL '7 days' FROM market_data_temp)
#         ORDER BY timestamp
#         """
        
#         indicators_df = duck_conn.execute(indicators_query).df()
        
#         if not indicators_df.empty:
#             indicators_df['symbol'] = symbol
            
#             # Melt the DataFrame to long format for storage
#             id_vars = ['timestamp', 'symbol']
#             value_vars = [col for col in indicators_df.columns if col not in id_vars]
            
#             melted_df = pd.melt(
#                 indicators_df,
#                 id_vars=id_vars,
#                 value_vars=value_vars,
#                 var_name='indicator_name',
#                 value_name='value'
#             )
            
#             # Remove null values
#             melted_df = melted_df.dropna()
            
#             return melted_df
        
#         return pd.DataFrame()
        
#     except Exception as e:
#         logger.error(f"Error calculating indicators with DuckDB: {str(e)}")
#         return pd.DataFrame()


# @celery_app.task(bind=True)
# def calculate_custom_indicators(self, symbol: str, indicators: List[str], parameters: Dict[str, Any] = None):
#     """Calculate custom technical indicators"""
#     try:
#         current_task.update_state(
#             state='PROGRESS',
#             meta={'status': f'Calculating custom indicators for {symbol}'}
#         )
        
#         # Load market data
#         query = """
#         SELECT timestamp, open, high, low, close, volume
#         FROM market_data
#         WHERE symbol = :symbol
#         AND timestamp >= NOW() - INTERVAL '90 days'
#         ORDER BY timestamp
#         """
        
#         df = db_manager.execute_postgres_query(query, {'symbol': symbol})
        
#         if df.empty:
#             raise ValueError(f"No market data available for {symbol}")
        
#         # Calculate requested indicators
#         results = {}
        
#         for indicator in indicators:
#             try:
#                 if indicator == 'autonama_channels':
#                     results[indicator] = calculate_autonama_channels(df, parameters)
#                 elif indicator == 'custom_rsi':
#                     period = parameters.get('rsi_period', 14) if parameters else 14
#                     results[indicator] = ta.momentum.RSIIndicator(df['close'], window=period).rsi()
#                 elif indicator == 'custom_macd':
#                     fast = parameters.get('macd_fast', 12) if parameters else 12
#                     slow = parameters.get('macd_slow', 26) if parameters else 26
#                     signal = parameters.get('macd_signal', 9) if parameters else 9
#                     macd = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
#                     results[indicator] = {
#                         'macd': macd.macd(),
#                         'signal': macd.macd_signal(),
#                         'histogram': macd.macd_diff()
#                     }
#                 # Add more custom indicators here
                
#             except Exception as e:
#                 logger.error(f"Error calculating {indicator}: {str(e)}")
#                 continue
        
#         return {
#             'symbol': symbol,
#             'indicators': list(results.keys()),
#             'data': results
#         }
        
#     except Exception as e:
#         logger.error(f"Error in calculate_custom_indicators: {str(e)}")
#         raise


# def calculate_autonama_channels(df: pd.DataFrame, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
#     """Calculate Autonama Channels indicator"""
#     try:
#         lookback = parameters.get('lookback_period', 20) if parameters else 20
#         channel_width = parameters.get('channel_width', 0.02) if parameters else 0.02
        
#         # Calculate rolling statistics
#         rolling_high = df['high'].rolling(window=lookback).max()
#         rolling_low = df['low'].rolling(window=lookback).min()
#         rolling_close = df['close'].rolling(window=lookback).mean()
        
#         # Calculate channels
#         upper_channel = rolling_high * (1 + channel_width)
#         lower_channel = rolling_low * (1 - channel_width)
#         middle_channel = (upper_channel + lower_channel) / 2
        
#         # Calculate signals
#         buy_signal = (df['close'] <= lower_channel) & (df['close'].shift(1) > lower_channel.shift(1))
#         sell_signal = (df['close'] >= upper_channel) & (df['close'].shift(1) < upper_channel.shift(1))
        
#         return {
#             'upper_channel': upper_channel.tolist(),
#             'middle_channel': middle_channel.tolist(),
#             'lower_channel': lower_channel.tolist(),
#             'buy_signals': buy_signal.tolist(),
#             'sell_signals': sell_signal.tolist(),
#             'timestamps': df['timestamp'].tolist()
#         }
        
#     except Exception as e:
#         logger.error(f"Error calculating Autonama Channels: {str(e)}")
#         return {}
