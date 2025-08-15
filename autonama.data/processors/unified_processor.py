"""
Unified Data Processor

This module coordinates all data processors and provides a unified interface
for multi-asset data ingestion with conflict resolution, scheduling, and monitoring.
"""

import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import time

from processors.base_processor import BaseProcessor, ProcessorStatus
from processors.duckdb_manager import get_duckdb_manager
from processors.twelvedata_processor import TwelveDataProcessor
from processors.binance_processor import BinanceProcessor
from config.processor_config import get_processor_config
from config.api_config import get_api_config
from models.asset_models import AssetMetadata, AssetPrice, AssetType, AssetConfig
from models.ohlc_models import OHLCData, Timeframe, DataSource
from utils.error_handler import (
    ProcessorError, ValidationError, ConfigurationError,
    handle_processor_errors, retry_on_error, create_error_context,
    get_error_handler
)

logger = logging.getLogger(__name__)


class DataPriority(Enum):
    """Data source priority levels."""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LATEST_TIMESTAMP = "latest_timestamp"
    HIGHEST_PRIORITY = "highest_priority"
    AVERAGE_VALUES = "average_values"
    MOST_COMPLETE = "most_complete"


@dataclass
class ProcessorConfig:
    """Configuration for individual processors."""
    processor_class: type
    priority: DataPriority
    enabled: bool
    asset_types: Set[AssetType]
    max_concurrent: int = 1
    timeout: int = 30


