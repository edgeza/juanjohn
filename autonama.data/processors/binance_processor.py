"""
Enhanced Binance Processor with CCXT Integration

This module provides comprehensive Binance API integration with CCXT fallback,
symbol conversion utilities, WebSocket support, and TimescaleDB storage.
"""

import logging
import time
import requests
import pandas as pd
import ccxt
import json
import threading

# Optional websocket import
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    websocket = None
    WEBSOCKET_AVAILABLE = False
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from decimal import Decimal
import hmac
import hashlib
from urllib.parse import urlencode

from processors.base_processor import BaseProcessor, ProcessorStatus
from processors.duckdb_manager import get_duckdb_manager
from config.api_config import get_api_config, APIProvider
from config.processor_config import get_processor_config
from models.asset_models import AssetType
from models.asset_models import AssetMetadata, AssetPrice, create_asset_from_dict, create_price_from_dict
from models.ohlc_models import OHLCData, Timeframe, DataSource as OHLCDataSource, create_ohlc_from_dict
from utils.error_handler import (
    APIError, RateLimitError, ValidationError, NetworkError,
    handle_processor_errors, retry_on_error, create_error_context
)

logger = logging.getLogger(__name__)


class BinanceProcessor(BaseProcessor):
    """
    Enhanced Binance processor with CCXT integration.
    
    Features:
    - Direct Binance API calls with authentication
    - CCXT integration as fallback
    - Symbol conversion utilities
    - WebSocket real-time data
    - Rate limiting (1200 requests/minute)
    - TimescaleDB integration
    """
    
    def __init__(self, api_key: str = None, secret_key: str = None, 
                 ccxt_exchange=None, duckdb_manager=None):
        """
        Initialize Binance processor.
        
        Args:
            api_key: Binance API key
            secret_key: Binance secret key
            ccxt_exchange: CCXT exchange instance
            duckdb_manager: DuckDBManager instance
        """
        # Get configuration
        config = get_processor_config().get_processor_settings('binance_processor')
        super().__init__('binance_processor', config.__dict__)
        
        # API configuration
        api_config = get_api_config()
        credentials = api_config.get_credentials(APIProvider.BINANCE)
        self.api_key = api_key or credentials.api_key
        self.secret_key = secret_key or credentials.secret_key
        self.endpoints = api_config.get_endpoints(APIProvider.BINANCE)
        
        # Database manager
        self.duckdb_manager = duckdb_manager or get_duckdb_manager()
        
        # API endpoints
        self.base_url = self.endpoints.base_url
        self.websocket_url = self.endpoints.websocket_url
        self.timeout = self.endpoints.timeout
        
        # Rate limiting (1200 requests per minute)
        self.requests_per_minute = self.endpoints.rate_limit_requests
        self.request_timestamps = []
        
        # CCXT integration
        self.ccxt_exchange = ccxt_exchange
        if not self.ccxt_exchange and self.api_key and self.secret_key:
            try:
                self.ccxt_exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.secret_key,
                    'sandbox': credentials.sandbox,
                    'enableRateLimit': True,
                    'timeout': self.timeout * 1000
                })
            except Exception as e:
                self.logger.warning(f"Failed to initialize CCXT exchange: {e}")
        
        # WebSocket connections
        self.websocket_connections = {}
        self.websocket_callbacks = {}
        self.websocket_lock = threading.Lock()
        
        # Symbol conversion mappings
        self.symbol_mappings = {
            # Internal format -> Binance format
            'BTC/USDT': 'BTCUSDT',
            'ETH/USDT': 'ETHUSDT',
            'ADA/USDT': 'ADAUSDT',
            'BNB/USDT': 'BNBUSDT',
            'SOL/USDT': 'SOLUSDT',
            'DOT/USDT': 'DOTUSDT',
            'LINK/USDT': 'LINKUSDT',
            'UNI/USDT': 'UNIUSDT',
            'LTC/USDT': 'LTCUSDT',
            'BCH/USDT': 'BCHUSDT'
        }
        
        # Reverse mapping
        self.reverse_mappings = {v: k for k, v in self.symbol_mappings.items()}
        
        # Timeframe mapping
        self.timeframe_mapping = {
            Timeframe.MINUTE_1: '1m',
            Timeframe.MINUTE_5: '5m',
            Timeframe.MINUTE_15: '15m',
            Timeframe.MINUTE_30: '30m',
            Timeframe.HOUR_1: '1h',
            Timeframe.HOUR_2: '2h',
            Timeframe.HOUR_4: '4h',
            Timeframe.HOUR_6: '6h',
            Timeframe.HOUR_8: '8h',
            Timeframe.HOUR_12: '12h',
            Timeframe.DAY_1: '1d',
            Timeframe.DAY_3: '3d',
            Timeframe.WEEK_1: '1w',
            Timeframe.MONTH_1: '1M'
        }
        
        self.logger.info("Binance processor initialized with CCXT integration")
    
    def validate_config(self) -> bool:
        """Validate processor configuration."""
        try:
            # Test API connection (public endpoint)
            response = self._make_request('GET', '/api/v3/ping')
            
            if response is None:
                return False
            
            # Test CCXT if available
            if self.ccxt_exchange:
                try:
                    self.ccxt_exchange.load_markets()
                    self.logger.info("CCXT exchange loaded successfully")
                except Exception as e:
                    self.logger.warning(f"CCXT validation failed: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def process_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Process data for a crypto symbol.
        
        Args:
            symbol: Crypto symbol in internal format (e.g., 'BTC/USDT')
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with processed data
        """
        try:
            binance_symbol = self.get_binance_symbol(symbol)
            
            # Get OHLC data
            ohlc_data = self.fetch_ohlc_data(
                symbol, 
                kwargs.get('timeframe', Timeframe.HOUR_1),
                kwargs.get('limit', 100)
            )
            
            # Get current price
            current_price = self.fetch_current_price(symbol)
            
            # Get 24h ticker statistics
            ticker_stats = self.fetch_24h_ticker(symbol)
            
            return {
                'symbol': symbol,
                'binance_symbol': binance_symbol,
                'asset_type': AssetType.CRYPTO,
                'ohlc_data': ohlc_data,
                'current_price': current_price,
                'ticker_stats': ticker_stats,
                'metadata': self._get_crypto_metadata(symbol)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process data for {symbol}: {e}")
            raise
    
    def get_binance_symbol(self, symbol: str) -> str:
        """
        Convert internal symbol format to Binance format.
        
        Args:
            symbol: Symbol in internal format (e.g., 'BTC/USDT')
            
        Returns:
            Symbol in Binance format (e.g., 'BTCUSDT')
        """
        if symbol in self.symbol_mappings:
            return self.symbol_mappings[symbol]
        
        # Auto-convert format
        if '/' in symbol:
            base, quote = symbol.split('/')
            if quote == 'USD':
                return f"{base}USDT"
            else:
                return f"{base}{quote}"
        
        # Already in Binance format
        return symbol.upper()
    
    def get_internal_symbol(self, binance_symbol: str) -> str:
        """
        Convert Binance format to internal format.
        
        Args:
            binance_symbol: Symbol in Binance format (e.g., 'BTCUSDT')
            
        Returns:
            Symbol in internal format (e.g., 'BTC/USDT')
        """
        if binance_symbol in self.reverse_mappings:
            return self.reverse_mappings[binance_symbol]
        
        # Auto-convert format
        if binance_symbol.endswith('USDT'):
            base = binance_symbol[:-4]
            return f"{base}/USDT"
        elif binance_symbol.endswith('BTC'):
            base = binance_symbol[:-3]
            return f"{base}/BTC"
        elif binance_symbol.endswith('ETH'):
            base = binance_symbol[:-3]
            return f"{base}/ETH"
        
        return binance_symbol
    
    def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limits."""
        now = datetime.now()
        
        # Remove timestamps older than 1 minute
        cutoff_time = now - timedelta(minutes=1)
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]
        
        # Check if we need to wait
        if len(self.request_timestamps) >= self.requests_per_minute:
            oldest_request = min(self.request_timestamps)
            wait_time = 61 - (now - oldest_request).total_seconds()
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
        
        # Record this request
        self.request_timestamps.append(now)
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate signature for authenticated requests."""
        if not self.secret_key:
            raise ValueError("Secret key required for authenticated requests")
        
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @retry_on_error(max_retries=3, delay=1.0)
    @handle_processor_errors('binance_processor', 'make_request')
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None,
                     signed: bool = False) -> Optional[Dict[str, Any]]:
        """
        Make API request with rate limiting and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs authentication
            
        Returns:
            API response data
        """
        # Wait for rate limit
        self._wait_for_rate_limit()
        
        params = params or {}
        headers = {}
        
        # Add API key for authenticated requests
        if self.api_key and (signed or endpoint.startswith('/api/v3/account')):
            headers['X-MBX-APIKEY'] = self.api_key
        
        # Add signature for signed requests
        if signed and self.secret_key:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, data=params, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            # Log API request
            self.logger.debug(f"Binance API: {method} {endpoint} - Status: {response.status_code} - Time: {response_time:.3f}s")
            
            # Handle HTTP errors
            if response.status_code == 429:
                raise RateLimitError(
                    "Binance rate limit exceeded",
                    retry_after=60,
                    context=create_error_context('binance_processor', 'api_request', endpoint=endpoint)
                )
            elif response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                
                error_message = error_data.get('msg', f"HTTP {response.status_code}")
                
                raise APIError(
                    f"Binance API error: {error_message}",
                    status_code=response.status_code,
                    response_body=response.text,
                    context=create_error_context('binance_processor', 'api_request', endpoint=endpoint)
                )
            
            # Parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                raise APIError(
                    f"Invalid JSON response: {e}",
                    status_code=response.status_code,
                    response_body=response.text,
                    context=create_error_context('binance_processor', 'api_request', endpoint=endpoint)
                )
                
        except requests.exceptions.Timeout:
            raise NetworkError(
                f"Request timeout after {self.timeout}s",
                context=create_error_context('binance_processor', 'api_request', endpoint=endpoint)
            )
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(
                f"Connection error: {e}",
                context=create_error_context('binance_processor', 'api_request', endpoint=endpoint)
            )
        except requests.exceptions.RequestException as e:
            raise APIError(
                f"Request failed: {e}",
                context=create_error_context('binance_processor', 'api_request', endpoint=endpoint)
            )
    
    @handle_processor_errors('binance_processor', 'fetch_ohlc_data')
    def fetch_ohlc_data(self, symbol: str, timeframe: Timeframe = Timeframe.HOUR_1,
                       limit: int = 100, start_time: datetime = None,
                       end_time: datetime = None) -> List[OHLCData]:
        """
        Fetch OHLC data from Binance.
        
        Args:
            symbol: Symbol in internal format
            timeframe: Data timeframe
            limit: Number of data points
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            List of OHLCData objects
        """
        try:
            binance_symbol = self.get_binance_symbol(symbol)
            binance_timeframe = self.timeframe_mapping.get(timeframe, '1h')
            
            params = {
                'symbol': binance_symbol,
                'interval': binance_timeframe,
                'limit': min(limit, 1000)  # Binance limit
            }
            
            if start_time:
                params['startTime'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            # Try direct API first
            try:
                data = self._make_request('GET', '/api/v3/klines', params)
                
                if data:
                    return self._process_klines_data(data, symbol, timeframe)
                    
            except Exception as e:
                self.logger.warning(f"Direct API failed for {symbol}, trying CCXT: {e}")
            
            # Fallback to CCXT
            if self.ccxt_exchange:
                try:
                    ccxt_timeframe = self.timeframe_mapping.get(timeframe, '1h')
                    since = int(start_time.timestamp() * 1000) if start_time else None
                    
                    ohlcv = self.ccxt_exchange.fetch_ohlcv(
                        binance_symbol, ccxt_timeframe, since, limit
                    )
                    
                    return self._process_ccxt_ohlcv(ohlcv, symbol, timeframe)
                    
                except Exception as e:
                    self.logger.error(f"CCXT fallback failed for {symbol}: {e}")
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLC data for {symbol}: {e}")
            raise
    
    @handle_processor_errors('binance_processor', 'fetch_current_price')
    def fetch_current_price(self, symbol: str) -> Optional[AssetPrice]:
        """
        Fetch current price for a symbol.
        
        Args:
            symbol: Symbol in internal format
            
        Returns:
            AssetPrice object or None
        """
        try:
            binance_symbol = self.get_binance_symbol(symbol)
            
            # Try direct API first
            try:
                data = self._make_request('GET', '/api/v3/ticker/price', {
                    'symbol': binance_symbol
                })
                
                if data and 'price' in data:
                    return AssetPrice(
                        symbol=symbol,
                        price=Decimal(str(data['price'])),
                        timestamp=datetime.utcnow(),
                        source='binance'
                    )
                    
            except Exception as e:
                self.logger.warning(f"Direct price API failed for {symbol}, trying CCXT: {e}")
            
            # Fallback to CCXT
            if self.ccxt_exchange:
                try:
                    ticker = self.ccxt_exchange.fetch_ticker(binance_symbol)
                    
                    return AssetPrice(
                        symbol=symbol,
                        price=Decimal(str(ticker['last'])),
                        bid=Decimal(str(ticker['bid'])) if ticker['bid'] else None,
                        ask=Decimal(str(ticker['ask'])) if ticker['ask'] else None,
                        high_24h=Decimal(str(ticker['high'])) if ticker['high'] else None,
                        low_24h=Decimal(str(ticker['low'])) if ticker['low'] else None,
                        volume_24h=Decimal(str(ticker['baseVolume'])) if ticker['baseVolume'] else None,
                        change_24h=Decimal(str(ticker['change'])) if ticker['change'] else None,
                        change_percent_24h=Decimal(str(ticker['percentage'])) if ticker['percentage'] else None,
                        timestamp=datetime.utcnow(),
                        source='binance_ccxt'
                    )
                    
                except Exception as e:
                    self.logger.error(f"CCXT price fallback failed for {symbol}: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to fetch current price for {symbol}: {e}")
            return None
    
    @handle_processor_errors('binance_processor', 'fetch_24h_ticker')
    def fetch_24h_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch 24h ticker statistics.
        
        Args:
            symbol: Symbol in internal format
            
        Returns:
            Dictionary with ticker statistics
        """
        try:
            binance_symbol = self.get_binance_symbol(symbol)
            
            data = self._make_request('GET', '/api/v3/ticker/24hr', {
                'symbol': binance_symbol
            })
            
            if data:
                return {
                    'symbol': symbol,
                    'price_change': Decimal(str(data.get('priceChange', '0'))),
                    'price_change_percent': Decimal(str(data.get('priceChangePercent', '0'))),
                    'weighted_avg_price': Decimal(str(data.get('weightedAvgPrice', '0'))),
                    'prev_close_price': Decimal(str(data.get('prevClosePrice', '0'))),
                    'last_price': Decimal(str(data.get('lastPrice', '0'))),
                    'bid_price': Decimal(str(data.get('bidPrice', '0'))),
                    'ask_price': Decimal(str(data.get('askPrice', '0'))),
                    'open_price': Decimal(str(data.get('openPrice', '0'))),
                    'high_price': Decimal(str(data.get('highPrice', '0'))),
                    'low_price': Decimal(str(data.get('lowPrice', '0'))),
                    'volume': Decimal(str(data.get('volume', '0'))),
                    'quote_volume': Decimal(str(data.get('quoteVolume', '0'))),
                    'open_time': datetime.fromtimestamp(data.get('openTime', 0) / 1000),
                    'close_time': datetime.fromtimestamp(data.get('closeTime', 0) / 1000),
                    'count': int(data.get('count', 0))
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to fetch 24h ticker for {symbol}: {e}")
            return None
    
    def _process_klines_data(self, data: List[List], symbol: str, 
                           timeframe: Timeframe) -> List[OHLCData]:
        """Process Binance klines data into OHLCData objects."""
        ohlc_data = []
        
        for kline in data:
            try:
                ohlc = OHLCData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    timeframe=timeframe,
                    open=Decimal(str(kline[1])),
                    high=Decimal(str(kline[2])),
                    low=Decimal(str(kline[3])),
                    close=Decimal(str(kline[4])),
                    volume=Decimal(str(kline[5])),
                    volume_quote=Decimal(str(kline[7])),
                    trades_count=int(kline[8]),
                    source=OHLCDataSource.BINANCE
                )
                ohlc_data.append(ohlc)
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to process kline data for {symbol}: {e}")
                continue
        
        return ohlc_data
    
    def _process_ccxt_ohlcv(self, data: List[List], symbol: str, 
                          timeframe: Timeframe) -> List[OHLCData]:
        """Process CCXT OHLCV data into OHLCData objects."""
        ohlc_data = []
        
        for ohlcv in data:
            try:
                ohlc = OHLCData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(ohlcv[0] / 1000),
                    timeframe=timeframe,
                    open=Decimal(str(ohlcv[1])),
                    high=Decimal(str(ohlcv[2])),
                    low=Decimal(str(ohlcv[3])),
                    close=Decimal(str(ohlcv[4])),
                    volume=Decimal(str(ohlcv[5])),
                    source=OHLCDataSource.CCXT
                )
                ohlc_data.append(ohlc)
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to process CCXT OHLCV data for {symbol}: {e}")
                continue
        
        return ohlc_data
    
    def _get_crypto_metadata(self, symbol: str) -> Optional[AssetMetadata]:
        """Get crypto metadata."""
        try:
            base, quote = symbol.split('/')
            return AssetMetadata(
                symbol=symbol,
                name=f"{base} / {quote}",
                asset_type=AssetType.CRYPTO,
                exchange='binance',
                base_currency=base,
                quote_currency=quote
            )
        except Exception as e:
            self.logger.error(f"Failed to get crypto metadata for {symbol}: {e}")
            return None
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols."""
        try:
            # Try direct API first
            try:
                data = self._make_request('GET', '/api/v3/exchangeInfo')
                
                if data and 'symbols' in data:
                    symbols = []
                    for symbol_info in data['symbols']:
                        if symbol_info.get('status') == 'TRADING':
                            binance_symbol = symbol_info['symbol']
                            internal_symbol = self.get_internal_symbol(binance_symbol)
                            symbols.append(internal_symbol)
                    return symbols
                    
            except Exception as e:
                self.logger.warning(f"Direct API failed for symbols, trying CCXT: {e}")
            
            # Fallback to CCXT
            if self.ccxt_exchange:
                try:
                    markets = self.ccxt_exchange.load_markets()
                    return [self.get_internal_symbol(symbol) for symbol in markets.keys()]
                except Exception as e:
                    self.logger.error(f"CCXT fallback failed for symbols: {e}")
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get supported symbols: {e}")
            return []
