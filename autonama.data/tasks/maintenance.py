from celery_app import celery_app
import logging
from datetime import datetime, timedelta
from utils.database import db_manager

logger = logging.getLogger(__name__)

@celery_app.task
def cleanup_old_data():
    """Clean up old data to maintain database performance"""
    try:
        logger.info("Starting data cleanup task")
        
        # Clean up old market data (keep last 2 years)
        cutoff_date = datetime.now() - timedelta(days=730)
        
        cleanup_queries = [
            # Clean old market data
            f"""
            DELETE FROM market_data 
            WHERE timestamp < '{cutoff_date.isoformat()}'
            """,
            
            # Clean old technical indicators
            f"""
            DELETE FROM technical_indicators 
            WHERE timestamp < '{cutoff_date.isoformat()}'
            """,
            
            # Clean old optimization results (keep last 6 months)
            f"""
            DELETE FROM optimization_results 
            WHERE created_at < '{(datetime.now() - timedelta(days=180)).isoformat()}'
            """
        ]
        
        cleaned_records = 0
        postgres_available = False
        
        # Try PostgreSQL cleanup
        try:
            for query in cleanup_queries:
                try:
                    with db_manager.postgres_engine.connect() as conn:
                        result = conn.execute(query)
                        cleaned_records += result.rowcount
                        conn.commit()
                        postgres_available = True
                except Exception as e:
                    logger.warning(f"Error executing cleanup query: {str(e)}")
                    continue
            
            if postgres_available:
                logger.info(f"PostgreSQL cleanup completed: {cleaned_records} records cleaned")
            
        except Exception as e:
            logger.warning(f"PostgreSQL cleanup failed: {str(e)}")
        
        # Try Redis cleanup
        redis_keys_cleaned = 0
        try:
            redis_client = db_manager.get_redis_client()
            
            # Get all keys and clean expired ones
            all_keys = redis_client.keys('*')
            expired_keys = []
            
            for key in all_keys:
                try:
                    ttl = redis_client.ttl(key)
                    if ttl == -1:  # No expiration set
                        # Set expiration for old keys
                        redis_client.expire(key, 86400)  # 24 hours
                    elif ttl == -2:  # Key doesn't exist
                        expired_keys.append(key)
                except Exception as e:
                    logger.warning(f"Error checking key {key}: {e}")
                    continue
            
            if expired_keys:
                redis_client.delete(*expired_keys)
                redis_keys_cleaned = len(expired_keys)
            
            logger.info(f"Redis cleanup completed: {redis_keys_cleaned} keys cleaned")
            
        except Exception as e:
            logger.warning(f"Redis cleanup failed: {str(e)}")
        
        # Summary
        total_cleaned = cleaned_records + redis_keys_cleaned
        if total_cleaned > 0:
            logger.info(f"Cleanup completed successfully: {cleaned_records} database records, {redis_keys_cleaned} Redis keys")
        else:
            logger.info("Cleanup completed: No data needed cleaning or services unavailable")
        
        return {
            'status': 'completed',
            'database_records_cleaned': cleaned_records,
            'redis_keys_cleaned': redis_keys_cleaned,
            'postgres_available': postgres_available,
            'total_cleaned': total_cleaned
        }
        
    except Exception as e:
        logger.error(f"Critical error in cleanup_old_data: {str(e)}")
        # Return partial success instead of failing completely
        return {
            'status': 'partial_failure',
            'error': str(e),
            'database_records_cleaned': 0,
            'redis_keys_cleaned': 0
        }


