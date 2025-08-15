import os
import json
import logging
from datetime import datetime
from celery import shared_task
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

@shared_task(bind=True)
def ingest_backtest_results(self, results_file_path: str):
    """
    Ingest backtest results from a JSON file and store in database
    
    Args:
        results_file_path: Path to the JSON file containing backtest results
    """
    try:
        logger.info(f"Starting ingestion of backtest results from {results_file_path}")
        
        # Check if file exists
        if not os.path.exists(results_file_path):
            raise FileNotFoundError(f"Results file not found: {results_file_path}")
        
        # Load results from JSON file
        with open(results_file_path, 'r') as f:
            results = json.load(f)
        
        if not results:
            logger.warning("No results found in file")
            return {
                'status': 'warning',
                'message': 'No results found in file',
                'timestamp': datetime.now().isoformat()
            }
        
        # Store results in database
        stored_count = 0
        error_count = 0
        
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                for result in results:
                    try:
                        # Insert alert
                        cursor.execute("""
                            INSERT INTO trading.alerts 
                            (symbol, interval, signal, current_price, upper_band, lower_band, 
                             potential_return, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, interval, created_at::date) 
                            DO UPDATE SET
                                signal = EXCLUDED.signal,
                                current_price = EXCLUDED.current_price,
                                upper_band = EXCLUDED.upper_band,
                                lower_band = EXCLUDED.lower_band,
                                potential_return = EXCLUDED.potential_return,
                                updated_at = NOW()
                        """, (
                            result['symbol'],
                            result['interval'],
                            result['signal'],
                            result['current_price'],
                            result['upper_band'],
                            result['lower_band'],
                            result['potential_return'],
                            result['timestamp']
                        ))
                        stored_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error storing result for {result.get('symbol', 'unknown')}: {e}")
                
                conn.commit()
        
        logger.info(f"Ingestion complete: {stored_count} stored, {error_count} errors")
        
        return {
            'status': 'success',
            'stored_count': stored_count,
            'error_count': error_count,
            'total_processed': len(results),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in backtest ingestion: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def ingest_backtest_results_from_directory(self, directory_path: str, pattern: str = "backtest_results_*.json"):
    """
    Ingest all backtest result files from a directory
    
    Args:
        directory_path: Directory containing backtest result files
        pattern: File pattern to match (default: backtest_results_*.json)
    """
    try:
        import glob
        
        logger.info(f"Starting ingestion from directory: {directory_path}")
        
        # Find all matching files
        file_pattern = os.path.join(directory_path, pattern)
        result_files = glob.glob(file_pattern)
        
        if not result_files:
            logger.warning(f"No result files found matching pattern: {file_pattern}")
            return {
                'status': 'warning',
                'message': 'No result files found',
                'timestamp': datetime.now().isoformat()
            }
        
        # Sort files by modification time (newest first)
        result_files.sort(key=os.path.getmtime, reverse=True)
        
        total_stored = 0
        total_errors = 0
        processed_files = 0
        
        for file_path in result_files:
            try:
                logger.info(f"Processing file: {file_path}")
                
                # Ingest this file
                result = ingest_backtest_results(file_path)
                
                if result['status'] == 'success':
                    total_stored += result['stored_count']
                    total_errors += result['error_count']
                    processed_files += 1
                else:
                    total_errors += 1
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                total_errors += 1
        
        logger.info(f"Directory ingestion complete: {processed_files} files processed")
        
        return {
            'status': 'success',
            'processed_files': processed_files,
            'total_stored': total_stored,
            'total_errors': total_errors,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in directory ingestion: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def monitor_backtest_results_directory(self, directory_path: str, pattern: str = "backtest_results_*.json"):
    """
    Monitor a directory for new backtest result files and ingest them automatically
    
    Args:
        directory_path: Directory to monitor
        pattern: File pattern to match
    """
    try:
        import glob
        import time
        
        logger.info(f"Starting monitoring of directory: {directory_path}")
        
        # Get list of existing files
        file_pattern = os.path.join(directory_path, pattern)
        existing_files = set(glob.glob(file_pattern))
        
        # Check for new files every 5 minutes
        while True:
            current_files = set(glob.glob(file_pattern))
            new_files = current_files - existing_files
            
            if new_files:
                logger.info(f"Found {len(new_files)} new result files")
                
                for file_path in new_files:
                    try:
                        # Wait a bit to ensure file is completely written
                        time.sleep(5)
                        
                        # Ingest the new file
                        result = ingest_backtest_results(file_path)
                        logger.info(f"Ingested {file_path}: {result}")
                        
                    except Exception as e:
                        logger.error(f"Error ingesting {file_path}: {e}")
                
                # Update existing files set
                existing_files = current_files
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
        
    except Exception as e:
        logger.error(f"Error in directory monitoring: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def cleanup_old_alerts(self, days_to_keep: int = 30):
    """
    Clean up old alerts from the database
    
    Args:
        days_to_keep: Number of days of alerts to keep
    """
    try:
        logger.info(f"Cleaning up alerts older than {days_to_keep} days")
        
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM trading.alerts 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days_to_keep,))
                
                deleted_count = cursor.rowcount
                conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old alerts")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old alerts: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def get_ingestion_status(self):
    """Get status of recent ingestion activities"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get recent alerts count
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(CASE WHEN signal = 'BUY' THEN 1 END) as buy_signals,
                        COUNT(CASE WHEN signal = 'SELL' THEN 1 END) as sell_signals,
                        COUNT(CASE WHEN signal = 'HOLD' THEN 1 END) as hold_signals,
                        MAX(created_at) as latest_alert
                    FROM trading.alerts 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                result = cursor.fetchone()
                
                return {
                    'status': 'success',
                    'total_alerts_24h': result['total_alerts'],
                    'buy_signals_24h': result['buy_signals'],
                    'sell_signals_24h': result['sell_signals'],
                    'hold_signals_24h': result['hold_signals'],
                    'latest_alert': result['latest_alert'].isoformat() if result['latest_alert'] else None,
                    'timestamp': datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 
import json
import logging
from datetime import datetime
from celery import shared_task
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'autonama',
    'user': 'postgres',
    'password': 'postgres'
}

@shared_task(bind=True)
def ingest_backtest_results(self, results_file_path: str):
    """
    Ingest backtest results from a JSON file and store in database
    
    Args:
        results_file_path: Path to the JSON file containing backtest results
    """
    try:
        logger.info(f"Starting ingestion of backtest results from {results_file_path}")
        
        # Check if file exists
        if not os.path.exists(results_file_path):
            raise FileNotFoundError(f"Results file not found: {results_file_path}")
        
        # Load results from JSON file
        with open(results_file_path, 'r') as f:
            results = json.load(f)
        
        if not results:
            logger.warning("No results found in file")
            return {
                'status': 'warning',
                'message': 'No results found in file',
                'timestamp': datetime.now().isoformat()
            }
        
        # Store results in database
        stored_count = 0
        error_count = 0
        
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                for result in results:
                    try:
                        # Insert alert
                        cursor.execute("""
                            INSERT INTO trading.alerts 
                            (symbol, interval, signal, current_price, upper_band, lower_band, 
                             potential_return, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, interval, created_at::date) 
                            DO UPDATE SET
                                signal = EXCLUDED.signal,
                                current_price = EXCLUDED.current_price,
                                upper_band = EXCLUDED.upper_band,
                                lower_band = EXCLUDED.lower_band,
                                potential_return = EXCLUDED.potential_return,
                                updated_at = NOW()
                        """, (
                            result['symbol'],
                            result['interval'],
                            result['signal'],
                            result['current_price'],
                            result['upper_band'],
                            result['lower_band'],
                            result['potential_return'],
                            result['timestamp']
                        ))
                        stored_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error storing result for {result.get('symbol', 'unknown')}: {e}")
                
                conn.commit()
        
        logger.info(f"Ingestion complete: {stored_count} stored, {error_count} errors")
        
        return {
            'status': 'success',
            'stored_count': stored_count,
            'error_count': error_count,
            'total_processed': len(results),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in backtest ingestion: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def ingest_backtest_results_from_directory(self, directory_path: str, pattern: str = "backtest_results_*.json"):
    """
    Ingest all backtest result files from a directory
    
    Args:
        directory_path: Directory containing backtest result files
        pattern: File pattern to match (default: backtest_results_*.json)
    """
    try:
        import glob
        
        logger.info(f"Starting ingestion from directory: {directory_path}")
        
        # Find all matching files
        file_pattern = os.path.join(directory_path, pattern)
        result_files = glob.glob(file_pattern)
        
        if not result_files:
            logger.warning(f"No result files found matching pattern: {file_pattern}")
            return {
                'status': 'warning',
                'message': 'No result files found',
                'timestamp': datetime.now().isoformat()
            }
        
        # Sort files by modification time (newest first)
        result_files.sort(key=os.path.getmtime, reverse=True)
        
        total_stored = 0
        total_errors = 0
        processed_files = 0
        
        for file_path in result_files:
            try:
                logger.info(f"Processing file: {file_path}")
                
                # Ingest this file
                result = ingest_backtest_results(file_path)
                
                if result['status'] == 'success':
                    total_stored += result['stored_count']
                    total_errors += result['error_count']
                    processed_files += 1
                else:
                    total_errors += 1
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                total_errors += 1
        
        logger.info(f"Directory ingestion complete: {processed_files} files processed")
        
        return {
            'status': 'success',
            'processed_files': processed_files,
            'total_stored': total_stored,
            'total_errors': total_errors,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in directory ingestion: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def monitor_backtest_results_directory(self, directory_path: str, pattern: str = "backtest_results_*.json"):
    """
    Monitor a directory for new backtest result files and ingest them automatically
    
    Args:
        directory_path: Directory to monitor
        pattern: File pattern to match
    """
    try:
        import glob
        import time
        
        logger.info(f"Starting monitoring of directory: {directory_path}")
        
        # Get list of existing files
        file_pattern = os.path.join(directory_path, pattern)
        existing_files = set(glob.glob(file_pattern))
        
        # Check for new files every 5 minutes
        while True:
            current_files = set(glob.glob(file_pattern))
            new_files = current_files - existing_files
            
            if new_files:
                logger.info(f"Found {len(new_files)} new result files")
                
                for file_path in new_files:
                    try:
                        # Wait a bit to ensure file is completely written
                        time.sleep(5)
                        
                        # Ingest the new file
                        result = ingest_backtest_results(file_path)
                        logger.info(f"Ingested {file_path}: {result}")
                        
                    except Exception as e:
                        logger.error(f"Error ingesting {file_path}: {e}")
                
                # Update existing files set
                existing_files = current_files
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
        
    except Exception as e:
        logger.error(f"Error in directory monitoring: {e}")
        self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes, max 3 times
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def cleanup_old_alerts(self, days_to_keep: int = 30):
    """
    Clean up old alerts from the database
    
    Args:
        days_to_keep: Number of days of alerts to keep
    """
    try:
        logger.info(f"Cleaning up alerts older than {days_to_keep} days")
        
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM trading.alerts 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days_to_keep,))
                
                deleted_count = cursor.rowcount
                conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} old alerts")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old alerts: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@shared_task(bind=True)
def get_ingestion_status(self):
    """Get status of recent ingestion activities"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get recent alerts count
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_alerts,
                        COUNT(CASE WHEN signal = 'BUY' THEN 1 END) as buy_signals,
                        COUNT(CASE WHEN signal = 'SELL' THEN 1 END) as sell_signals,
                        COUNT(CASE WHEN signal = 'HOLD' THEN 1 END) as hold_signals,
                        MAX(created_at) as latest_alert
                    FROM trading.alerts 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                result = cursor.fetchone()
                
                return {
                    'status': 'success',
                    'total_alerts_24h': result['total_alerts'],
                    'buy_signals_24h': result['buy_signals'],
                    'sell_signals_24h': result['sell_signals'],
                    'hold_signals_24h': result['hold_signals'],
                    'latest_alert': result['latest_alert'].isoformat() if result['latest_alert'] else None,
                    'timestamp': datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 
 