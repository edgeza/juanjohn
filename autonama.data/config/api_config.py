"""
API Configuration Management

This module manages API keys, endpoints, and configuration for all external data sources.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Supported API providers."""
    TWELVEDATA = "twelvedata"
    BINANCE = "binance"
    CCXT = "ccxt"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    POLYGON = "polygon"


@dataclass
class APIEndpoints:
    """API endpoint configurations."""
    base_url: str
    websocket_url: Optional[str] = None
    rate_limit_requests: int = 60
    rate_limit_period: int = 60  # seconds
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0


@dataclass
class APICredentials:
    """API credentials configuration."""
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    passphrase: Optional[str] = None
    sandbox: bool = False


class APIConfig:
    """
    Centralized API configuration management.
    
    Handles API keys, endpoints, rate limits, and other configuration
    for all external data providers.
    """
    
    # Default API configurations
    DEFAULT_CONFIGS = {
        APIProvider.TWELVEDATA: APIEndpoints(
            base_url="https://api.twelvedata.com",
            rate_limit_requests=8,  # Free tier: 8 requests/minute
            rate_limit_period=60,
            timeout=30,
            max_retries=3
        ),
        APIProvider.BINANCE: APIEndpoints(
            base_url="https://api.binance.com",
            websocket_url="wss://stream.binance.com:9443/ws",
            rate_limit_requests=1200,  # 1200 requests/minute
            rate_limit_period=60,
            timeout=10,
            max_retries=3
        ),
        APIProvider.ALPHA_VANTAGE: APIEndpoints(
            base_url="https://www.alphavantage.co",
            rate_limit_requests=5,  # Free tier: 5 requests/minute
            rate_limit_period=60,
            timeout=30,
            max_retries=3
        ),
        APIProvider.YAHOO_FINANCE: APIEndpoints(
            base_url="https://query1.finance.yahoo.com",
            rate_limit_requests=2000,  # Generous limit
            rate_limit_period=3600,  # Per hour
            timeout=15,
            max_retries=2
        ),
        APIProvider.POLYGON: APIEndpoints(
            base_url="https://api.polygon.io",
            rate_limit_requests=5,  # Free tier: 5 requests/minute
            rate_limit_period=60,
            timeout=30,
            max_retries=3
        )
    }
    
    def __init__(self):
        """Initialize API configuration."""
        self._credentials = {}
        self._endpoints = {}
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from environment variables."""
        logger.info("Loading API configuration from environment")
        
        # Load API credentials from environment
        self._credentials = {
            APIProvider.TWELVEDATA: APICredentials(
                api_key=os.getenv('TWELVEDATA_API_KEY'),
                sandbox=os.getenv('TWELVEDATA_SANDBOX', 'false').lower() == 'true'
            ),
            APIProvider.BINANCE: APICredentials(
                api_key=os.getenv('BINANCE_API_KEY'),
                secret_key=os.getenv('BINANCE_SECRET_KEY'),
                sandbox=os.getenv('BINANCE_SANDBOX', 'false').lower() == 'true'
            ),
            APIProvider.ALPHA_VANTAGE: APICredentials(
                api_key=os.getenv('ALPHA_VANTAGE_API_KEY')
            ),
            APIProvider.POLYGON: APICredentials(
                api_key=os.getenv('POLYGON_API_KEY')
            )
        }
        
        # Load custom endpoint configurations if provided
        self._endpoints = self.DEFAULT_CONFIGS.copy()
        
        # Override with custom configurations if environment variables are set
        for provider in APIProvider:
            env_prefix = f"{provider.value.upper()}_"
            
            # Check for custom rate limits
            rate_limit_key = f"{env_prefix}RATE_LIMIT_REQUESTS"
            if os.getenv(rate_limit_key):
                try:
                    custom_rate_limit = int(os.getenv(rate_limit_key))
                    self._endpoints[provider].rate_limit_requests = custom_rate_limit
                    logger.info(f"Custom rate limit for {provider.value}: {custom_rate_limit}")
                except ValueError:
                    logger.warning(f"Invalid rate limit value for {provider.value}")
            
            # Check for custom timeout
            timeout_key = f"{env_prefix}TIMEOUT"
            if os.getenv(timeout_key):
                try:
                    custom_timeout = int(os.getenv(timeout_key))
                    self._endpoints[provider].timeout = custom_timeout
                    logger.info(f"Custom timeout for {provider.value}: {custom_timeout}")
                except ValueError:
                    logger.warning(f"Invalid timeout value for {provider.value}")
    
    def get_credentials(self, provider: APIProvider) -> APICredentials:
        """
        Get API credentials for a provider.
        
        Args:
            provider: API provider
            
        Returns:
            APICredentials object
        """
        return self._credentials.get(provider, APICredentials())
    
    def get_endpoints(self, provider: APIProvider) -> APIEndpoints:
        """
        Get API endpoints configuration for a provider.
        
        Args:
            provider: API provider
            
        Returns:
            APIEndpoints object
        """
        return self._endpoints.get(provider, APIEndpoints(base_url=""))
    
    def has_valid_credentials(self, provider: APIProvider) -> bool:
        """
        Check if valid credentials exist for a provider.
        
        Args:
            provider: API provider
            
        Returns:
            bool: True if valid credentials exist
        """
        creds = self.get_credentials(provider)
        
        # Different providers require different credential types
        if provider in [APIProvider.TWELVEDATA, APIProvider.ALPHA_VANTAGE, APIProvider.POLYGON]:
            return creds.api_key is not None and len(creds.api_key.strip()) > 0
        elif provider == APIProvider.BINANCE:
            return (creds.api_key is not None and len(creds.api_key.strip()) > 0 and
                    creds.secret_key is not None and len(creds.secret_key.strip()) > 0)
        elif provider == APIProvider.YAHOO_FINANCE:
            return True  # No credentials required
        else:
            return False
    
    def get_provider_config(self, provider: APIProvider) -> Dict[str, Any]:
        """
        Get complete configuration for a provider.
        
        Args:
            provider: API provider
            
        Returns:
            Dict containing credentials and endpoints
        """
        return {
            'provider': provider.value,
            'credentials': self.get_credentials(provider),
            'endpoints': self.get_endpoints(provider),
            'has_valid_credentials': self.has_valid_credentials(provider)
        }
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get configuration for all providers.
        
        Returns:
            Dict mapping provider names to their configurations
        """
        return {
            provider.value: self.get_provider_config(provider)
            for provider in APIProvider
        }
    
    def validate_all_credentials(self) -> Dict[str, bool]:
        """
        Validate credentials for all providers.
        
        Returns:
            Dict mapping provider names to validation status
        """
        validation_results = {}
        
        for provider in APIProvider:
            is_valid = self.has_valid_credentials(provider)
            validation_results[provider.value] = is_valid
            
            if is_valid:
                logger.info(f"✅ {provider.value} credentials are valid")
            else:
                logger.warning(f"❌ {provider.value} credentials are missing or invalid")
        
        return validation_results
    
    def get_ccxt_exchange_config(self, exchange_name: str) -> Dict[str, Any]:
        """
        Get CCXT exchange configuration.
        
        Args:
            exchange_name: Name of the exchange (e.g., 'binance', 'coinbase')
            
        Returns:
            Dict containing CCXT exchange configuration
        """
        # Map exchange names to our API providers
        exchange_mapping = {
            'binance': APIProvider.BINANCE,
            'binanceus': APIProvider.BINANCE,
        }
        
        provider = exchange_mapping.get(exchange_name.lower())
        if not provider:
            logger.warning(f"No configuration mapping for exchange: {exchange_name}")
            return {}
        
        creds = self.get_credentials(provider)
        endpoints = self.get_endpoints(provider)
        
        config = {
            'apiKey': creds.api_key,
            'secret': creds.secret_key,
            'sandbox': creds.sandbox,
            'timeout': endpoints.timeout * 1000,  # CCXT expects milliseconds
            'rateLimit': int(60000 / endpoints.rate_limit_requests),  # ms between requests
            'enableRateLimit': True,
        }
        
        # Remove None values
        return {k: v for k, v in config.items() if v is not None}


# Global API configuration instance
api_config = APIConfig()


def get_api_config() -> APIConfig:
    """Get the global API configuration instance."""
    return api_config


def reload_api_config() -> APIConfig:
    """Reload API configuration from environment."""
    global api_config
    api_config = APIConfig()
    return api_config