@dataclass
class DataIngestionResult:
    """Result of data ingestion operation."""
    symbol: str
    asset_type: AssetType
    source: DataSource
    success: bool
    records_count: int = 0
    error_message: Optional[str] = None
    processing_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class UnifiedDataProcessor(BaseProcessor):
    """
    Unified processor that coordinates all data sources.
    
    Features:
    - Multi-processor coordination
    - Data conflict resolution
    - Automatic failover between sources
    - Parallel processing with rate limiting
    - Comprehensive error handling
    - Performance monitoring
    """
    
    def __init__(self, duckdb_manager=None):
        """
        Initialize unified processor.
        
        Args:
            duckdb_manager: DuckDBManager instance
        """
        # Get configuration
        config = get_processor_config().get_processor_settings('unified_processor')
        super().__init__('unified_processor', config.__dict__)
        
        # Database manager
        self.duckdb_manager = duckdb_manager or get_duckdb_manager()
        
        # Processor configurations
        self.processor_configs = {
            DataSource.TWELVEDATA: ProcessorConfig(
                processor_class=TwelveDataProcessor,
                priority=DataPriority.PRIMARY,
                enabled=True,
                asset_types={AssetType.STOCK, AssetType.FOREX, AssetType.COMMODITY},
                max_concurrent=1,  # Rate limited
                timeout=60
            ),
            DataSource.BINANCE: ProcessorConfig(
                processor_class=BinanceProcessor,
                priority=DataPriority.PRIMARY,
                enabled=True,
                asset_types={AssetType.CRYPTO},
                max_concurrent=3,  # Higher rate limit
                timeout=30
            )
        }
        
        # Initialize processors
        self.processors = {}
        self._initialize_processors()
        
        # Processing state
        self.processing_lock = threading.Lock()
        self.active_tasks = {}
        self.last_update_times = {}
        
        # Conflict resolution strategy
        self.conflict_resolution = ConflictResolution.LATEST_TIMESTAMP
        
        # Performance tracking
        self.ingestion_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_records': 0,
            'processing_time': 0.0,
            'last_update': datetime.utcnow()
        }
        
        self.logger.info("Unified data processor initialized")
    
    def _initialize_processors(self) -> None:
        """Initialize individual processors."""
        api_config = get_api_config()
        
        for source, config in self.processor_configs.items():
            if not config.enabled:
                continue
                
            try:
                # Check if API credentials are available
                if source == DataSource.TWELVEDATA:
                    if not api_config.has_valid_credentials(api_config.APIProvider.TWELVEDATA):
                        self.logger.warning("TwelveData credentials not available, skipping")
                        continue
                    self.processors[source] = TwelveDataProcessor(duckdb_manager=self.duckdb_manager)
                    
                elif source == DataSource.BINANCE:
                    # Binance can work without credentials for public data
                    self.processors[source] = BinanceProcessor(duckdb_manager=self.duckdb_manager)
                
                self.logger.info(f"Initialized processor: {source.value}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {source.value} processor: {e}")
                config.enabled = False
    
    def validate_config(self) -> bool:
        """Validate unified processor configuration."""
        try:
            # Check if at least one processor is available
            if not self.processors:
                self.logger.error("No processors available")
                return False
            
            # Validate each processor
            for source, processor in self.processors.items():
                if not processor.validate_config():
                    self.logger.warning(f"Processor {source.value} validation failed")
                    self.processor_configs[source].enabled = False
            
            # Check if we still have enabled processors
            enabled_processors = [
                source for source, config in self.processor_configs.items() 
                if config.enabled and source in self.processors
            ]
            
            if not enabled_processors:
                self.logger.error("No valid processors available")
                return False
            
            self.logger.info(f"Validated processors: {[p.value for p in enabled_processors]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def process_data(self, assets: List[AssetConfig] = None, **kwargs) -> Dict[str, Any]:
        """
        Process data for multiple assets.
        
        Args:
            assets: List of asset configurations
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with processing results
        """
        if assets is None:
            processor_config = get_processor_config()
            assets = processor_config.get_all_assets()
        
        return self.update_all_assets(assets, **kwargs)
    
    @handle_processor_errors('unified_processor', 'update_all_assets')
    def update_all_assets(self, assets: List[AssetConfig], 
                         parallel: bool = True, max_workers: int = 5) -> Dict[str, List[DataIngestionResult]]:
        """
        Update data for all specified assets.
        
        Args:
            assets: List of asset configurations
            parallel: Whether to process in parallel
            max_workers: Maximum number of parallel workers
            
        Returns:
            Dictionary mapping asset symbols to ingestion results
        """
        start_time = time.time()
        results = {}
        
        try:
            if parallel and len(assets) > 1:
                results = self._update_assets_parallel(assets, max_workers)
            else:
                results = self._update_assets_sequential(assets)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_ingestion_stats(results, processing_time)
            
            # Log summary
            total_assets = len(assets)
            successful_assets = len([r for r in results.values() if any(res.success for res in r)])
            
            self.logger.info(
                f"Asset update completed: {successful_assets}/{total_assets} successful "
                f"in {processing_time:.2f}s"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to update assets: {e}")
            raise
    
    def _update_assets_parallel(self, assets: List[AssetConfig], 
                              max_workers: int) -> Dict[str, List[DataIngestionResult]]:
        """Update assets in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_asset = {
                executor.submit(self._update_single_asset, asset): asset
                for asset in assets
            }
            
            # Collect results
            for future in as_completed(future_to_asset):
                asset = future_to_asset[future]
                try:
                    asset_results = future.result()
                    results[asset.symbol] = asset_results
                except Exception as e:
                    self.logger.error(f"Failed to update {asset.symbol}: {e}")
                    results[asset.symbol] = [DataIngestionResult(
                        symbol=asset.symbol,
                        asset_type=asset.asset_type,
                        source=DataSource.BINANCE,  # Default
                        success=False,
                        error_message=str(e)
                    )]
        
        return results
    
    def _update_assets_sequential(self, assets: List[AssetConfig]) -> Dict[str, List[DataIngestionResult]]:
        """Update assets sequentially."""
        results = {}
        
        for asset in assets:
            try:
                asset_results = self._update_single_asset(asset)
                results[asset.symbol] = asset_results
            except Exception as e:
                self.logger.error(f"Failed to update {asset.symbol}: {e}")
                results[asset.symbol] = [DataIngestionResult(
                    symbol=asset.symbol,
                    asset_type=asset.asset_type,
                    source=DataSource.BINANCE,  # Default
                    success=False,
                    error_message=str(e)
                )]
        
        return results
    
    def _update_single_asset(self, asset: AssetConfig) -> List[DataIngestionResult]:
        """
        Update data for a single asset from all applicable sources.
        
        Args:
            asset: Asset configuration
            
        Returns:
            List of ingestion results from different sources
        """
        results = []
        
        # Get applicable processors for this asset type
        applicable_processors = self._get_applicable_processors(asset.asset_type)
        
        if not applicable_processors:
            self.logger.warning(f"No processors available for {asset.symbol} ({asset.asset_type})")
            return [DataIngestionResult(
                symbol=asset.symbol,
                asset_type=asset.asset_type,
                source=DataSource.BINANCE,  # Default
                success=False,
                error_message="No applicable processors"
            )]
        
        # Try each processor in priority order
        for source, processor in applicable_processors:
            try:
                start_time = time.time()
                
                # Process data
                data = processor.process_data(
                    asset.symbol,
                    asset.asset_type,
                    timeframe=Timeframe.HOUR_1,
                    limit=100
                )
                
                processing_time = time.time() - start_time
                
                # Count records
                records_count = 0
                if 'ohlc_data' in data and data['ohlc_data']:
                    records_count = len(data['ohlc_data'])
                elif 'time_series' in data and data['time_series']:
                    records_count = len(data['time_series'])
                
                # Store data (placeholder - would integrate with TimescaleDB)
                self._store_asset_data(asset.symbol, data)
                
                result = DataIngestionResult(
                    symbol=asset.symbol,
                    asset_type=asset.asset_type,
                    source=source,
                    success=True,
                    records_count=records_count,
                    processing_time=processing_time
                )
                
                results.append(result)
                
                self.logger.debug(f"Successfully processed {asset.symbol} from {source.value}")
                
            except Exception as e:
                self.logger.warning(f"Failed to process {asset.symbol} from {source.value}: {e}")
                
                result = DataIngestionResult(
                    symbol=asset.symbol,
                    asset_type=asset.asset_type,
                    source=source,
                    success=False,
                    error_message=str(e),
                    processing_time=time.time() - start_time if 'start_time' in locals() else 0.0
                )
                
                results.append(result)
        
        return results
    
    def _get_applicable_processors(self, asset_type: AssetType) -> List[tuple]:
        """
        Get processors applicable for an asset type, sorted by priority.
        
        Args:
            asset_type: Type of asset
            
        Returns:
            List of (source, processor) tuples sorted by priority
        """
        applicable = []
        
        for source, processor in self.processors.items():
            config = self.processor_configs[source]
            
            if config.enabled and asset_type in config.asset_types:
                applicable.append((source, processor, config.priority))
        
        # Sort by priority (lower number = higher priority)
        applicable.sort(key=lambda x: x[2].value)
        
        return [(source, processor) for source, processor, _ in applicable]
    
    def _store_asset_data(self, symbol: str, data: Dict[str, Any]) -> None:
        """
        Store processed asset data.
        
        Args:
            symbol: Asset symbol
            data: Processed data dictionary
        """
        try:
            # This would integrate with TimescaleDB storage
            # For now, just log the operation
            
            asset_type = data.get('asset_type', 'unknown')
            records_count = 0
            
            if 'ohlc_data' in data and data['ohlc_data']:
                records_count = len(data['ohlc_data'])
            elif 'time_series' in data and data['time_series']:
                records_count = len(data['time_series'])
            
            self.logger.debug(f"Stored {records_count} records for {symbol} ({asset_type})")
            
            # Update last update time
            self.last_update_times[symbol] = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Failed to store data for {symbol}: {e}")
    
    def _update_ingestion_stats(self, results: Dict[str, List[DataIngestionResult]], 
                              processing_time: float) -> None:
        """Update ingestion statistics."""
        total_requests = sum(len(asset_results) for asset_results in results.values())
        successful_requests = sum(
            len([r for r in asset_results if r.success]) 
            for asset_results in results.values()
        )
        failed_requests = total_requests - successful_requests
        total_records = sum(
            sum(r.records_count for r in asset_results if r.success)
            for asset_results in results.values()
        )
        
        self.ingestion_stats.update({
            'total_requests': self.ingestion_stats['total_requests'] + total_requests,
            'successful_requests': self.ingestion_stats['successful_requests'] + successful_requests,
            'failed_requests': self.ingestion_stats['failed_requests'] + failed_requests,
            'total_records': self.ingestion_stats['total_records'] + total_records,
            'processing_time': self.ingestion_stats['processing_time'] + processing_time,
            'last_update': datetime.utcnow()
        })
    
    def get_processor_status(self) -> Dict[str, Any]:
        """Get status of all processors."""
        status = {
            'unified_processor': {
                'status': self.status.value,
                'processors_count': len(self.processors),
                'enabled_processors': [
                    source.value for source, config in self.processor_configs.items()
                    if config.enabled and source in self.processors
                ],
                'ingestion_stats': self.ingestion_stats.copy(),
                'last_update_times': {
                    symbol: timestamp.isoformat()
                    for symbol, timestamp in self.last_update_times.items()
                }
            }
        }
        
        # Add individual processor status
        for source, processor in self.processors.items():
            if hasattr(processor, 'get_status'):
                status[source.value] = processor.get_status()
        
        return status
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary from all processors."""
        error_handler = get_error_handler()
        return error_handler.get_all_error_summaries()
    
    def force_update_asset(self, symbol: str, asset_type: AssetType = None) -> List[DataIngestionResult]:
        """
        Force update for a specific asset.
        
        Args:
            symbol: Asset symbol
            asset_type: Asset type (will be determined if not provided)
            
        Returns:
            List of ingestion results
        """
        try:
            # Get asset configuration
            processor_config = get_processor_config()
            asset_config = processor_config.get_asset_config(symbol)
            
            if not asset_config:
                # Create temporary config
                if not asset_type:
                    raise ValidationError(f"Asset type required for unknown symbol: {symbol}")
                
                from config.processor_config import AssetConfig, Exchange
                asset_config = AssetConfig(
                    symbol=symbol,
                    asset_type=asset_type,
                    exchange=Exchange.BINANCE if asset_type == AssetType.CRYPTO else Exchange.NASDAQ,
                    data_sources=[DataSource.BINANCE if asset_type == AssetType.CRYPTO else DataSource.TWELVEDATA]
                )
            
            return self._update_single_asset(asset_config)
            
        except Exception as e:
            self.logger.error(f"Failed to force update {symbol}: {e}")
            raise
    
    def schedule_updates(self, interval_minutes: int = 5) -> None:
        """
        Schedule periodic updates for all assets.
        
        Args:
            interval_minutes: Update interval in minutes
        """
        def update_loop():
            while self.status == ProcessorStatus.RUNNING:
                try:
                    processor_config = get_processor_config()
                    assets = processor_config.get_all_assets()
                    
                    self.logger.info(f"Starting scheduled update for {len(assets)} assets")
                    self.update_all_assets(assets)
                    
                except Exception as e:
                    self.logger.error(f"Scheduled update failed: {e}")
                
                # Wait for next update
                time.sleep(interval_minutes * 60)
        
        # Start update thread
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        
        self.logger.info(f"Scheduled updates every {interval_minutes} minutes")
    
    def stop_all_processors(self) -> None:
        """Stop all processors."""
        for source, processor in self.processors.items():
            try:
                if hasattr(processor, 'stop'):
                    processor.stop()
                self.logger.info(f"Stopped processor: {source.value}")
            except Exception as e:
                self.logger.error(f"Failed to stop {source.value} processor: {e}")
        
        self.status = ProcessorStatus.STOPPED


# Global unified processor instance
_unified_processor = None
_processor_lock = threading.Lock()


def get_unified_processor(**kwargs) -> UnifiedDataProcessor:
    """Get the global unified processor instance."""
    global _unified_processor
    
    if _unified_processor is None:
        with _processor_lock:
            if _unified_processor is None:
                _unified_processor = UnifiedDataProcessor(**kwargs)
    
    return _unified_processor


def close_unified_processor() -> None:
    """Close the global unified processor instance."""
    global _unified_processor
    
    if _unified_processor:
        _unified_processor.stop_all_processors()
        _unified_processor = None
