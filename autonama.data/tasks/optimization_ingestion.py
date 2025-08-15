#!/usr/bin/env python3
"""
Optimization Data Ingestion Task

This task scans the hotbox/export_results folder for the latest optimization data
and ingests it into PostgreSQL for alerts and analytics.
"""

import os
import json
import logging
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any
from celery import shared_task
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import pandas as pd

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',  # Use localhost when running locally, 'postgres' when in Docker
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

class OptimizationDataIngestion:
    def __init__(self, db_config: Dict = None):
        """Initialize the ingestion system"""
        self.db_config = db_config or DB_CONFIG
        self.connection = None
        self.hotbox_dir = "../autonama.ingestion/hotbox/export_results"  # Local path
        
    def connect_database(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_database(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def get_latest_export_files(self) -> Dict[str, str]:
        """
        Get the most recent export files from hotbox
        
        Returns:
            Dictionary with file paths for different data types
        """
        try:
            files = {}
            
            # Find latest alerts file
            alerts_pattern = os.path.join(self.hotbox_dir, "alerts_*.json")
            alerts_files = glob.glob(alerts_pattern)
            if alerts_files:
                alerts_files.sort(key=os.path.getmtime, reverse=True)
                files['alerts'] = alerts_files[0]
                logger.info(f"Found latest alerts file: {files['alerts']}")
            
            # Find latest analytics file
            analytics_pattern = os.path.join(self.hotbox_dir, "analytics_*.json")
            analytics_files = glob.glob(analytics_pattern)
            if analytics_files:
                analytics_files.sort(key=os.path.getmtime, reverse=True)
                files['analytics'] = analytics_files[0]
                logger.info(f"Found latest analytics file: {files['analytics']}")
            
            # Find latest summary file
            summary_pattern = os.path.join(self.hotbox_dir, "summary_*.json")
            summary_files = glob.glob(summary_pattern)
            if summary_files:
                summary_files.sort(key=os.path.getmtime, reverse=True)
                files['summary'] = summary_files[0]
                logger.info(f"Found latest summary file: {files['summary']}")
            
            # Find latest plots file
            plots_pattern = os.path.join(self.hotbox_dir, "plots_data_*.json")
            plots_files = glob.glob(plots_pattern)
            if plots_files:
                plots_files.sort(key=os.path.getmtime, reverse=True)
                files['plots'] = plots_files[0]
                logger.info(f"Found latest plots file: {files['plots']}")
            
            # Find latest manifest file
            manifest_pattern = os.path.join(self.hotbox_dir, "ingestion_manifest.json")
            if os.path.exists(manifest_pattern):
                files['manifest'] = manifest_pattern
                logger.info(f"Found manifest file: {files['manifest']}")
            
            if not files:
                logger.warning(f"No export files found in {self.hotbox_dir}")
            
            return files
            
        except Exception as e:
            logger.error(f"Error finding latest export files: {e}")
            return {}
    
    def create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist"""
        try:
            cursor = self.connection.cursor()
            
            # Create alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.alerts (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    signal VARCHAR(10) NOT NULL,
                    current_price DECIMAL(20, 8),
                    potential_return DECIMAL(10, 4),
                    signal_strength DECIMAL(10, 4),
                    risk_level VARCHAR(20),
                    interval VARCHAR(10),
                    optimized_degree INTEGER,
                    optimized_kstd DECIMAL(10, 4),
                    optimized_lookback INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create asset analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.asset_analytics (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10),
                    current_price DECIMAL(20, 8),
                    lower_band DECIMAL(20, 8),
                    upper_band DECIMAL(20, 8),
                    signal VARCHAR(10),
                    potential_return DECIMAL(10, 4),
                    total_return DECIMAL(10, 4),
                    sharpe_ratio DECIMAL(10, 4),
                    max_drawdown DECIMAL(10, 4),
                    degree INTEGER,
                    kstd DECIMAL(10, 4),
                    lookback INTEGER,
                    optimized_degree INTEGER,
                    optimized_kstd DECIMAL(10, 4),
                    optimized_lookback INTEGER,
                    data_points INTEGER,
                    total_available INTEGER,
                    analysis_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create optimization summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.optimization_summary (
                    id SERIAL PRIMARY KEY,
                    analysis_date TIMESTAMP,
                    total_assets INTEGER,
                    buy_signals INTEGER,
                    sell_signals INTEGER,
                    hold_signals INTEGER,
                    avg_potential_return DECIMAL(10, 4),
                    avg_total_return DECIMAL(10, 4),
                    optimization_enabled BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create plots data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.plots_data (
                    id SERIAL PRIMARY KEY,
                    chart_type VARCHAR(50),
                    data JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.connection.rollback()
            raise
    
    def ingest_alerts(self, alerts_data: List[Dict]) -> int:
        """Ingest alerts data into the database"""
        try:
            cursor = self.connection.cursor()
            
            # Clear old alerts
            cursor.execute("DELETE FROM trading.alerts")
            
            # Prepare data for insertion
            alerts_to_insert = []
            for alert in alerts_data:
                alerts_to_insert.append((
                    alert.get('symbol'),
                    alert.get('signal'),
                    alert.get('current_price'),
                    alert.get('potential_return'),
                    alert.get('signal_strength'),
                    alert.get('risk_level'),
                    alert.get('interval'),
                    alert.get('optimized_degree'),
                    alert.get('optimized_kstd'),
                    alert.get('optimized_lookback'),
                    alert.get('timestamp')
                ))
            
            # Insert alerts
            execute_values(
                cursor,
                """
                INSERT INTO trading.alerts 
                (symbol, signal, current_price, potential_return, signal_strength, 
                 risk_level, interval, optimized_degree, optimized_kstd, optimized_lookback, timestamp)
                VALUES %s
                """,
                alerts_to_insert
            )
            
            self.connection.commit()
            logger.info(f"Ingested {len(alerts_to_insert)} alerts")
            return len(alerts_to_insert)
            
        except Exception as e:
            logger.error(f"Error ingesting alerts: {e}")
            self.connection.rollback()
            raise
    
    def ingest_asset_analytics(self, analytics_data: List[Dict]) -> int:
        """Ingest asset analytics data into the database"""
        try:
            cursor = self.connection.cursor()
            
            # Clear old analytics
            cursor.execute("DELETE FROM trading.asset_analytics")
            
            # Prepare data for insertion
            analytics_to_insert = []
            for asset in analytics_data:
                analytics_to_insert.append((
                    asset.get('symbol'),
                    asset.get('interval'),
                    asset.get('current_price'),
                    asset.get('lower_band'),
                    asset.get('upper_band'),
                    asset.get('signal'),
                    asset.get('potential_return'),
                    asset.get('total_return'),
                    asset.get('sharpe_ratio'),
                    asset.get('max_drawdown'),
                    asset.get('degree'),
                    asset.get('kstd'),
                    asset.get('lookback'),
                    asset.get('optimized_degree'),
                    asset.get('optimized_kstd'),
                    asset.get('optimized_lookback'),
                    asset.get('data_points'),
                    asset.get('total_available'),
                    asset.get('analysis_date')
                ))
            
            # Insert analytics
            execute_values(
                cursor,
                """
                INSERT INTO trading.asset_analytics 
                (symbol, interval, current_price, lower_band, upper_band, signal,
                 potential_return, total_return, sharpe_ratio, max_drawdown,
                 degree, kstd, lookback, optimized_degree, optimized_kstd,
                 optimized_lookback, data_points, total_available, analysis_date)
                VALUES %s
                """,
                analytics_to_insert
            )
            
            self.connection.commit()
            logger.info(f"Ingested {len(analytics_to_insert)} asset analytics")
            return len(analytics_to_insert)
            
        except Exception as e:
            logger.error(f"Error ingesting asset analytics: {e}")
            self.connection.rollback()
            raise
    
    def ingest_optimization_summary(self, summary_data: Dict) -> int:
        """Ingest optimization summary data into the database"""
        try:
            cursor = self.connection.cursor()
            
            # Clear old summary
            cursor.execute("DELETE FROM trading.optimization_summary")
            
            # Insert summary
            cursor.execute("""
                INSERT INTO trading.optimization_summary 
                (analysis_date, total_assets, buy_signals, sell_signals, hold_signals,
                 avg_potential_return, avg_total_return, optimization_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    summary_data.get('timestamp'),
                    summary_data.get('total_assets_analyzed'),
                    summary_data.get('analysis_summary', {}).get('buy_signals'),
                    summary_data.get('analysis_summary', {}).get('sell_signals'),
                    summary_data.get('analysis_summary', {}).get('hold_signals'),
                    summary_data.get('analysis_summary', {}).get('avg_potential_return'),
                    summary_data.get('analysis_summary', {}).get('avg_total_return'),
                    summary_data.get('optimization_enabled')
                )
            )
            
            self.connection.commit()
            logger.info("Ingested optimization summary")
            return 1
            
        except Exception as e:
            logger.error(f"Error ingesting optimization summary: {e}")
            self.connection.rollback()
            raise
    
    def ingest_plots_data(self, plots_data: Dict) -> int:
        """Ingest plots data into the database"""
        try:
            cursor = self.connection.cursor()
            
            # Clear old plots data
            cursor.execute("DELETE FROM trading.plots_data")
            
            # Insert plots data
            cursor.execute("""
                INSERT INTO trading.plots_data 
                (chart_type, data)
                VALUES (%s, %s)
                """,
                ('optimization_plots', json.dumps(plots_data))
            )
            
            self.connection.commit()
            logger.info("Ingested plots data")
            return 1
            
        except Exception as e:
            logger.error(f"Error ingesting plots data: {e}")
            self.connection.rollback()
            raise
    
    def load_json_file(self, filepath: str) -> Any:
        """Load JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {filepath}: {e}")
            raise
    
    def ingest_latest_data(self) -> Dict:
        """
        Ingest the latest optimization data
        
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Connect to database
            self.connect_database()
            
            # Create tables if they don't exist
            self.create_tables_if_not_exist()
            
            # Get latest export files
            files = self.get_latest_export_files()
            if not files:
                return {'error': 'No export files found'}
            
            results = {}
            
            # Ingest alerts
            if 'alerts' in files:
                alerts_data = self.load_json_file(files['alerts'])
                results['alerts_ingested'] = self.ingest_alerts(alerts_data)
            
            # Ingest analytics
            if 'analytics' in files:
                analytics_data = self.load_json_file(files['analytics'])
                results['analytics_ingested'] = self.ingest_asset_analytics(
                    analytics_data.get('individual_analyses', [])
                )
            
            # Ingest summary
            if 'summary' in files:
                summary_data = self.load_json_file(files['summary'])
                results['summary_ingested'] = self.ingest_optimization_summary(summary_data)
            
            # Ingest plots data
            if 'plots' in files:
                plots_data = self.load_json_file(files['plots'])
                results['plots_ingested'] = self.ingest_plots_data(plots_data)
            
            # Close database connection
            self.close_database()
            
            logger.info("Optimization data ingestion completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error ingesting optimization data: {e}")
            if self.connection:
                self.close_database()
            raise

@shared_task(bind=True)
def ingest_optimization_data(self):
    """
    Celery task to ingest optimization data from hotbox export
    
    This task:
    1. Scans the hotbox/export_results folder for latest data
    2. Ingests alerts for real-time alerting
    3. Ingests analytics for detailed asset analysis
    4. Ingests summary data for dashboard overview
    5. Ingests plots data for chart generation
    """
    try:
        logger.info("Starting optimization data ingestion task")
        
        # Initialize ingestion system
        ingestion = OptimizationDataIngestion()
        
        # Ingest latest data
        results = ingestion.ingest_latest_data()
        
        logger.info(f"Optimization data ingestion completed: {results}")
        
        return {
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Optimization data ingestion failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Main function for testing"""
    try:
        logger.info("Testing optimization data ingestion")
        
        ingestion = OptimizationDataIngestion()
        results = ingestion.ingest_latest_data()
        
        print("Ingestion completed successfully:")
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main() 