"""
TwelveData Data Ingestion Tasks for TimescaleDB

This module implements TwelveData data ingestion tasks for stocks, forex, and commodities
using the TimescaleDB-first architecture.
"""

from celery import current_task
from celery_app import celery_app
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import time
import os

from processors.twelvedata_processor import TwelveDataProcessor, STOCK_SYMBOLS, FOREX_SYMBOLS, COMMODITY_SYMBOLS
from tasks.timescale_data_ingestion import timescale_manager, duckdb_engine

logger = logging.getLogger(__name__)

# Initialize TwelveData processor
try:
    twelvedata_processor = TwelveDataProcessor()
    logger.info("TwelveData processor initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TwelveData processor: {e}")
    twelvedata_processor = None


@celery_app.task(bind=True)
def update_stock_data_timescale(self, symbols: Optional[List[str]] = None, force_update: bool = False):
    """
    Update stock data using TwelveData API and store in TimescaleDB.
    
    Args:
        symbols: List of stock symbols to update (defaults to STOCK_SYMBOLS)
        force_update: Whether to force update even if data is recent
    """
    try:
        if not twelvedata_processor:
            raise Exception("TwelveData processor not initialized")
        
        # Use default symbols if none provided
        if symbols is None:
            symbols = STOCK_SYMBOLS[:10]  # Start with first 10 for testing
        
        logger.info(f"Starting stock data update for {len(symbols)} symbols")
        
        success_count = 0
        failed_count = 0
        total_records = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': len(symbols),
                        'symbol': symbol,
                        'status': f'Processing stock {symbol}'
                    }
                )
                
                logger.info(f"Processing stock {symbol} ({i}/{len(symbols)})")
                
                # Check if we need to update (unless forced)
                if not force_update:
                    latest_timestamp = timescale_manager.get_latest_timestamp(symbol, 'twelvedata', '1d')
                    if latest_timestamp and (datetime.utcnow() - latest_timestamp).total_seconds() < 86400:  # 24 hours
                        logger.info(f"Skipping {symbol} - data is recent")
                        continue
                
                # Fetch data from TwelveData
                result = twelvedata_processor.update_symbol_data(symbol, 'stock', force_update)
                
                if result['success'] and result['data']:
                    # Store in TimescaleDB
                    inserted_count = timescale_manager.insert_ohlc_data(
                        result['data'], symbol, 'twelvedata', '1d'
                    )
                    
                    if inserted_count > 0:
                        logger.info(f"✅ {symbol}: {inserted_count} records stored in TimescaleDB")
                        success_count += 1
                        total_records += inserted_count
                        
                        # Calculate technical indicators using DuckDB
                        indicators = duckdb_engine.calculate_technical_indicators(symbol)
                        if indicators:
                            duckdb_engine.store_indicators_to_timescale(symbol, indicators, '1d')
                            logger.info(f"Calculated and stored indicators for {symbol}")
                    else:
                        logger.warning(f"❌ {symbol}: No data inserted")
                        failed_count += 1
                else:
                    logger.warning(f"❌ {symbol}: {result.get('error', 'Unknown error')}")
                    failed_count += 1
                
                # Rate limiting delay
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing stock {symbol}: {e}")
                failed_count += 1
        
        logger.info(f"Stock data update completed: {success_count} success, {failed_count} failed, {total_records} total records")
        
        return {
            'status': 'completed',
            'category': 'stocks',
            'symbols_processed': len(symbols),
            'success_count': success_count,
            'failed_count': failed_count,
            'total_records': total_records,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Critical error in stock data update: {e}")
        raise


@celery_app.task(bind=True)
def update_forex_data_timescale(self, symbols: Optional[List[str]] = None, force_update: bool = False):
    """
    Update forex data using TwelveData API and store in TimescaleDB.
    
    Args:
        symbols: List of forex pairs to update (defaults to FOREX_SYMBOLS)
        force_update: Whether to force update even if data is recent
    """
    try:
        if not twelvedata_processor:
            raise Exception("TwelveData processor not initialized")
        
        # Use default symbols if none provided
        if symbols is None:
            symbols = FOREX_SYMBOLS[:10]  # Start with first 10 for testing
        
        logger.info(f"Starting forex data update for {len(symbols)} pairs")
        
        success_count = 0
        failed_count = 0
        total_records = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': len(symbols),
                        'symbol': symbol,
                        'status': f'Processing forex {symbol}'
                    }
                )
                
                logger.info(f"Processing forex {symbol} ({i}/{len(symbols)})")
                
                # Check if we need to update (unless forced)
                if not force_update:
                    latest_timestamp = timescale_manager.get_latest_timestamp(symbol, 'twelvedata', '1d')
                    if latest_timestamp and (datetime.utcnow() - latest_timestamp).total_seconds() < 86400:  # 24 hours
                        logger.info(f"Skipping {symbol} - data is recent")
                        continue
                
                # Fetch data from TwelveData
                result = twelvedata_processor.update_symbol_data(symbol, 'forex', force_update)
                
                if result['success'] and result['data']:
                    # Store in TimescaleDB
                    inserted_count = timescale_manager.insert_ohlc_data(
                        result['data'], symbol, 'twelvedata', '1d'
                    )
                    
                    if inserted_count > 0:
                        logger.info(f"✅ {symbol}: {inserted_count} records stored in TimescaleDB")
                        success_count += 1
                        total_records += inserted_count
                        
                        # Calculate technical indicators using DuckDB
                        indicators = duckdb_engine.calculate_technical_indicators(symbol)
                        if indicators:
                            duckdb_engine.store_indicators_to_timescale(symbol, indicators, '1d')
                            logger.info(f"Calculated and stored indicators for {symbol}")
                    else:
                        logger.warning(f"❌ {symbol}: No data inserted")
                        failed_count += 1
                else:
                    logger.warning(f"❌ {symbol}: {result.get('error', 'Unknown error')}")
                    failed_count += 1
                
                # Rate limiting delay
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing forex {symbol}: {e}")
                failed_count += 1
        
        logger.info(f"Forex data update completed: {success_count} success, {failed_count} failed, {total_records} total records")
        
        return {
            'status': 'completed',
            'category': 'forex',
            'symbols_processed': len(symbols),
            'success_count': success_count,
            'failed_count': failed_count,
            'total_records': total_records,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Critical error in forex data update: {e}")
        raise


@celery_app.task(bind=True)
def update_commodity_data_timescale(self, symbols: Optional[List[str]] = None, force_update: bool = False):
    """
    Update commodity data using TwelveData API and store in TimescaleDB.
    
    Args:
        symbols: List of commodity symbols to update (defaults to COMMODITY_SYMBOLS)
        force_update: Whether to force update even if data is recent
    """
    try:
        if not twelvedata_processor:
            raise Exception("TwelveData processor not initialized")
        
        # Use default symbols if none provided
        if symbols is None:
            symbols = COMMODITY_SYMBOLS[:10]  # Start with first 10 for testing
        
        logger.info(f"Starting commodity data update for {len(symbols)} symbols")
        
        success_count = 0
        failed_count = 0
        total_records = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Update task progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i,
                        'total': len(symbols),
                        'symbol': symbol,
                        'status': f'Processing commodity {symbol}'
                    }
                )
                
                logger.info(f"Processing commodity {symbol} ({i}/{len(symbols)})")
                
                # Check if we need to update (unless forced)
                if not force_update:
                    latest_timestamp = timescale_manager.get_latest_timestamp(symbol, 'twelvedata', '1d')
                    if latest_timestamp and (datetime.utcnow() - latest_timestamp).total_seconds() < 86400:  # 24 hours
                        logger.info(f"Skipping {symbol} - data is recent")
                        continue
                
                # Fetch data from TwelveData
                result = twelvedata_processor.update_symbol_data(symbol, 'commodity', force_update)
                
                if result['success'] and result['data']:
                    # Store in TimescaleDB
                    inserted_count = timescale_manager.insert_ohlc_data(
                        result['data'], symbol, 'twelvedata', '1d'
                    )
                    
                    if inserted_count > 0:
                        logger.info(f"✅ {symbol}: {inserted_count} records stored in TimescaleDB")
                        success_count += 1
                        total_records += inserted_count
                        
                        # Calculate technical indicators using DuckDB
                        indicators = duckdb_engine.calculate_technical_indicators(symbol)
                        if indicators:
                            duckdb_engine.store_indicators_to_timescale(symbol, indicators, '1d')
                            logger.info(f"Calculated and stored indicators for {symbol}")
                    else:
                        logger.warning(f"❌ {symbol}: No data inserted")
                        failed_count += 1
                else:
                    logger.warning(f"❌ {symbol}: {result.get('error', 'Unknown error')}")
                    failed_count += 1
                
                # Rate limiting delay
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing commodity {symbol}: {e}")
                failed_count += 1
        
        logger.info(f"Commodity data update completed: {success_count} success, {failed_count} failed, {total_records} total records")
        
        return {
            'status': 'completed',
            'category': 'commodities',
            'symbols_processed': len(symbols),
            'success_count': success_count,
            'failed_count': failed_count,
            'total_records': total_records,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Critical error in commodity data update: {e}")
        raise


@celery_app.task(bind=True)
def update_all_twelvedata_assets(self, force_update: bool = False):
    """
    Update all TwelveData assets (stocks, forex, commodities).
    
    Args:
        force_update: Whether to force update all data
    """
    try:
        logger.info("Starting comprehensive TwelveData asset update")
        
        all_results = {}
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 3,
                'status': 'Starting multi-asset update'
            }
        )
        
        # Update stocks
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': 1,
                'total': 3,
                'status': 'Updating stocks data'
            }
        )
        
        stock_result = update_stock_data_timescale.apply(args=[None, force_update]).get()
        all_results['stocks'] = stock_result
        
        # Update forex
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': 2,
                'total': 3,
                'status': 'Updating forex data'
            }
        )
        
        forex_result = update_forex_data_timescale.apply(args=[None, force_update]).get()
        all_results['forex'] = forex_result
        
        # Update commodities
        current_task.update_state(
            state='PROGRESS',
            meta={
                'current': 3,
                'total': 3,
                'status': 'Updating commodities data'
            }
        )
        
        commodity_result = update_commodity_data_timescale.apply(args=[None, force_update]).get()
        all_results['commodities'] = commodity_result
        
        # Calculate totals
        total_success = sum(result.get('success_count', 0) for result in all_results.values())
        total_failed = sum(result.get('failed_count', 0) for result in all_results.values())
        total_records = sum(result.get('total_records', 0) for result in all_results.values())
        
        logger.info(f"TwelveData multi-asset update completed: {total_success} success, {total_failed} failed, {total_records} total records")
        
        return {
            'status': 'completed',
            'approach': 'twelvedata_multi_asset',
            'total_success': total_success,
            'total_failed': total_failed,
            'total_records': total_records,
            'details': all_results,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Critical error in TwelveData multi-asset update: {e}")
        raise


def test_twelvedata_connection():
    """Test TwelveData API connection and basic functionality."""
    try:
        if not twelvedata_processor:
            return {
                'status': 'failed',
                'error': 'TwelveData processor not initialized'
            }
        
        logger.info("Testing TwelveData connection...")
        
        # Test stock data
        stock_result = twelvedata_processor.update_symbol_data('AAPL', 'stock')
        
        # Test forex data
        forex_result = twelvedata_processor.update_symbol_data('EUR/USD', 'forex')
        
        # Test commodity data
        commodity_result = twelvedata_processor.update_symbol_data('XAU/USD', 'commodity')
        
        results = {
            'stock_test': stock_result,
            'forex_test': forex_result,
            'commodity_test': commodity_result
        }
        
        success_count = sum(1 for result in results.values() if result.get('success', False))
        
        logger.info(f"TwelveData connection test completed: {success_count}/3 tests passed")
        
        return {
            'status': 'completed',
            'tests_passed': success_count,
            'total_tests': 3,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"TwelveData connection test failed: {e}")
        return {
            'status': 'failed',
            'error': str(e)
        }