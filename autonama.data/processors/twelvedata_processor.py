"""
TwelveData Processor for TimescaleDB-First Architecture

This module provides TwelveData API integration for fetching
stock, forex, and commodity data with TimescaleDB storage.
"""

import logging
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import os

logger = logging.getLogger(__name__)


class TwelveDataProcessor:
    """
    TwelveData API processor for multi-asset data with rate limiting.
    
    Features:
    - Stock market data (NASDAQ, NYSE, etc.)
    - Forex data (major and minor pairs)
    - Commodity data (gold, oil, etc.)
    - Rate limiting (8 requests/minute for free tier)
    - TimescaleDB integration
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize TwelveData processor.
        
        Args:
            api_key: TwelveData API key
        """
        self.api_key = api_key or os.getenv('TWELVEDATA_API_KEY')
        
        if not self.api_key:
            raise ValueError("TwelveData API key is required. Set TWELVEDATA_API_KEY environment variable.")
        
        # Rate limiting (8 requests per minute for free tier, using 6 for safety)
        self.requests_per_minute = 6
        self.request_timestamps = []
        
        # API configuration
        self.base_url = "https://api.twelvedata.com"
        self.timeout = 30
        
        logger.info(f"TwelveData processor initialized with API key: {self.api_key[:8]}...")
    
    def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limits."""
        while len(self.request_timestamps) >= self.requests_per_minute:
            now = datetime.now()
            # Time since the oldest request
            time_passed = now - self.request_timestamps[0]
            if time_passed > timedelta(minutes=1):
                self.request_timestamps.pop(0)  # Remove the oldest timestamp
            else:
                # Wait until the oldest request is more than a minute old
                wait_seconds = (timedelta(minutes=1) - time_passed).total_seconds() + 0.1
                logger.info(f"Rate limit reached. Waiting for {wait_seconds:.2f} seconds.")
                time.sleep(wait_seconds)
                # After waiting, re-evaluate by popping the (now old) timestamp
                if self.request_timestamps:
                    self.request_timestamps.pop(0)

        self.request_timestamps.append(datetime.now())
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make API request with rate limiting and error handling.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            API response data or None on error
        """
        try:
            self._wait_for_rate_limit()
            
            # Add API key to parameters
            params['apikey'] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            
            logger.debug(f"Making request to: {url}")
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if 'status' in data and data['status'] == 'error':
                    logger.error(f"TwelveData API error: {data.get('message', 'Unknown error')}")
                    return None
                
                return data
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in request: {str(e)}")
            return None
    
    def fetch_time_series(self, symbol: str, interval: str = '1day', 
                         outputsize: int = 100, market: str = None) -> Optional[pd.DataFrame]:
        """
        Fetch time series data from TwelveData API.
        
        Args:
            symbol: Asset symbol
            interval: Data interval (1day, 1h, etc.)
            outputsize: Number of data points
            market: Market type (optional)
            
        Returns:
            DataFrame with OHLCV data or None on error
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
        }
        
        if market:
            params['market'] = market
        
        try:
            data = self._make_request('time_series', params)
            
            if not data or 'values' not in data:
                logger.warning(f"No time series data for {symbol}")
                return None
            
            if not isinstance(data['values'], list):
                logger.warning(f"Invalid time series format for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data['values'])
            
            if df.empty:
                logger.warning(f"Empty time series data for {symbol}")
                return None
            
            # Process datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            
            # Convert OHLCV columns to numeric
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by datetime
            df = df.sort_index()
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            if df.empty:
                logger.warning(f"No valid data after cleaning for {symbol}")
                return None
            
            logger.info(f"Successfully fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching time series for {symbol}: {str(e)}")
            return None
    
    def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time quote for a symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Quote data or None on error
        """
        try:
            data = self._make_request('quote', {'symbol': symbol})
            
            if not data:
                logger.warning(f"No quote data for {symbol}")
                return None
            
            logger.info(f"Successfully fetched quote for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None
    
    def get_stocks_list(self, exchange: str = "NASDAQ", country: str = "USA") -> List[str]:
        """
        Fetch a list of stock symbols from the TwelveData API.
        
        Args:
            exchange: Stock exchange
            country: Country code
            
        Returns:
            List of stock symbols
        """
        try:
            params = {"exchange": exchange, "country": country}
            data = self._make_request('stocks', params)
            
            if not data or 'data' not in data:
                logger.warning(f"No stocks data for {exchange}")
                return []
            
            if not isinstance(data['data'], list):
                logger.warning(f"Invalid stocks data format for {exchange}")
                return []
            
            symbols = [item['symbol'] for item in data['data'] if item and 'symbol' in item]
            logger.info(f"Successfully fetched {len(symbols)} stocks from {exchange}")
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching stocks list: {str(e)}")
            return []
    
    def update_symbol_data(self, symbol: str, category: str, 
                          force_update: bool = False) -> Dict[str, Any]:
        """
        Update data for a specific symbol.
        
        Args:
            symbol: Asset symbol
            category: Asset category (stock, forex, commodity)
            force_update: Whether to force update
            
        Returns:
            Dictionary with update results
        """
        try:
            logger.info(f"Updating {symbol} in {category}")
            
            # Determine market type for API
            market_mapping = {
                'stock': None,  # No market parameter needed for stocks
                'forex': 'forex', 
                'commodity': 'commodity'
            }
            market = market_mapping.get(category)
            
            # Fetch time series data
            df = self.fetch_time_series(symbol, "1day", outputsize=100, market=market)
            
            if df is None or df.empty:
                logger.warning(f"No data received for {symbol} in {category}")
                return {
                    'symbol': symbol,
                    'category': category,
                    'success': False,
                    'error': 'No data received',
                    'records': 0
                }
            
            # Convert DataFrame to list of dictionaries for TimescaleDB storage
            data_records = []
            for timestamp, row in df.iterrows():
                record = {
                    'timestamp': timestamp,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row.get('volume', 0))
                }
                data_records.append(record)
            
            logger.info(f"Successfully processed {len(data_records)} records for {symbol}")
            
            return {
                'symbol': symbol,
                'category': category,
                'success': True,
                'records': len(data_records),
                'data': data_records,
                'latest_price': float(df['close'].iloc[-1]) if not df.empty else None
            }
            
        except Exception as e:
            logger.error(f"Error updating data for {symbol} in {category}: {str(e)}")
            return {
                'symbol': symbol,
                'category': category,
                'success': False,
                'error': str(e),
                'records': 0
            }
    
    def update_category_data(self, category: str, symbols: List[str], 
                           force_update: bool = False) -> Dict[str, int]:
        """
        Update data for multiple symbols in a category.
        
        Args:
            category: Asset category
            symbols: List of symbols to update
            force_update: Whether to force update all symbols
            
        Returns:
            Dictionary with update statistics
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0, 'total': len(symbols)}
        
        logger.info(f"Starting update for {len(symbols)} symbols in {category}")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                logger.info(f"Processing {symbol} ({i}/{len(symbols)})")
                
                result = self.update_symbol_data(symbol, category, force_update)
                
                if result['success']:
                    stats['success'] += 1
                    logger.info(f"✅ {symbol}: {result['records']} records")
                else:
                    stats['failed'] += 1
                    logger.warning(f"❌ {symbol}: {result.get('error', 'Unknown error')}")
                
                # Add small delay between requests
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                stats['failed'] += 1
        
        logger.info(f"Category update completed: {stats}")
        return stats


# Static symbol lists for different asset classes
STOCK_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'WMT',
    'PG', 'MA', 'UNH', 'HD', 'BAC', 'XOM', 'DIS', 'NFLX', 'ADBE', 'PYPL',
    'CRM', 'CSCO', 'PFE', 'ABT', 'LLY', 'JNJ', 'KO', 'PEP', 'AVGO', 'COST'
]

FOREX_SYMBOLS = [
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CHF', 'USD/CAD', 'NZD/USD', 'USD/SGD',
    'EUR/GBP', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY', 'CAD/JPY', 'CHF/JPY', 'NZD/JPY',
    'EUR/CHF', 'GBP/CHF', 'AUD/CHF', 'CAD/CHF', 'NZD/CHF'
]

COMMODITY_SYMBOLS = [
    'XAU/USD', 'XAG/USD', 'CL=F', 'GC=F', 'SI=F', 'PL=F', 'PA=F', 'HG=F',
    'ZC=F', 'ZS=F', 'ZW=F', 'KC=F', 'CT=F', 'CC=F', 'SB=F'
]