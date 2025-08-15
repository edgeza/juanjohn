"""
Celery App Configuration for API

This integrates Celery directly with the FastAPI application
to avoid the import issues with separate containers.
"""

import os
import sys
from celery import Celery
from src.core.config import settings

# No need to add data directory to Python path - tasks are in src.tasks

# Create Celery app
celery_app = Celery(
    "autonama_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Explicitly set task discovery to only look in src.tasks
    include=['src.tasks.autonama_optimization', 'src.tasks.multi_asset_ingestion', 'src.tasks.binance_data_fetcher'],
    # Beat schedule for scheduled tasks
    beat_schedule={
        'update-crypto-data': {
            'task': 'src.tasks.binance_data_fetcher.scheduled_crypto_update',
            'schedule': 600.0,  # Every 10 minutes (changed from 300.0)
        },
        'update-stock-data': {
            'task': 'src.tasks.multi_asset_ingestion.scheduled_stock_update',
            'schedule': 600.0,  # Every 10 minutes
        },
        'update-forex-data': {
            'task': 'src.tasks.multi_asset_ingestion.scheduled_forex_update',
            'schedule': 600.0,  # Every 10 minutes
        },
        'update-all-assets': {
            'task': 'src.tasks.binance_data_fetcher.update_all_asset_types',
            'schedule': 1800.0,  # Every 30 minutes
        },
    }
)

# Import tasks to register them
try:
    # Import data tasks - using relative imports since tasks are in the same module
    from src.tasks.autonama_optimization import run_autonama_optimization, run_single_autonama_optimization
    from src.tasks.binance_data_fetcher import (
        fetch_binance_data,
        scheduled_crypto_update,
        scheduled_stock_update, 
        scheduled_forex_update,
        update_all_asset_types
    )
    
    print("✅ Successfully imported Celery tasks")
    
except ImportError as e:
    print(f"⚠️ Could not import some Celery tasks: {e}")
    # Create dummy tasks for development
    
    @celery_app.task(bind=True)
    def run_autonama_optimization(self, **kwargs):
        """Dummy optimization task"""
        return {
            "status": "completed",
            "message": "Optimization completed (dummy)",
            "optimized_assets": 5,
            "total_return": 0.15,
            "sharpe_ratio": 1.2
        }
    
    @celery_app.task(bind=True) 
    def run_single_autonama_optimization(self, **kwargs):
        """Dummy single optimization task"""
        return {
            "status": "completed", 
            "message": f"Single optimization completed for {kwargs.get('symbol', 'UNKNOWN')}",
            "symbol": kwargs.get('symbol'),
            "total_return": 0.12,
            "sharpe_ratio": 1.1
        }

# Make tasks available for import
__all__ = ['celery_app', 'run_autonama_optimization', 'run_single_autonama_optimization']