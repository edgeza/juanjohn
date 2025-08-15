import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from binance.client import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from datetime import datetime, timedelta
import sys
import os
import logging

# Suppress warnings and reduce logging noise
warnings.filterwarnings('ignore')
logging.getLogger('tornado').setLevel(logging.ERROR)

# Add the parent directory to the path to import the data handler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_data_handler import CryptoDataHandler

def show_page():
    # --- Binance API ---
    client = Client()
    
    # Initialize crypto data handler
    db_handler = CryptoDataHandler("data/crypto_data.duckdb")
    
    @st.cache_data(ttl=3600) # Cache for 1 hour
    def get_top_100_coins():
        """Get top 100 USDT pairs from Binance by volume."""
        try:
            # Get 24hr ticker for all symbols
            tickers = client.get_ticker()
            
            # Filter for USDT pairs
            usdt_pairs = []
            for ticker in tickers:
                if ticker['symbol'].endswith('USDT') and ticker['symbol'] != 'USDTUSDT':
                    volume_usd = float(ticker['quoteVolume'])
                    usdt_pairs.append({
                        'symbol': ticker['symbol'],
                        'volume': volume_usd,
                        'price': float(ticker['lastPrice'])
                    })
            
            # Sort by volume and return exactly top 100
            usdt_pairs.sort(key=lambda x: x['volume'], reverse=True)
            top_100 = [pair['symbol'] for pair in usdt_pairs[:100]]
            
            # Ensure we always return exactly 100 coins
            if len(top_100) < 100:
                st.warning(f"Only found {len(top_100)} USDT pairs. This may be due to API limitations.")
            
            return top_100
            
        except Exception as e:
            st.error(f"Error fetching top 100 coins: {e}")
            # Return core movers as fallback
            return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'AVAXUSDT', 'MATICUSDT']

    def get_klines_from_db(symbol, interval, lookback_candles=500, force_update=False):
        """Fetch historical klines data from DuckDB with smart bulk download and incremental updates."""
        try:
            # Convert interval format (e.g., '15m' -> '15M')
            interval_upper = interval.upper()
            
            # Calculate date range based on timeframe and number of candles
            end_date = datetime.now()
            
            # Calculate minutes per candle based on interval
            interval_minutes = {
                '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
                '1d': 1440, '3d': 4320, '1w': 10080
            }
            
            minutes_per_candle = interval_minutes.get(interval.lower(), 60)  # Default to 1h
            total_minutes = lookback_candles * minutes_per_candle
            start_date = end_date - timedelta(minutes=total_minutes)
            
            # Check if we have data in DuckDB
            latest_timestamp = db_handler.get_latest_timestamp(symbol, interval_upper)
            earliest_timestamp = db_handler.get_earliest_timestamp(symbol, interval_upper)
            
            # Determine minimum data requirements based on candles
            is_major = symbol in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
            min_candles = 2000 if is_major else 1000  # More candles for majors
            
            # For core movers, always ensure we have data
            core_movers = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
            is_core_mover = symbol in core_movers
            
            # Check if we need bulk download (no data or insufficient data)
            need_bulk_download = (
                latest_timestamp is None or 
                earliest_timestamp is None or
                (end_date - earliest_timestamp).days < (min_candles * minutes_per_candle / 1440)  # Convert to days
            )
            
            # Check if we need incremental update (data is old)
            need_incremental_update = (
                latest_timestamp is None or 
                latest_timestamp < (end_date - timedelta(hours=1))
            )
            
            # For core movers, force download if no data exists
            if is_core_mover and (latest_timestamp is None or earliest_timestamp is None):
                need_bulk_download = True
            
            if need_bulk_download:
                # Bulk download - get maximum available data
                bulk_start_date = end_date - timedelta(minutes=min_candles * minutes_per_candle * 2)  # Try to get 2x minimum
                
                st.info(f"Bulk downloading {symbol} {interval} data (this may take a moment)...")
                
                klines = client.get_historical_klines(
                    symbol=symbol, 
                    interval=interval, 
                    start_str=bulk_start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    end_str=end_date.strftime('%Y-%m-%d %H:%M:%S')
                )
                
                if klines:
                    # Convert to DataFrame
                    df = pd.DataFrame(klines, columns=[
                        "timestamp", "open", "high", "low", "close", "volume", "close_time",
                        "quote_asset_volume", "number_of_trades", "taker_buy_base",
                        "taker_buy_quote", "ignore"
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                    
                    # Rename index to match database expectations
                    df.index.name = 'DateTime'
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })
                    
                    # Store in DuckDB
                    db_handler.insert_data(symbol, interval_upper, df)
                    
                    st.success(f"Downloaded {len(df)} bars for {symbol} {interval}")
                    
                    # Return data for requested range
                    df_filtered = df.loc[start_date:end_date]
                    df_return = df_filtered.copy()
                    df_return.index.name = 'timestamp'
                    df_return = df_return.rename(columns={
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    return df_return
                else:
                    return pd.DataFrame()
                    
            elif need_incremental_update:
                # Incremental update - only get new data since last update
                update_start = latest_timestamp + timedelta(minutes=1) if latest_timestamp else end_date - timedelta(days=1)
                
                klines = client.get_historical_klines(
                    symbol=symbol, 
                    interval=interval, 
                    start_str=update_start.strftime('%Y-%m-%d %H:%M:%S'),
                    end_str=end_date.strftime('%Y-%m-%d %H:%M:%S')
                )
                
                if klines:
                    # Convert to DataFrame
                    df = pd.DataFrame(klines, columns=[
                        "timestamp", "open", "high", "low", "close", "volume", "close_time",
                        "quote_asset_volume", "number_of_trades", "taker_buy_base",
                        "taker_buy_quote", "ignore"
                    ])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                    
                    # Rename index to match database expectations
                    df.index.name = 'DateTime'
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })
                    
                    # Store in DuckDB
                    db_handler.insert_data(symbol, interval_upper, df)
                    
                    st.success(f"Updated {len(df)} new bars for {symbol} {interval}")
                
            # Get data from DuckDB (whether we updated or not)
            df = db_handler.get_data(symbol, interval_upper, start_date, end_date)
            if not df.empty:
                # Rename columns to match expected format
                df = df.rename(columns={
                    'datetime': 'timestamp',
                    'open': 'open',
                    'high': 'high', 
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                df.set_index('timestamp', inplace=True)
                return df
            else:
                return pd.DataFrame()
                    
        except Exception as e:
            st.warning(f"Could not fetch data for {symbol} ({interval}): {e}")
            
            # For core movers, try direct API call as fallback
            core_movers = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
            if symbol in core_movers:
                try:
                    st.info(f"Attempting direct API download for {symbol} {interval}...")
                    
                    # Direct API call for core movers
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365)  # 1 year for fallback
                    
                    klines = client.get_historical_klines(
                        symbol=symbol, 
                        interval=interval, 
                        start_str=start_date.strftime('%Y-%m-%d %H:%M:%S'),
                        end_str=end_date.strftime('%Y-%m-%d %H:%M:%S')
                    )
                    
                    if klines:
                        # Convert to DataFrame
                        df = pd.DataFrame(klines, columns=[
                            "timestamp", "open", "high", "low", "close", "volume", "close_time",
                            "quote_asset_volume", "number_of_trades", "taker_buy_base",
                            "taker_buy_quote", "ignore"
                        ])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                        
                        st.success(f"Direct API download successful for {symbol} {interval}")
                        return df
                    else:
                        st.error(f"No data available from API for {symbol} {interval}")
                        return pd.DataFrame()
                        
                except Exception as api_error:
                    st.error(f"Direct API call also failed for {symbol} {interval}: {api_error}")
                    return pd.DataFrame()
            else:
                return pd.DataFrame()

    def preprocess_data(data, window=5):
        data = data[~data.index.duplicated(keep='first')]
        data = data.ffill().bfill()
        if len(data) < window:
            return data
        data = data.rolling(window=window, min_periods=1).mean()
        return data

    def calculate_polynomial_regression(data, degree=4, kstd=2.0):
        if len(data) < degree + 1:
            return None, None, None
        X = np.arange(len(data))
        y = data.values
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                coefficients = np.polyfit(X, y, degree)
            polynomial = np.poly1d(coefficients)
            regression_line = polynomial(X)
            std_dev = np.std(y - regression_line)
            upper_band = regression_line + kstd * std_dev
            lower_band = regression_line - kstd * std_dev
            return regression_line, upper_band, lower_band
        except Exception:
            return None, None, None

    def generate_signal(indicators):
        if indicators is None or 'Close' not in indicators or len(indicators) == 0:
            return 'HOLD', None, None, None
        last_close = indicators['Close'].iloc[-1]
        last_lower_band = indicators['lower_band'].iloc[-1]
        last_upper_band = indicators['upper_band'].iloc[-1]

        signal = 'HOLD'
        if last_close < last_lower_band:
            signal = 'BUY'
        elif last_close > last_upper_band:
            signal = 'SELL'
        
        potential_return = ((last_upper_band - last_lower_band) / last_lower_band) * 100 if last_lower_band != 0 else 0
        return signal, last_lower_band, last_upper_band, potential_return

    def scan_coin(coin, timeframe, degree, kstd, lookback_candles, force_update=False):
        df = get_klines_from_db(coin, timeframe, lookback_candles, force_update)
        
        # For core movers, we must always return a result
        core_movers = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        is_core_mover = coin in core_movers
        
        if df.empty or len(df) < 50:  # Require at least 50 data points for reliable regression
            if is_core_mover:
                # For core movers, return a HOLD signal with basic info
                return {
                    'coin': coin,
                    'timeframe': timeframe,
                    'signal': 'HOLD',
                    'price': 0.0,
                    'indicators': pd.DataFrame(),
                    'potential_return': 0.0,
                    'upper_band': None,
                    'lower_band': None,
                    'error': 'Insufficient data'
                }
            else:
                return None
        
        close_data = preprocess_data(df['close'])
        regression_line, upper_band, lower_band = calculate_polynomial_regression(close_data, degree=degree, kstd=kstd)

        if regression_line is None:
            if is_core_mover:
                # For core movers, return a HOLD signal with basic info
                return {
                    'coin': coin,
                    'timeframe': timeframe,
                    'signal': 'HOLD',
                    'price': close_data.iloc[-1] if not close_data.empty else 0.0,
                    'indicators': pd.DataFrame(),
                    'potential_return': 0.0,
                    'upper_band': None,
                    'lower_band': None,
                    'error': 'Regression calculation failed'
                }
            else:
                return None

        indicators = pd.DataFrame({
            'Close': close_data,
            'regression_line': regression_line,
            'upper_band': upper_band,
            'lower_band': lower_band
        }, index=close_data.index)

        signal, ll, ul, pot_ret = generate_signal(indicators)

        # Return results for all signals, including HOLD
        return {
            'coin': coin,
            'timeframe': timeframe,
            'signal': signal,
            'price': close_data.iloc[-1],
            'indicators': indicators,
            'potential_return': pot_ret,
            'upper_band': ul,
            'lower_band': ll
        }

    # --- Streamlit UI ---

    st.title("📈 Crypto Scanner")
    st.markdown("This tool automatically finds and scans high-volume cryptocurrencies on Binance for potential trading signals.")

    # --- Sidebar Controls ---
    st.sidebar.header("Scan Parameters")
    
    # Add lookback period control
    lookback_candles = st.sidebar.slider("Lookback Period (candles)", 50, 1000, 500, help="Number of historical candles to use for regression analysis. Adapts to each timeframe automatically.", key="cs_lookback")
    
    # Show timeframe-specific lookback periods
    if lookback_candles:
        st.sidebar.markdown("**Lookback periods by timeframe:**")
        timeframes_display = ['15m', '1h', '4h', '1d']
        for tf in timeframes_display:
            interval_minutes = {'15m': 15, '1h': 60, '4h': 240, '1d': 1440}
            minutes = interval_minutes.get(tf, 60)
            total_minutes = lookback_candles * minutes
            days = total_minutes / 1440
            if days >= 1:
                st.sidebar.markdown(f"• {tf}: {days:.1f} days")
            else:
                hours = total_minutes / 60
                st.sidebar.markdown(f"• {tf}: {hours:.1f} hours")
    
    degree_param = st.sidebar.slider("Regression Degree", 2, 10, 4, key="cs_degree")
    kstd_param = st.sidebar.slider("Std. Dev. Multiplier (k)", 1.0, 3.0, 2.0, 0.1, key="cs_kstd")

    timeframes_to_scan = st.sidebar.multiselect(
        "Select Timeframes to Scan",
        options=['15m', '1h', '4h', '1d'],
        default=['15m', '1h', '4h', '1d'],
        key="cs_timeframes"
    )
    
    # Store current parameters for comparison
    current_params = {
        'lookback': lookback_candles,
        'degree': degree_param,
        'kstd': kstd_param,
        'timeframes': tuple(timeframes_to_scan)
    }
    
    # Clear results if parameters changed
    if 'scan_params' not in st.session_state:
        st.session_state.scan_params = current_params
    elif st.session_state.scan_params != current_params:
        st.session_state.scan_params = current_params
        if 'scan_results' in st.session_state:
            del st.session_state.scan_results

    # Always scan top 100 coins from Binance
    coins_to_scan = []

    # Database info
    st.sidebar.subheader("Database Info")
    try:
        db_summary = db_handler.get_data_summary()
        st.sidebar.info(f"Database: {db_summary['total_symbols']} symbols, {db_summary['total_bars']} bars")
    except:
        st.sidebar.info("Database: Initializing...")

    # Simple update mode
    update_fresh_data = st.sidebar.checkbox("🔄 Update data before scan", value=False, 
                                           help="Check this to fetch fresh data from Binance before scanning")

    # Scan controls
    col1, col2 = st.sidebar.columns(2)
    with col1:
        run_scan = st.button("🚀 Run Scan", key="cs_run_scan")
    with col2:
        if st.button("🗑️ Clear Cache", key="cs_clear_cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
            st.rerun()
    
    if run_scan:
        with st.spinner("Finding top 100 coins to scan..."):
            coins_to_scan = get_top_100_coins()
        if coins_to_scan:
            st.sidebar.success(f"Found {len(coins_to_scan)} top coins to scan.")
        else:
            st.sidebar.error("No coins found.")
        
        # Always include core movers in the scan
        core_movers = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        if not timeframes_to_scan:
            st.warning("Please select timeframes to scan.")
        else:
            # Always include core movers in the scan
            all_coins_to_scan = list(set(coins_to_scan + core_movers))  # Remove duplicates
            
            st.session_state.scan_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            total_jobs = len(all_coins_to_scan) * len(timeframes_to_scan)
            completed_jobs = 0
            
            status_text.info(f"Scanning {len(all_coins_to_scan)} coins across {len(timeframes_to_scan)} timeframes...")

            # Use the simple update checkbox
            try:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    for coin in all_coins_to_scan:
                        for tf in timeframes_to_scan:
                            futures.append(executor.submit(scan_coin, coin, tf, degree_param, kstd_param, lookback_candles, update_fresh_data))

                    for future in as_completed(futures):
                        try:
                            result = future.result(timeout=30)  # 30 second timeout
                            if result:
                                st.session_state.scan_results.append(result)
                        except Exception as e:
                            st.warning(f"Error processing scan result: {str(e)}")
                        completed_jobs += 1
                        progress_bar.progress(completed_jobs / total_jobs)
            except Exception as e:
                st.error(f"Error during scan execution: {str(e)}")
                st.info("Please try running the scan again.")
            
            status_text.success(f"Scan complete! Found {len(st.session_state.scan_results)} signals.")

    # --- Display Results ---
    if 'scan_results' in st.session_state and st.session_state.scan_results:
        # Get all available timeframes and arrange them in the correct order
        all_timeframes = list(set([r['timeframe'] for r in st.session_state.scan_results]))
        
        # Define the desired order
        desired_order = ['15m', '1h', '4h', '1d']
        
        # Sort timeframes according to desired order
        sorted_timeframes = []
        for tf in desired_order:
            if tf in all_timeframes:
                sorted_timeframes.append(tf)
        
        # Add any remaining timeframes that weren't in the desired order
        for tf in all_timeframes:
            if tf not in sorted_timeframes:
                sorted_timeframes.append(tf)
        
        if sorted_timeframes:
            # Create tabs at the top for each timeframe
            tab_names = [f"{tf} Results" for tf in sorted_timeframes]
            tabs = st.tabs(tab_names)
            
            for i, timeframe in enumerate(sorted_timeframes):
                with tabs[i]:
                    # Filter results for this timeframe
                    timeframe_results = [r for r in st.session_state.scan_results if r['timeframe'] == timeframe]
                    
                    # --- Core Movers for this timeframe ---
                    st.subheader(f"🎯 Core Movers ({timeframe})")
                    st.markdown("Key market indicators: BTCUSDT, ETHUSDT, SOLUSDT")
                    
                    core_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
                    core_results = [r for r in timeframe_results if r['coin'] in core_coins]
                    
                    if core_results:
                        cols = st.columns(len(core_results))
                        for j, result in enumerate(core_results):
                            with cols[j]:
                                # Determine color based on signal
                                if result['signal'] == 'BUY':
                                    color = "green"
                                    signal_emoji = "🟢"
                                elif result['signal'] == 'SELL':
                                    color = "red"
                                    signal_emoji = "🔴"
                                else:  # HOLD
                                    color = "orange"
                                    signal_emoji = "🟡"
                                
                                st.markdown(f"### **{result['coin']}** {signal_emoji}")
                                st.markdown(f"**Signal:** <span style='color:{color}; font-weight:bold;'>{result['signal']}</span>", unsafe_allow_html=True)
                                
                                # Handle error cases for core movers
                                if 'error' in result:
                                    st.error(f"Error: {result['error']}")
                                    st.metric("Current Price", "N/A")
                                    st.info("Data unavailable")
                                else:
                                    st.metric("Current Price", f"${result['price']:,.4f}")
                                    
                                    # Show band information for better context
                                    if result['upper_band'] and result['lower_band']:
                                        st.metric("Upper Band", f"${result['upper_band']:,.4f}")
                                        st.metric("Lower Band", f"${result['lower_band']:,.4f}")
                                    
                                    # Show potential return for actionable signals
                                    if result['signal'] != 'HOLD':
                                        st.metric("Potential Return", f"{result['potential_return']:.2f}%")
                                    else:
                                        st.info("Price is within normal range")
                                    
                                    # Small chart for each core coin (only if we have indicators data)
                                    if not result['indicators'].empty:
                                        indicators = result['indicators']
                                        fig = go.Figure()
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['Close'], mode='lines', name='Price', line=dict(color='blue')))
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['upper_band'], mode='lines', name='Upper', line=dict(dash='dash', color='red')))
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['lower_band'], mode='lines', name='Lower', line=dict(dash='dash', color='green')))
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['regression_line'], mode='lines', name='Trend', line=dict(color='orange')))
                                        
                                        fig.update_layout(
                                            title=f"{result['coin']} ({timeframe})",
                                            height=200,
                                            margin=dict(l=10, r=10, t=30, b=10),
                                            showlegend=False
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info("Chart unavailable")
                    else:
                        st.info(f"No core movers data available for {timeframe}. Please run the scan again.")
                    
                    st.markdown("---")
                    
                    # --- Other Opportunities for this timeframe ---
                    st.subheader(f"📊 {timeframe} Opportunities")
                    
                    # Filter out core movers from opportunities
                    other_results = [r for r in timeframe_results if r['coin'] not in core_coins]
                    
                    # Separate actionable and neutral signals
                    actionable_results = [r for r in other_results if r['signal'] != 'HOLD']
                    neutral_results = [r for r in other_results if r['signal'] == 'HOLD']
                    
                    # Filter controls for actionable signals
                    if actionable_results:
                        st.subheader(f"🚀 {timeframe} Actionable Signals")
                        
                        # Add filter for potential return
                        min_return = st.slider(
                            f"Minimum Potential Return (%) for {timeframe}",
                            min_value=0.0,
                            max_value=50.0,
                            value=0.0,
                            step=0.5,
                            key=f"filter_{timeframe}"
                        )
                        
                        # Filter actionable results by potential return
                        filtered_actionable = [r for r in actionable_results if r['potential_return'] >= min_return]
                        filtered_actionable = sorted(filtered_actionable, key=lambda x: x['potential_return'], reverse=True)
                        
                        if filtered_actionable:
                            st.info(f"Showing {len(filtered_actionable)} signals with ≥{min_return}% potential return")
                            
                            for result in filtered_actionable:
                                with st.container():
                                    col1, col2 = st.columns([1, 2])
                                    
                                    with col1:
                                        color = "green" if result['signal'] == 'BUY' else "red"
                                        signal_emoji = "🟢" if result['signal'] == 'BUY' else "🔴"
                                        st.markdown(f"### **{result['coin']}** {signal_emoji}")
                                        st.markdown(f"**Signal:** <span style='color:{color}; font-weight:bold;'>{result['signal']}</span>", unsafe_allow_html=True)
                                        st.metric("Current Price", f"${result['price']:,.4f}")
                                        st.metric("Potential Return", f"{result['potential_return']:.2f}%")

                                    with col2:
                                        indicators = result['indicators']
                                        fig = go.Figure()
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['Close'], mode='lines', name='Price'))
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['upper_band'], mode='lines', name='Upper Band', line=dict(dash='dash', color='red')))
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['lower_band'], mode='lines', name='Lower Band', line=dict(dash='dash', color='green')))
                                        fig.add_trace(go.Scatter(x=indicators.index, y=indicators['regression_line'], mode='lines', name='Regression Line', line=dict(color='blue')))
                                        
                                        fig.update_layout(
                                            title=f"{result['coin']} Chart ({timeframe})",
                                            height=300,
                                            margin=dict(l=20, r=20, t=40, b=20),
                                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                    
                                    st.markdown("---")
                        else:
                            st.warning(f"No signals found with ≥{min_return}% potential return for {timeframe}")
                    else:
                        st.info(f"No actionable signals found for {timeframe}")
                    
                    # Show neutral signals in compact format
                    if neutral_results:
                        st.subheader(f"🟡 {timeframe} Neutral Signals")
                        st.info(f"Found {len(neutral_results)} coins in neutral states on {timeframe}")
                        
                        # Group by coin for summary
                        neutral_by_coin = {}
                        for result in neutral_results:
                            if result['coin'] not in neutral_by_coin:
                                neutral_by_coin[result['coin']] = []
                            neutral_by_coin[result['coin']].append(result)
                        
                        # Display neutral coins in columns
                        cols = st.columns(3)
                        for j, (coin, results) in enumerate(neutral_by_coin.items()):
                            with cols[j % 3]:
                                avg_price = np.mean([r['price'] for r in results])
                                st.markdown(f"**{coin}**")
                                st.markdown(f"Price: ${avg_price:,.4f}")
                                st.markdown("Neutral")
                                st.markdown("---")
        else:
            st.info("No scan results available. Please run the scan first.")

    elif 'scan_results' not in st.session_state:
        st.info("Click 'Run Scan' in the sidebar to search for signals.") 