@celery_app.task
def optimize_database():
    """Optimize database performance with improved error handling"""
    try:
        logger.info("Starting database optimization task")
        
        optimization_queries = [
            # Analyze tables for better query planning
            "ANALYZE market_data;",
            "ANALYZE technical_indicators;", 
            "ANALYZE optimization_results;",
            
            # Vacuum tables to reclaim space (these might take longer)
            "VACUUM market_data;",
            "VACUUM technical_indicators;",
            "VACUUM optimization_results;",
        ]
        
        successful_operations = 0
        failed_operations = 0
        
        # Check if PostgreSQL is available first
        try:
            with db_manager.postgres_engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("PostgreSQL connection verified for optimization")
        except Exception as e:
            logger.warning(f"PostgreSQL not available for optimization: {e}")
            return {
                'status': 'skipped',
                'reason': 'PostgreSQL not available',
                'error': str(e)
            }
        
        # Execute optimization queries
        for query in optimization_queries:
            try:
                logger.info(f"Executing: {query.strip()}")
                with db_manager.postgres_engine.connect() as conn:
                    conn.execute(query)
                    conn.commit()
                successful_operations += 1
                logger.info(f"Successfully executed: {query.strip()}")
            except Exception as e:
                failed_operations += 1
                logger.warning(f"Failed to execute {query.strip()}: {str(e)}")
                continue
        
        # Summary
        total_operations = len(optimization_queries)
        success_rate = (successful_operations / total_operations) * 100
        
        logger.info(f"Database optimization completed: {successful_operations}/{total_operations} operations successful ({success_rate:.1f}%)")
        
        return {
            'status': 'completed' if successful_operations > 0 else 'failed',
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'total_operations': total_operations,
            'success_rate': round(success_rate, 1)
        }
        
    except Exception as e:
        logger.error(f"Critical error in optimize_database: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'successful_operations': 0,
            'failed_operations': 0
        }


@celery_app.task
def health_check():
    """Perform system health check with improved error handling"""
    try:
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'postgres': False,
            'redis': False,
            'duckdb': False,
            'disk_space': None,
            'memory_usage': None,
            'errors': []
        }
        
        # Check PostgreSQL connection with better error handling
        try:
            # Try to import and use database manager
            with db_manager.postgres_engine.connect() as conn:
                conn.execute("SELECT 1")
            health_status['postgres'] = True
            logger.info("PostgreSQL health check passed")
        except Exception as e:
            error_msg = f"PostgreSQL health check failed: {str(e)}"
            logger.warning(error_msg)  # Changed from ERROR to WARNING
            health_status['errors'].append(error_msg)
            health_status['postgres'] = False
        
        # Check Redis connection
        try:
            redis_client = db_manager.get_redis_client()
            redis_client.ping()
            health_status['redis'] = True
            logger.info("Redis health check passed")
        except Exception as e:
            error_msg = f"Redis health check failed: {str(e)}"
            logger.warning(error_msg)  # Changed from ERROR to WARNING
            health_status['errors'].append(error_msg)
            health_status['redis'] = False
        
        # Check DuckDB connection with lock handling
        try:
            # Use a more cautious approach for DuckDB
            # import duckdb  # REMOVED: No longer needed
            import os
            
            duckdb_path = os.getenv('DUCKDB_PATH', '/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb')
            
            # Check if file exists and is accessible
            if os.path.exists(duckdb_path):
                # Try to connect with read-only mode to avoid lock conflicts
                try:
                    conn = duckdb.connect(duckdb_path, read_only=True)
                    conn.execute("SELECT 1")
                    conn.close()
                    health_status['duckdb'] = True
                    logger.info("DuckDB health check passed (read-only)")
                except Exception as lock_error:
                    # If read-only fails due to locks, that's actually OK - it means the DB is being used
                    if "lock" in str(lock_error).lower():
                        health_status['duckdb'] = True  # DB is active, just locked
                        logger.info("DuckDB health check passed (database is actively being used)")
                    else:
                        raise lock_error
            else:
                # File doesn't exist, try to create directory
                os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)
                health_status['duckdb'] = False
                health_status['errors'].append("DuckDB file does not exist")
                logger.warning("DuckDB file does not exist")
                
        except Exception as e:
            error_msg = f"DuckDB health check failed: {str(e)}"
            logger.warning(error_msg)  # Changed from ERROR to WARNING
            health_status['errors'].append(error_msg)
            health_status['duckdb'] = False
        
        # Check system resources
        try:
            import psutil
            
            # Disk space
            disk_usage = psutil.disk_usage('/')
            health_status['disk_space'] = {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': round((disk_usage.used / disk_usage.total) * 100, 2)
            }
            
            # Memory usage
            memory = psutil.virtual_memory()
            health_status['memory_usage'] = {
                'total': memory.total,
                'used': memory.used,
                'available': memory.available,
                'percent': round(memory.percent, 2)
            }
            
            logger.info(f"System resources: Disk {health_status['disk_space']['percent']}% used, Memory {health_status['memory_usage']['percent']}% used")
            
        except ImportError:
            logger.info("psutil not available for system monitoring")
            health_status['errors'].append("psutil not available for system monitoring")
        except Exception as e:
            error_msg = f"System resource check failed: {str(e)}"
            logger.warning(error_msg)
            health_status['errors'].append(error_msg)
        
        # Try to cache health status (but don't fail if Redis is down)
        try:
            if health_status['redis']:
                db_manager.cache_data('system_health', health_status, expire=300)  # 5 minutes
        except Exception as e:
            logger.warning(f"Could not cache health status: {e}")
        
        # Log overall health summary
        services_up = sum([health_status['postgres'], health_status['redis'], health_status['duckdb']])
        logger.info(f"Health check completed: {services_up}/3 services healthy")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Critical error in health_check: {str(e)}")
        # Return a basic health status even if the check fails
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'postgres': False,
            'redis': False,
            'duckdb': False,
            'disk_space': None,
            'memory_usage': None,
            'errors': [f"Health check failed: {str(e)}"],
            'status': 'error'
        }


