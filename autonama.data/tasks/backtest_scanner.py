import os
import sys
import logging
from datetime import datetime, timedelta
from celery import shared_task
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Optional, Tuple

# Add the engine directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'autonama.engine'))

from backtest_engine import BacktestEngine

# Suppress warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

# Binance configuration (you'll need to add your API keys)
BINANCE_CONFIG = {
    'api_key': 'your_api_key_here',  # Replace with your actual API key
    'api_secret': 'your_api_secret_here'  # Replace with your actual API secret
}

@shared_task(bind=True)
def run_daily_backtest_scan(self):
    """
    Run daily backtest scan for all top 100 assets
    """
    try:
        logger.info("Starting daily backtest scan...")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Run the daily scan
        results = engine.run_daily_scan()
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        hold_signals = [r for r in results if r['signal'] == 'HOLD']
        
        logger.info(f"Daily scan complete:")
        logger.info(f"Total assets scanned: {len(results)}")
        logger.info(f"BUY signals: {len(buy_signals)}")
        logger.info(f"SELL signals: {len(sell_signals)}")
        logger.info(f"HOLD signals: {len(hold_signals)}")
        
        # Log top BUY signals
        if buy_signals:
            buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
            logger.info("Top BUY signals:")
            for signal in buy_signals[:5]:
                logger.info(f"{signal['symbol']}: {signal['potential_return']:.2f}% potential return")
        
        return {
            'status': 'success',
            'total_scanned': len(results),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'hold_signals': len(hold_signals),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in daily backtest scan: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def scan_single_asset(self, symbol: str, interval: str = '1d', degree: int = 4, kstd: float = 2.0, days: int = 720):
    """
    Scan a single asset for trading signals
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval ('1d' for daily)
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier for bands
        days: Number of days to analyze
    """
    try:
        logger.info(f"Starting scan for {symbol}")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Scan the asset
        result = engine.scan_asset(symbol, interval, degree, kstd, days)
        
        if result:
            logger.info(f"Scan complete for {symbol}: {result['signal']} signal, {result['potential_return']:.2f}% potential return")
            return result
        else:
            logger.warning(f"No result for {symbol}")
            return None
            
    except Exception as e:
        logger.error(f"Error scanning {symbol}: {e}")
        self.retry(countdown=60, max_retries=2)  # Retry after 1 minute, max 2 times
        return None

@shared_task(bind=True)
def scan_multiple_assets(self, symbols: List[str], interval: str = '1d', degree: int = 4, kstd: float = 2.0, days: int = 720):
    """
    Scan multiple assets in parallel
    
    Args:
        symbols: List of trading symbols
        interval: Time interval
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier for bands
        days: Number of days to analyze
    """
    try:
        logger.info(f"Starting scan for {len(symbols)} assets")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Scan all assets
        results = engine.scan_all_assets(symbols, interval, degree, kstd, days)
        
        # Store alerts
        if results:
            engine.store_alerts(results)
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        
        logger.info(f"Multi-asset scan complete:")
        logger.info(f"Total assets scanned: {len(results)}")
        logger.info(f"BUY signals: {len(buy_signals)}")
        logger.info(f"SELL signals: {len(sell_signals)}")
        
        return {
            'status': 'success',
            'total_scanned': len(results),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in multi-asset scan: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def get_current_alerts(self, signal_type: str = None, min_potential_return: float = 0.0):
    """
    Get current alerts from the database
    
    Args:
        signal_type: Filter by signal type ('BUY', 'SELL', 'HOLD')
        min_potential_return: Minimum potential return percentage
    """
    try:
        logger.info("Fetching current alerts...")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Get alerts
        alerts = engine.get_alerts(signal_type, min_potential_return)
        
        logger.info(f"Retrieved {len(alerts)} alerts")
        
        return {
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def update_historical_data(self, symbols: List[str] = None, interval: str = '1d', days: int = 720):
    """
    Update historical data for assets
    
    Args:
        symbols: List of symbols to update (if None, uses top 100)
        interval: Time interval
        days: Number of days to fetch
    """
    try:
        logger.info("Starting historical data update...")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        if symbols is None:
            symbols = engine.get_top_100_assets()
        
        updated_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                logger.info(f"Updating data for {symbol}")
                df = engine.fetch_historical_data(symbol, interval, days)
                
                if not df.empty:
                    updated_count += 1
                    logger.info(f"Successfully updated {symbol}: {len(df)} records")
                else:
                    failed_count += 1
                    logger.warning(f"No data received for {symbol}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error updating {symbol}: {e}")
        
        logger.info(f"Historical data update complete:")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Failed: {failed_count}")
        
        return {
            'status': 'success',
            'updated_count': updated_count,
            'failed_count': failed_count,
            'total_attempted': len(symbols),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in historical data update: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 
import sys
import logging
from datetime import datetime, timedelta
from celery import shared_task
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Optional, Tuple

# Add the engine directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'autonama.engine'))

from backtest_engine import BacktestEngine

# Suppress warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

# Binance configuration (you'll need to add your API keys)
BINANCE_CONFIG = {
    'api_key': 'your_api_key_here',  # Replace with your actual API key
    'api_secret': 'your_api_secret_here'  # Replace with your actual API secret
}

@shared_task(bind=True)
def run_daily_backtest_scan(self):
    """
    Run daily backtest scan for all top 100 assets
    """
    try:
        logger.info("Starting daily backtest scan...")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Run the daily scan
        results = engine.run_daily_scan()
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        hold_signals = [r for r in results if r['signal'] == 'HOLD']
        
        logger.info(f"Daily scan complete:")
        logger.info(f"Total assets scanned: {len(results)}")
        logger.info(f"BUY signals: {len(buy_signals)}")
        logger.info(f"SELL signals: {len(sell_signals)}")
        logger.info(f"HOLD signals: {len(hold_signals)}")
        
        # Log top BUY signals
        if buy_signals:
            buy_signals.sort(key=lambda x: x['potential_return'], reverse=True)
            logger.info("Top BUY signals:")
            for signal in buy_signals[:5]:
                logger.info(f"{signal['symbol']}: {signal['potential_return']:.2f}% potential return")
        
        return {
            'status': 'success',
            'total_scanned': len(results),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'hold_signals': len(hold_signals),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in daily backtest scan: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def scan_single_asset(self, symbol: str, interval: str = '1d', degree: int = 4, kstd: float = 2.0, days: int = 720):
    """
    Scan a single asset for trading signals
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Time interval ('1d' for daily)
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier for bands
        days: Number of days to analyze
    """
    try:
        logger.info(f"Starting scan for {symbol}")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Scan the asset
        result = engine.scan_asset(symbol, interval, degree, kstd, days)
        
        if result:
            logger.info(f"Scan complete for {symbol}: {result['signal']} signal, {result['potential_return']:.2f}% potential return")
            return result
        else:
            logger.warning(f"No result for {symbol}")
            return None
            
    except Exception as e:
        logger.error(f"Error scanning {symbol}: {e}")
        self.retry(countdown=60, max_retries=2)  # Retry after 1 minute, max 2 times
        return None

@shared_task(bind=True)
def scan_multiple_assets(self, symbols: List[str], interval: str = '1d', degree: int = 4, kstd: float = 2.0, days: int = 720):
    """
    Scan multiple assets in parallel
    
    Args:
        symbols: List of trading symbols
        interval: Time interval
        degree: Polynomial degree for regression
        kstd: Standard deviation multiplier for bands
        days: Number of days to analyze
    """
    try:
        logger.info(f"Starting scan for {len(symbols)} assets")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Scan all assets
        results = engine.scan_all_assets(symbols, interval, degree, kstd, days)
        
        # Store alerts
        if results:
            engine.store_alerts(results)
        
        # Log summary
        buy_signals = [r for r in results if r['signal'] == 'BUY']
        sell_signals = [r for r in results if r['signal'] == 'SELL']
        
        logger.info(f"Multi-asset scan complete:")
        logger.info(f"Total assets scanned: {len(results)}")
        logger.info(f"BUY signals: {len(buy_signals)}")
        logger.info(f"SELL signals: {len(sell_signals)}")
        
        return {
            'status': 'success',
            'total_scanned': len(results),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in multi-asset scan: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def get_current_alerts(self, signal_type: str = None, min_potential_return: float = 0.0):
    """
    Get current alerts from the database
    
    Args:
        signal_type: Filter by signal type ('BUY', 'SELL', 'HOLD')
        min_potential_return: Minimum potential return percentage
    """
    try:
        logger.info("Fetching current alerts...")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        # Get alerts
        alerts = engine.get_alerts(signal_type, min_potential_return)
        
        logger.info(f"Retrieved {len(alerts)} alerts")
        
        return {
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def update_historical_data(self, symbols: List[str] = None, interval: str = '1d', days: int = 720):
    """
    Update historical data for assets
    
    Args:
        symbols: List of symbols to update (if None, uses top 100)
        interval: Time interval
        days: Number of days to fetch
    """
    try:
        logger.info("Starting historical data update...")
        
        # Initialize the backtesting engine
        engine = BacktestEngine(DB_CONFIG, BINANCE_CONFIG)
        
        if symbols is None:
            symbols = engine.get_top_100_assets()
        
        updated_count = 0
        failed_count = 0
        
        for symbol in symbols:
            try:
                logger.info(f"Updating data for {symbol}")
                df = engine.fetch_historical_data(symbol, interval, days)
                
                if not df.empty:
                    updated_count += 1
                    logger.info(f"Successfully updated {symbol}: {len(df)} records")
                else:
                    failed_count += 1
                    logger.warning(f"No data received for {symbol}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error updating {symbol}: {e}")
        
        logger.info(f"Historical data update complete:")
        logger.info(f"Successfully updated: {updated_count}")
        logger.info(f"Failed: {failed_count}")
        
        return {
            'status': 'success',
            'updated_count': updated_count,
            'failed_count': failed_count,
            'total_attempted': len(symbols),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in historical data update: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 
 