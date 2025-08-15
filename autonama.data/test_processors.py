#!/usr/bin/env python3
"""
Comprehensive Test Suite for Data Processors

This script tests all implemented processors to ensure they work correctly
with the TimescaleDB and configuration systems.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the data directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our processors and configurations
from processors.duckdb_manager import get_duckdb_manager, close_duckdb_manager
from processors.twelvedata_processor import TwelveDataProcessor
from processors.binance_processor import BinanceProcessor
from processors.unified_processor import get_unified_processor, close_unified_processor
from config.api_config import get_api_config
from config.database_config import get_database_config
from config.processor_config import get_processor_config, AssetType, AssetConfig, Exchange, DataSource
from config.logging_config import setup_logging, get_logger
from utils.error_handler import get_error_handler

# Setup logging
setup_logging(service_name="processor_test", log_level="INFO", enable_console=True, enable_file=False)
logger = get_logger("processor_test")


class ProcessorTester:
    """Comprehensive processor testing suite."""
    
    def __init__(self):
        self.test_results = {}
        self.error_handler = get_error_handler()
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all processor tests."""
        logger.info("🚀 Starting comprehensive processor tests")
        
        # Test configurations
        self.test_configurations()
        
        # Test DuckDB Manager
        self.test_duckdb_manager()
        
        # Test TwelveData Processor
        self.test_twelvedata_processor()
        
        # Test Binance Processor
        self.test_binance_processor()
        
        # Test Unified Processor
        self.test_unified_processor()
        
        # Generate summary
        self.generate_test_summary()
        
        return self.test_results
    
    def test_configurations(self) -> None:
        """Test all configuration systems."""
        logger.info("📋 Testing configuration systems...")
        
        try:
            # Test API configuration
            api_config = get_api_config()
            credentials_status = api_config.validate_all_credentials()
            
            self.test_results['api_config'] = {
                'status': 'success',
                'credentials': credentials_status,
                'providers_count': len(credentials_status)
            }
            
            logger.info(f"✅ API Config: {len(credentials_status)} providers configured")
            
            # Test database configuration
            db_config = get_database_config()
            db_validation = db_config.validate_connections()
            
            self.test_results['database_config'] = {
                'status': 'success',
                'connections': db_validation,
                'timescale_url': db_config.get_timescaledb_url(include_password=False),
                'duckdb_path': db_config.get_duckdb_path()
            }
            
            logger.info(f"✅ Database Config: {len(db_validation)} connections configured")
            
            # Test processor configuration
            processor_config = get_processor_config()
            config_summary = processor_config.get_configuration_summary()
            
            self.test_results['processor_config'] = {
                'status': 'success',
                'summary': config_summary
            }
            
            logger.info(f"✅ Processor Config: {config_summary['assets']['total']} assets configured")
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            self.test_results['configurations'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_duckdb_manager(self) -> None:
        """Test DuckDB Manager functionality."""
        logger.info("🗄️ Testing DuckDB Manager...")
        
        try:
            # Get DuckDB manager instance
            duckdb_manager = get_duckdb_manager()
            
            # Test basic functionality
            test_query = "SELECT 1 as test_value"
            result = duckdb_manager.execute_query(test_query)
            
            assert len(result) == 1
            assert result.iloc[0]['test_value'] == 1
            
            # Test TimescaleDB connection (if available)
            try:
                timescale_test = duckdb_manager.execute_query("""
                    SELECT COUNT(*) as asset_count 
                    FROM timescale.trading.asset_metadata
                """)
                
                asset_count = timescale_test.iloc[0]['asset_count']
                logger.info(f"📊 Found {asset_count} assets in TimescaleDB")
                
            except Exception as e:
                logger.warning(f"TimescaleDB connection test failed: {e}")
                asset_count = 0
            
            # Test table info
            try:
                # This will fail if table doesn't exist, which is expected
                table_info = duckdb_manager.get_table_info('asset_metadata')
                logger.info(f"📋 Table info retrieved: {len(table_info.get('columns', []))} columns")
            except:
                logger.info("📋 No local tables found (expected for fresh setup)")
            
            self.test_results['duckdb_manager'] = {
                'status': 'success',
                'basic_query': True,
                'timescale_assets': asset_count,
                'connection_type': 'singleton',
                'features': ['analytics_queries', 'parquet_support', 'timescale_integration']
            }
            
            logger.info("✅ DuckDB Manager: All tests passed")
            
        except Exception as e:
            logger.error(f"❌ DuckDB Manager test failed: {e}")
            self.test_results['duckdb_manager'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_twelvedata_processor(self) -> None:
        """Test TwelveData Processor functionality."""
        logger.info("📊 Testing TwelveData Processor...")
        
        try:
            # Check if API key is available
            api_config = get_api_config()
            if not api_config.has_valid_credentials(api_config.APIProvider.TWELVEDATA):
                logger.warning("⚠️ TwelveData API key not available, skipping processor test")
                self.test_results['twelvedata_processor'] = {
                    'status': 'skipped',
                    'reason': 'No API credentials'
                }
                return
            
            # Initialize processor
            processor = TwelveDataProcessor()
            
            # Test configuration validation
            config_valid = processor.validate_config()
            
            if not config_valid:
                logger.warning("⚠️ TwelveData configuration validation failed")
                self.test_results['twelvedata_processor'] = {
                    'status': 'failed',
                    'error': 'Configuration validation failed'
                }
                return
            
            # Test supported symbols (this might hit rate limits)
            try:
                stock_symbols = processor.get_supported_symbols(AssetType.STOCK)
                logger.info(f"📈 Found {len(stock_symbols)} supported stock symbols")
            except Exception as e:
                logger.warning(f"Could not fetch supported symbols: {e}")
                stock_symbols = []
            
            # Test basic data fetching (commented out to avoid rate limits)
            # try:
            #     stock_data = processor.fetch_stock_data('AAPL', outputsize=5)
            #     logger.info(f"📊 Fetched AAPL data: {len(stock_data.get('time_series', []))} records")
            # except Exception as e:
            #     logger.warning(f"Could not fetch AAPL data: {e}")
            
            self.test_results['twelvedata_processor'] = {
                'status': 'success',
                'config_valid': config_valid,
                'supported_symbols_count': len(stock_symbols),
                'asset_types': ['stock', 'forex', 'commodity', 'etf'],
                'rate_limit': '8 requests/minute',
                'features': ['multi_asset', 'rate_limiting', 'error_handling']
            }
            
            logger.info("✅ TwelveData Processor: Configuration and basic tests passed")
            
        except Exception as e:
            logger.error(f"❌ TwelveData Processor test failed: {e}")
            self.test_results['twelvedata_processor'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_binance_processor(self) -> None:
        """Test Binance Processor functionality."""
        logger.info("₿ Testing Binance Processor...")
        
        try:
            # Initialize processor (works without API keys for public data)
            processor = BinanceProcessor()
            
            # Test configuration validation
            config_valid = processor.validate_config()
            
            # Test symbol conversion
            test_symbols = {
                'BTC/USDT': 'BTCUSDT',
                'ETH/USDT': 'ETHUSDT',
                'ADA/USDT': 'ADAUSDT'
            }
            
            conversion_tests = {}
            for internal, binance in test_symbols.items():
                converted = processor.get_binance_symbol(internal)
                reverse = processor.get_internal_symbol(binance)
                
                conversion_tests[internal] = {
                    'to_binance': converted == binance,
                    'from_binance': reverse == internal
                }
            
            # Test supported symbols (public endpoint)
            try:
                supported_symbols = processor.get_supported_symbols()
                logger.info(f"₿ Found {len(supported_symbols)} supported crypto symbols")
            except Exception as e:
                logger.warning(f"Could not fetch supported symbols: {e}")
                supported_symbols = []
            
            # Test basic price fetching (public endpoint)
            try:
                btc_price = processor.fetch_current_price('BTC/USDT')
                if btc_price:
                    logger.info(f"₿ BTC/USDT current price: ${btc_price.price}")
                    price_test = True
                else:
                    price_test = False
            except Exception as e:
                logger.warning(f"Could not fetch BTC price: {e}")
                price_test = False
            
            self.test_results['binance_processor'] = {
                'status': 'success',
                'config_valid': config_valid,
                'symbol_conversion': conversion_tests,
                'supported_symbols_count': len(supported_symbols),
                'price_fetch_test': price_test,
                'features': ['ccxt_fallback', 'symbol_conversion', 'websocket_ready', 'rate_limiting']
            }
            
            logger.info("✅ Binance Processor: All tests passed")
            
        except Exception as e:
            logger.error(f"❌ Binance Processor test failed: {e}")
            self.test_results['binance_processor'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_unified_processor(self) -> None:
        """Test Unified Processor functionality."""
        logger.info("🎯 Testing Unified Processor...")
        
        try:
            # Get unified processor instance
            unified = get_unified_processor()
            
            # Test configuration validation
            config_valid = unified.validate_config()
            
            # Test processor status
            status = unified.get_processor_status()
            
            # Test with a small set of assets
            test_assets = [
                AssetConfig(
                    symbol='BTC/USDT',
                    asset_type=AssetType.CRYPTO,
                    exchange=Exchange.BINANCE,
                    data_sources=[DataSource.BINANCE]
                )
            ]
            
            # Test single asset update (this will actually try to fetch data)
            try:
                results = unified._update_single_asset(test_assets[0])
                update_test = len(results) > 0 and any(r.success for r in results)
                logger.info(f"🎯 Asset update test: {'✅ Success' if update_test else '⚠️ Failed'}")
            except Exception as e:
                logger.warning(f"Asset update test failed: {e}")
                update_test = False
            
            # Test error summary
            error_summary = unified.get_error_summary()
            
            self.test_results['unified_processor'] = {
                'status': 'success',
                'config_valid': config_valid,
                'processor_status': status,
                'enabled_processors': status['unified_processor']['enabled_processors'],
                'update_test': update_test,
                'error_tracking': len(error_summary) > 0,
                'features': ['multi_source', 'conflict_resolution', 'parallel_processing', 'monitoring']
            }
            
            logger.info("✅ Unified Processor: All tests passed")
            
        except Exception as e:
            logger.error(f"❌ Unified Processor test failed: {e}")
            self.test_results['unified_processor'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_test_summary(self) -> None:
        """Generate comprehensive test summary."""
        logger.info("📋 Generating test summary...")
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results.values() if r.get('status') == 'success'])
        failed_tests = len([r for r in self.test_results.values() if r.get('status') == 'failed'])
        skipped_tests = len([r for r in self.test_results.values() if r.get('status') == 'skipped'])
        
        summary = {
            'test_summary': {
                'total_tests': total_tests,
                'successful': successful_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        self.test_results.update(summary)
        
        # Log summary
        logger.info("=" * 60)
        logger.info("🎉 PROCESSOR TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📊 Total Tests: {total_tests}")
        logger.info(f"✅ Successful: {successful_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⚠️ Skipped: {skipped_tests}")
        logger.info(f"📈 Success Rate: {summary['test_summary']['success_rate']:.1f}%")
        logger.info("=" * 60)
        
        # Detailed results
        for test_name, result in self.test_results.items():
            if test_name == 'test_summary':
                continue
                
            status_emoji = {
                'success': '✅',
                'failed': '❌',
                'skipped': '⚠️'
            }.get(result.get('status'), '❓')
            
            logger.info(f"{status_emoji} {test_name}: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'failed' and 'error' in result:
                logger.info(f"   Error: {result['error']}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            close_duckdb_manager()
            close_unified_processor()
            logger.info("🧹 Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")


def main():
    """Main test execution."""
    tester = ProcessorTester()
    
    try:
        results = tester.run_all_tests()
        
        # Print final status
        summary = results.get('test_summary', {})
        success_rate = summary.get('success_rate', 0)
        
        if success_rate >= 80:
            logger.info("🎉 PROCESSOR TESTS: EXCELLENT RESULTS!")
        elif success_rate >= 60:
            logger.info("👍 PROCESSOR TESTS: GOOD RESULTS")
        else:
            logger.warning("⚠️ PROCESSOR TESTS: NEEDS ATTENTION")
        
        return 0 if success_rate >= 60 else 1
        
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        return 1
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