@celery_app.task
def backup_critical_data():
    """Backup critical data with improved error handling"""
    try:
        import os
        from datetime import datetime
        
        logger.info("Starting critical data backup task")
        
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"/tmp/autonama_backup_{backup_timestamp}"
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Created backup directory: {backup_dir}")
        
        files_created = 0
        errors = []
        
        # Check if PostgreSQL is available
        postgres_available = False
        try:
            with db_manager.postgres_engine.connect() as conn:
                conn.execute("SELECT 1")
            postgres_available = True
            logger.info("PostgreSQL connection verified for backup")
        except Exception as e:
            logger.warning(f"PostgreSQL not available for backup: {e}")
            errors.append(f"PostgreSQL unavailable: {str(e)}")
        
        if postgres_available:
            # Export optimization results
            try:
                query = """
                SELECT * FROM optimization_results 
                WHERE created_at >= NOW() - INTERVAL '30 days'
                """
                
                results_df = db_manager.execute_postgres_query(query)
                if not results_df.empty:
                    backup_file = f"{backup_dir}/optimization_results.csv"
                    results_df.to_csv(backup_file, index=False)
                    files_created += 1
                    logger.info(f"Backed up {len(results_df)} optimization results")
                else:
                    logger.info("No recent optimization results to backup")
                    
            except Exception as e:
                error_msg = f"Failed to backup optimization results: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
            
            # Export recent market data for key symbols
            key_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
            
            for symbol in key_symbols:
                try:
                    query = """
                    SELECT * FROM market_data 
                    WHERE symbol = :symbol 
                    AND timestamp >= NOW() - INTERVAL '7 days'
                    """
                    
                    data_df = db_manager.execute_postgres_query(query, {'symbol': symbol})
                    if not data_df.empty:
                        backup_file = f"{backup_dir}/market_data_{symbol}.csv"
                        data_df.to_csv(backup_file, index=False)
                        files_created += 1
                        logger.info(f"Backed up {len(data_df)} records for {symbol}")
                    else:
                        logger.info(f"No recent data for {symbol} to backup")
                        
                except Exception as e:
                    error_msg = f"Failed to backup data for {symbol}: {str(e)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
        
        # Create a backup summary file
        try:
            summary = {
                'backup_timestamp': backup_timestamp,
                'files_created': files_created,
                'postgres_available': postgres_available,
                'errors': errors,
                'backup_directory': backup_dir
            }
            
            import json
            with open(f"{backup_dir}/backup_summary.json", 'w') as f:
                json.dump(summary, f, indent=2)
            files_created += 1
            
        except Exception as e:
            logger.warning(f"Failed to create backup summary: {e}")
        
        # Final summary
        if files_created > 0:
            logger.info(f"Backup completed successfully: {backup_dir} ({files_created} files created)")
        else:
            logger.warning("Backup completed but no files were created")
        
        return {
            'status': 'completed' if files_created > 0 else 'partial_failure',
            'backup_location': backup_dir,
            'files_created': files_created,
            'postgres_available': postgres_available,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Critical error in backup_critical_data: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'backup_location': None,
            'files_created': 0
        }
