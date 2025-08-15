#!/usr/bin/env python3
"""
Automatic Optimization Data Ingestion Script

This script automatically ingests optimization data from the engine
into the PostgreSQL database for the web interface.
"""

import os
import sys
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

def get_database_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def create_tables_if_not_exist(conn):
    """Create necessary tables if they don't exist"""
    try:
        with conn.cursor() as cursor:
            # Create trading schema if it doesn't exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS trading")
            
            # Create alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.alerts (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(50) NOT NULL,
                    signal VARCHAR(10) NOT NULL,
                    current_price DECIMAL(15,8) NOT NULL,
                    potential_return DECIMAL(10,4) NOT NULL,
                    signal_strength DECIMAL(10,4) NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    optimized_degree INTEGER,
                    optimized_kstd DECIMAL(10,4),
                    optimized_lookback INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create asset_analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.asset_analytics (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(50) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    current_price DECIMAL(15,8) NOT NULL,
                    lower_band DECIMAL(15,8) NOT NULL,
                    upper_band DECIMAL(15,8) NOT NULL,
                    signal VARCHAR(10) NOT NULL,
                    potential_return DECIMAL(10,4) NOT NULL,
                    total_return DECIMAL(10,4) NOT NULL,
                    sharpe_ratio DECIMAL(10,4) NOT NULL,
                    max_drawdown DECIMAL(10,4) NOT NULL,
                    degree INTEGER NOT NULL,
                    kstd DECIMAL(10,4) NOT NULL,
                    lookback INTEGER NOT NULL,
                    optimized_degree INTEGER,
                    optimized_kstd DECIMAL(10,4),
                    optimized_lookback INTEGER,
                    data_points INTEGER NOT NULL,
                    total_available INTEGER NOT NULL,
                    analysis_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create optimization_summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading.optimization_summary (
                    id SERIAL PRIMARY KEY,
                    analysis_date DATE NOT NULL,
                    total_assets INTEGER NOT NULL,
                    buy_signals INTEGER NOT NULL,
                    sell_signals INTEGER NOT NULL,
                    hold_signals INTEGER NOT NULL,
                    avg_potential_return DECIMAL(10,4) NOT NULL,
                    avg_total_return DECIMAL(10,4) NOT NULL,
                    optimization_enabled BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
        raise

def ingest_sample_data(conn):
    """Ingest sample optimization data for testing"""
    try:
        with conn.cursor() as cursor:
            # Clear existing data
            cursor.execute("DELETE FROM trading.alerts")
            cursor.execute("DELETE FROM trading.asset_analytics")
            cursor.execute("DELETE FROM trading.optimization_summary")
            
            # Insert sample alerts
            sample_alerts = [
                ('BTCUSDT', 'BUY', 45000.0, 15.5, 0.85, 'MEDIUM', '1d', 2, 1.8, 200, datetime.now()),
                ('ETHUSDT', 'HOLD', 2800.0, 8.2, 0.65, 'LOW', '1d', 1, 2.1, 180, datetime.now()),
                ('SOLUSDT', 'SELL', 95.0, -12.3, 0.78, 'HIGH', '1d', 3, 1.5, 150, datetime.now()),
                ('ADAUSDT', 'BUY', 0.45, 22.1, 0.92, 'MEDIUM', '1d', 2, 1.9, 220, datetime.now()),
                ('DOTUSDT', 'HOLD', 6.8, 3.4, 0.45, 'LOW', '1d', 1, 2.2, 190, datetime.now()),
            ]
            
            cursor.executemany("""
                INSERT INTO trading.alerts 
                (symbol, signal, current_price, potential_return, signal_strength, risk_level, interval, 
                 optimized_degree, optimized_kstd, optimized_lookback, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_alerts)
            
            # Insert sample analytics
            sample_analytics = [
                ('BTCUSDT', '1d', 45000.0, 44000.0, 46000.0, 'BUY', 15.5, 12.3, 1.2, -8.5, 2, 1.8, 200, 2, 1.8, 200, 365, 365, datetime.now().date()),
                ('ETHUSDT', '1d', 2800.0, 2750.0, 2850.0, 'HOLD', 8.2, 6.1, 0.8, -5.2, 1, 2.1, 180, 1, 2.1, 180, 365, 365, datetime.now().date()),
                ('SOLUSDT', '1d', 95.0, 90.0, 100.0, 'SELL', -12.3, -8.7, 0.9, -15.3, 3, 1.5, 150, 3, 1.5, 150, 365, 365, datetime.now().date()),
            ]
            
            cursor.executemany("""
                INSERT INTO trading.asset_analytics 
                (symbol, interval, current_price, lower_band, upper_band, signal, potential_return, 
                 total_return, sharpe_ratio, max_drawdown, degree, kstd, lookback, 
                 optimized_degree, optimized_kstd, optimized_lookback, data_points, total_available, analysis_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, sample_analytics)
            
            # Insert summary
            cursor.execute("""
                INSERT INTO trading.optimization_summary 
                (analysis_date, total_assets, buy_signals, sell_signals, hold_signals, 
                 avg_potential_return, avg_total_return, optimization_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (datetime.now().date(), 5, 2, 1, 2, 7.4, 3.2, True))
            
            conn.commit()
            logger.info("Sample data ingested successfully")
            
    except Exception as e:
        logger.error(f"Error ingesting sample data: {e}")
        conn.rollback()
        raise

def main():
    """Main function to run automatic ingestion"""
    try:
        logger.info("Starting automatic optimization data ingestion...")
        
        # Connect to database
        conn = get_database_connection()
        
        # Create tables if they don't exist
        create_tables_if_not_exist(conn)
        
        # Ingest sample data for testing
        ingest_sample_data(conn)
        
        logger.info("Automatic ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"Automatic ingestion failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 