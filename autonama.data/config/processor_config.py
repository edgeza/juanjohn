"""
Processor Configuration

Configuration management for data processors.
Handles API keys, rate limits, and processor-specific settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int
    burst_limit: Optional[int] = None
    backoff_factor: float = 2.0
    max_retries: int = 3

@dataclass
class ProcessorConfig:
    """Base processor configuration"""
    name: str
    enabled: bool = True
    timeout_seconds: int = 30
    rate_limit: Optional[RateLimitConfig] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    extra_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}

class ProcessorConfigManager:
    """Manages processor configurations"""
    
    def __init__(self):
        self.configs = self._load_configurations()
    
    def _load_configurations(self) -> Dict[str, ProcessorConfig]:
        """Load all processor configurations"""
        configs = {}
        
        # TwelveData Processor Configuration
        configs['twelvedata'] = ProcessorConfig(
            name='twelvedata',
            enabled=os.getenv('TWELVEDATA_ENABLED', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('TWELVEDATA_TIMEOUT', '30')),
            rate_limit=RateLimitConfig(
                requests_per_minute=int(os.getenv('TWELVEDATA_RATE_LIMIT', '8')),
                burst_limit=int(os.getenv('TWELVEDATA_BURST_LIMIT', '12')),
                backoff_factor=float(os.getenv('TWELVEDATA_BACKOFF_FACTOR', '2.0')),
                max_retries=int(os.getenv('TWELVEDATA_MAX_RETRIES', '3'))
            ),
            api_key=os.getenv('TWELVEDATA_API_KEY'),
            base_url=os.getenv('TWELVEDATA_BASE_URL', 'https://api.twelvedata.com'),
            extra_config={
                'supported_assets': ['stocks', 'forex', 'commodities', 'etf'],
                'default_interval': '1min',
                'max_data_points': 5000
            }
        )
        
        # Binance Processor Configuration
        configs['binance'] = ProcessorConfig(
            name='binance',
            enabled=os.getenv('BINANCE_ENABLED', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('BINANCE_TIMEOUT', '30')),
            rate_limit=RateLimitConfig(
                requests_per_minute=int(os.getenv('BINANCE_RATE_LIMIT', '1200')),
                burst_limit=int(os.getenv('BINANCE_BURST_LIMIT', '1500')),
                backoff_factor=float(os.getenv('BINANCE_BACKOFF_FACTOR', '1.5')),
                max_retries=int(os.getenv('BINANCE_MAX_RETRIES', '3'))
            ),
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET'),
            base_url=os.getenv('BINANCE_BASE_URL', 'https://api.binance.com'),
            extra_config={
                'supported_assets': ['crypto'],
                'default_interval': '1m',
                'max_data_points': 1000,
                'testnet': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
            }
        )
        
        # CCXT Processor Configuration
        configs['ccxt'] = ProcessorConfig(
            name='ccxt',
            enabled=os.getenv('CCXT_ENABLED', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('CCXT_TIMEOUT', '30')),
            rate_limit=RateLimitConfig(
                requests_per_minute=int(os.getenv('CCXT_RATE_LIMIT', '60')),
                burst_limit=int(os.getenv('CCXT_BURST_LIMIT', '100')),
                backoff_factor=float(os.getenv('CCXT_BACKOFF_FACTOR', '2.0')),
                max_retries=int(os.getenv('CCXT_MAX_RETRIES', '3'))
            ),
            extra_config={
                'supported_exchanges': ['binance', 'coinbase', 'kraken', 'bitfinex'],
                'default_exchange': 'binance',
                'sandbox_mode': os.getenv('CCXT_SANDBOX', 'false').lower() == 'true'
            }
        )
        
        # DuckDB Manager Configuration - REMOVED: No longer needed
        # configs['duckdb'] = ProcessorConfig(
        #     name='duckdb',
        #     enabled=os.getenv('DUCKDB_ENABLED', 'true').lower() == 'true',
        #     timeout_seconds=int(os.getenv('DUCKDB_TIMEOUT', '60')),
        #     extra_config={
        #         'database_path': os.getenv('DUCKDB_PATH', '/tmp/autonama_analytics.duckdb'),
        #         'memory_limit': os.getenv('DUCKDB_MEMORY_LIMIT', '2GB'),
        #         'threads': int(os.getenv('DUCKDB_THREADS', '4')),
        #         'parquet_path': os.getenv('PARQUET_PATH', '/data/parquet'),
        #         'extensions': ['postgres_scanner', 'parquet', 'httpfs']
        #     }
        # )
        
        # Unified Processor Configuration
        configs['unified'] = ProcessorConfig(
            name='unified',
            enabled=os.getenv('UNIFIED_PROCESSOR_ENABLED', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('UNIFIED_PROCESSOR_TIMEOUT', '120')),
            extra_config={
                'max_concurrent_assets': int(os.getenv('MAX_CONCURRENT_ASSETS', '10')),
                'retry_failed_assets': os.getenv('RETRY_FAILED_ASSETS', 'true').lower() == 'true',
                'priority_processing': os.getenv('PRIORITY_PROCESSING', 'true').lower() == 'true',
                'fallback_enabled': os.getenv('FALLBACK_ENABLED', 'true').lower() == 'true'
            }
        )
        

        
        return configs
    
    def get_config(self, processor_name: str) -> Optional[ProcessorConfig]:
        """Get configuration for a specific processor"""
        return self.configs.get(processor_name)
    
    def is_enabled(self, processor_name: str) -> bool:
        """Check if a processor is enabled"""
        config = self.get_config(processor_name)
        return config.enabled if config else False
    
    def get_rate_limit(self, processor_name: str) -> Optional[RateLimitConfig]:
        """Get rate limit configuration for a processor"""
        config = self.get_config(processor_name)
        return config.rate_limit if config else None
    
    def get_api_credentials(self, processor_name: str) -> Dict[str, Optional[str]]:
        """Get API credentials for a processor"""
        config = self.get_config(processor_name)
        if not config:
            return {}
        
        return {
            'api_key': config.api_key,
            'api_secret': config.api_secret,
            'base_url': config.base_url
        }
    
    def update_config(self, processor_name: str, updates: Dict[str, Any]):
        """Update configuration for a processor"""
        if processor_name in self.configs:
            config = self.configs[processor_name]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    config.extra_config[key] = value
    
    def get_all_configs(self) -> Dict[str, ProcessorConfig]:
        """Get all processor configurations"""
        return self.configs.copy()
    
    def validate_configurations(self) -> Dict[str, Any]:
        """Validate all processor configurations"""
        validation_results = {}
        
        for name, config in self.configs.items():
            results = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check if processor is enabled but missing required config
            if config.enabled:
                if name in ['twelvedata', 'binance'] and not config.api_key:
                    results['errors'].append(f"API key required for {name}")
                    results['valid'] = False
                
                if name == 'binance' and not config.api_secret:
                    results['errors'].append(f"API secret required for {name}")
                    results['valid'] = False
                
                if config.timeout_seconds <= 0:
                    results['errors'].append(f"Invalid timeout for {name}")
                    results['valid'] = False
                
                if config.rate_limit and config.rate_limit.requests_per_minute <= 0:
                    results['errors'].append(f"Invalid rate limit for {name}")
                    results['valid'] = False
            
            # Warnings for missing optional config
            if config.enabled and name in ['twelvedata', 'binance'] and not config.base_url:
                results['warnings'].append(f"Base URL not configured for {name}, using default")
            
            validation_results[name] = results
        
        return validation_results
    
    def get_processor_settings(self, processor_name: str) -> ProcessorConfig:
        """Get processor settings (alias for get_config)"""
        config = self.get_config(processor_name)
        if not config:
            # Return a default config if not found
            return ProcessorConfig(name=processor_name, enabled=False)
        return config
    
    def get_all_assets(self) -> list:
        """Get all configured assets"""
        # Import here to avoid circular imports
        from models.asset_models import get_all_default_assets
        return get_all_default_assets()
    
    def get_asset_config(self, symbol: str):
        """Get asset configuration for a symbol"""
        # Import here to avoid circular imports
        from models.asset_models import get_all_default_assets
        all_assets = get_all_default_assets()
        for asset in all_assets:
            if asset.symbol == symbol:
                return asset
        return None

# Global configuration manager instance
config_manager = ProcessorConfigManager()

def get_processor_config(processor_name: str = None) -> ProcessorConfigManager:
    """Get processor configuration manager or specific processor config"""
    if processor_name is None:
        return config_manager
    return config_manager.get_config(processor_name)

def is_processor_enabled(processor_name: str) -> bool:
    """Check if processor is enabled"""
    return config_manager.is_enabled(processor_name)

def get_rate_limit_config(processor_name: str) -> Optional[RateLimitConfig]:
    """Get rate limit configuration"""
    return config_manager.get_rate_limit(processor_name)

def get_api_credentials(processor_name: str) -> Dict[str, Optional[str]]:
    """Get API credentials"""
    return config_manager.get_api_credentials(processor_name)

def validate_all_configs() -> Dict[str, Any]:
    """Validate all configurations"""
    return config_manager.validate_configurations()

# Configuration validation on import
if __name__ == "__main__":
    validation_results = validate_all_configs()
    
    print("Processor Configuration Validation:")
    print("=" * 50)
    
    for processor, results in validation_results.items():
        status = "✅ VALID" if results['valid'] else "❌ INVALID"
        print(f"{processor}: {status}")
        
        if results['errors']:
            for error in results['errors']:
                print(f"  ERROR: {error}")
        
        if results['warnings']:
            for warning in results['warnings']:
                print(f"  WARNING: {warning}")
        
        print()
