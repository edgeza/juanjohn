
#!/usr/bin/env python3
"""
VectorBTPro Results Ingestion System

This system acts as a clean bridge between the local VectorBTPro engine
and the main Docker system. It validates and processes output files
before ingestion into PostgreSQL.

Designed to run in the same conda environment as VectorBTPro.

Key Features:
- Validates output files for completeness and accuracy
- Processes both CSV and JSON formats
- Ensures data integrity before database insertion
- Provides detailed validation reports
- Clean error handling and logging
- Uses VectorBTPro for enhanced validation
"""

import os
import json
import logging
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import glob
from psycopg2.extras import RealDictCursor
import hashlib
import re

# Try to import VectorBTPro for enhanced validation
try:
    import vectorbtpro as vbt
    VECTORBT_AVAILABLE = True
    print(f"✅ VectorBTPro {vbt.__version__} available for enhanced validation")
except ImportError:
    VECTORBT_AVAILABLE = False
    print("⚠️ VectorBTPro not available, using basic validation")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("vectorbt_ingestion.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VectorBTIngestionValidator:
    """Validates VectorBTPro output files before ingestion"""
    
    def __init__(self):
        self.required_csv_columns = [
            'symbol', 'interval', 'current_price', 'lower_band', 'upper_band',
            'signal', 'potential_return', 'total_return', 'sharpe_ratio', 
            'max_drawdown', 'degree', 'kstd', 'analysis_date'
        ]
        
        self.required_json_fields = [
            'symbol', 'interval', 'current_price', 'lower_band', 'upper_band',
            'signal', 'potential_return', 'total_return', 'sharpe_ratio',
            'max_drawdown', 'degree', 'kstd', 'analysis_date'
        ]
        
        self.valid_signals = ['BUY', 'SELL', 'HOLD']
        self.valid_intervals = ['1d', '4h', '1h', '15m', '5m', '1m']
        
        # VectorBTPro validation settings
        self.use_vectorbt_validation = VECTORBT_AVAILABLE
    
    def validate_csv_file(self, filepath: str) -> Tuple[bool, List[str]]:
        """
        Validate CSV output file from VectorBTPro engine
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check file exists
            if not os.path.exists(filepath):
                errors.append(f"File does not exist: {filepath}")
                return False, errors
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                errors.append("File is empty")
                return False, errors
            
            # Read CSV
            df = pd.read_csv(filepath)
            
            # Check for required columns
            missing_columns = set(self.required_csv_columns) - set(df.columns)
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Check for empty dataframe
            if df.empty:
                errors.append("DataFrame is empty")
                return False, errors
            
            # Validate data types and ranges
            for index, row in df.iterrows():
                row_errors = self._validate_row(row, index)
                errors.extend(row_errors)
            
            # Check for duplicate symbols
            duplicates = df['symbol'].duplicated()
            if duplicates.any():
                duplicate_symbols = df[duplicates]['symbol'].tolist()
                errors.append(f"Duplicate symbols found: {duplicate_symbols}")
            
            # Validate analysis date format
            if 'analysis_date' in df.columns:
                try:
                    pd.to_datetime(df['analysis_date'])
                except:
                    errors.append("Invalid analysis_date format")
            
            # Enhanced validation with VectorBTPro if available
            if self.use_vectorbt_validation and not errors:
                vectorbt_errors = self._validate_with_vectorbt(df)
                errors.extend(vectorbt_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error reading CSV file: {str(e)}")
            return False, errors
    
    def validate_json_file(self, filepath: str) -> Tuple[bool, List[str]]:
        """
        Validate JSON output file from VectorBTPro engine
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check file exists
            if not os.path.exists(filepath):
                errors.append(f"File does not exist: {filepath}")
                return False, errors
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                errors.append("File is empty")
                return False, errors
            
            # Read JSON
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check if data is a list
            if not isinstance(data, list):
                errors.append("JSON data must be a list of objects")
                return False, errors
            
            if len(data) == 0:
                errors.append("JSON data is empty")
                return False, errors
            
            # Validate each record
            symbols = set()
            for index, record in enumerate(data):
                if not isinstance(record, dict):
                    errors.append(f"Record {index} is not a dictionary")
                    continue
                
                # Check for required fields
                missing_fields = set(self.required_json_fields) - set(record.keys())
                if missing_fields:
                    errors.append(f"Record {index} missing fields: {missing_fields}")
                
                # Validate symbol format
                symbol = record.get('symbol', '')
                if not self._is_valid_symbol(symbol):
                    errors.append(f"Record {index} has invalid symbol: {symbol}")
                else:
                    if symbol in symbols:
                        errors.append(f"Duplicate symbol found: {symbol}")
                    else:
                        symbols.add(symbol)
                
                # Validate other fields
                row_errors = self._validate_record(record, index)
                errors.extend(row_errors)
            
            # Enhanced validation with VectorBTPro if available
            if self.use_vectorbt_validation and not errors:
                df = pd.DataFrame(data)
                vectorbt_errors = self._validate_with_vectorbt(df)
                errors.extend(vectorbt_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error reading JSON file: {str(e)}")
            return False, errors
    
    def _validate_with_vectorbt(self, df: pd.DataFrame) -> List[str]:
        """
        Enhanced validation using VectorBTPro
        
        Args:
            df: DataFrame to validate
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if not VECTORBT_AVAILABLE:
            return errors
        
        try:
            # Check if results look like VectorBTPro output
            if 'total_return' in df.columns and 'sharpe_ratio' in df.columns:
                # Validate that returns are reasonable
                total_returns = pd.to_numeric(df['total_return'], errors='coerce')
                sharpe_ratios = pd.to_numeric(df['sharpe_ratio'], errors='coerce')
                
                # Check for extreme values
                if total_returns.max() > 1000:  # 1000% return
                    errors.append("Unrealistic total return values detected (>1000%)")
                
                if sharpe_ratios.max() > 10:  # Very high Sharpe ratio
                    errors.append("Unrealistic Sharpe ratio values detected (>10)")
                
                # Check for negative Sharpe ratios (might indicate poor strategy)
                negative_sharpe = (sharpe_ratios < 0).sum()
                if negative_sharpe > len(df) * 0.5:  # More than 50% negative
                    errors.append(f"High number of negative Sharpe ratios: {negative_sharpe}")
            
            # Validate price relationships
            if all(col in df.columns for col in ['current_price', 'lower_band', 'upper_band']):
                current_prices = pd.to_numeric(df['current_price'], errors='coerce')
                lower_bands = pd.to_numeric(df['lower_band'], errors='coerce')
                upper_bands = pd.to_numeric(df['upper_band'], errors='coerce')
                
                # Check for invalid band relationships
                invalid_bands = (lower_bands >= upper_bands).sum()
                if invalid_bands > 0:
                    errors.append(f"Invalid band relationships found: {invalid_bands} records")
                
                # Check for extreme price movements
                price_changes = ((upper_bands - lower_bands) / lower_bands * 100).abs()
                extreme_moves = (price_changes > 100).sum()  # >100% move
                if extreme_moves > len(df) * 0.1:  # More than 10% extreme moves
                    errors.append(f"High number of extreme price movements: {extreme_moves}")
            
        except Exception as e:
            errors.append(f"VectorBTPro validation error: {str(e)}")
        
        return errors
    
    def _validate_row(self, row: pd.Series, index: int) -> List[str]:
        """Validate a single CSV row"""
        errors = []
        
        # Validate symbol
        symbol = row.get('symbol', '')
        if not self._is_valid_symbol(symbol):
            errors.append(f"Row {index}: Invalid symbol format: {symbol}")
        
        # Validate interval
        interval = row.get('interval', '')
        if interval not in self.valid_intervals:
            errors.append(f"Row {index}: Invalid interval: {interval}")
        
        # Validate signal
        signal = row.get('signal', '')
        if signal not in self.valid_signals:
            errors.append(f"Row {index}: Invalid signal: {signal}")
        
        # Validate numeric fields
        numeric_fields = ['current_price', 'lower_band', 'upper_band', 'potential_return', 
                         'total_return', 'sharpe_ratio', 'max_drawdown', 'degree', 'kstd']
        
        for field in numeric_fields:
            value = row.get(field)
            if pd.isna(value):
                errors.append(f"Row {index}: Missing {field}")
            elif not isinstance(value, (int, float)):
                try:
                    float(value)
                except:
                    errors.append(f"Row {index}: Invalid {field}: {value}")
        
        # Validate price relationships
        current_price = row.get('current_price')
        lower_band = row.get('lower_band')
        upper_band = row.get('upper_band')
        
        if all(pd.notna([current_price, lower_band, upper_band])):
            if lower_band >= upper_band:
                errors.append(f"Row {index}: Lower band >= Upper band")
        
        return errors
    
    def _validate_record(self, record: Dict, index: int) -> List[str]:
        """Validate a single JSON record"""
        errors = []
        
        # Validate symbol
        symbol = record.get('symbol', '')
        if not self._is_valid_symbol(symbol):
            errors.append(f"Record {index}: Invalid symbol format: {symbol}")
        
        # Validate interval
        interval = record.get('interval', '')
        if interval not in self.valid_intervals:
            errors.append(f"Record {index}: Invalid interval: {interval}")
        
        # Validate signal
        signal = record.get('signal', '')
        if signal not in self.valid_signals:
            errors.append(f"Record {index}: Invalid signal: {signal}")
        
        # Validate numeric fields
        numeric_fields = ['current_price', 'lower_band', 'upper_band', 'potential_return', 
                         'total_return', 'sharpe_ratio', 'max_drawdown', 'degree', 'kstd']
        
        for field in numeric_fields:
            value = record.get(field)
            if value is None:
                errors.append(f"Record {index}: Missing {field}")
            elif not isinstance(value, (int, float)):
                try:
                    float(value)
                except:
                    errors.append(f"Record {index}: Invalid {field}: {value}")
        
        # Validate price relationships
        current_price = record.get('current_price')
        lower_band = record.get('lower_band')
        upper_band = record.get('upper_band')
        
        if all(v is not None for v in [current_price, lower_band, upper_band]):
            if lower_band >= upper_band:
                errors.append(f"Record {index}: Lower band >= Upper band")
        
        return errors
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol follows valid format"""
        if not isinstance(symbol, str):
            return False
        
        # Check for valid crypto symbol format (e.g., BTCUSDT, ETHUSDT)
        pattern = r'^[A-Z0-9]+USDT$'
        return bool(re.match(pattern, symbol))

class VectorBTIngestionProcessor:
    """Processes validated VectorBTPro results for database ingestion"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection = None
        self.validator = VectorBTIngestionValidator()
    
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
    
    def find_latest_results(self, engine_results_dir: str) -> Dict[str, str]:
        """
        Find the latest VectorBTPro results files
        
        Args:
            engine_results_dir: Directory containing engine results
        
        Returns:
            Dictionary with file paths for CSV and JSON
        """
        try:
            files = {}
            
            # Find latest CSV file
            csv_pattern = os.path.join(engine_results_dir, "vectorbt_analysis_results_*.csv")
            csv_files = glob.glob(csv_pattern)
            if csv_files:
                csv_files.sort(key=os.path.getmtime, reverse=True)
                files['csv'] = csv_files[0]
                logger.info(f"Found latest CSV file: {files['csv']}")
            
            # Find latest JSON file
            json_pattern = os.path.join(engine_results_dir, "vectorbt_analysis_results_*.json")
            json_files = glob.glob(json_pattern)
            if json_files:
                json_files.sort(key=os.path.getmtime, reverse=True)
                files['json'] = json_files[0]
                logger.info(f"Found latest JSON file: {files['json']}")
            
            if not files:
                logger.warning(f"No VectorBTPro results files found in {engine_results_dir}")
            
            return files
            
        except Exception as e:
            logger.error(f"Error finding latest results files: {e}")
            return {}
    
    def validate_and_load_results(self, files: Dict[str, str]) -> Tuple[List[Dict], List[str]]:
        """
        Validate and load results from files
        
        Args:
            files: Dictionary with file paths
        
        Returns:
            Tuple of (valid_results, validation_errors)
        """
        all_results = []
        all_errors = []
        
        # Validate and load CSV
        if 'csv' in files:
            is_valid, errors = self.validator.validate_csv_file(files['csv'])
            if is_valid:
                try:
                    df = pd.read_csv(files['csv'])
                    results = df.to_dict('records')
                    all_results.extend(results)
                    logger.info(f"Successfully loaded {len(results)} results from CSV")
                except Exception as e:
                    all_errors.append(f"Error loading CSV: {e}")
            else:
                all_errors.extend(errors)
                logger.error(f"CSV validation failed: {errors}")
        
        # Validate and load JSON
        if 'json' in files:
            is_valid, errors = self.validator.validate_json_file(files['json'])
            if is_valid:
                try:
                    with open(files['json'], 'r') as f:
                        results = json.load(f)
                    all_results.extend(results)
                    logger.info(f"Successfully loaded {len(results)} results from JSON")
                except Exception as e:
                    all_errors.append(f"Error loading JSON: {e}")
            else:
                all_errors.extend(errors)
                logger.error(f"JSON validation failed: {errors}")
        
        # Remove duplicates
        if all_results:
            seen = set()
            unique_results = []
            for result in all_results:
                key = f"{result.get('symbol')}_{result.get('interval', '1d')}"
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            all_results = unique_results
        
        return all_results, all_errors
    
    def create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist"""
        try:
            with self.connection.cursor() as cursor:
                # Create alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trading.alerts (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        interval VARCHAR(10) NOT NULL,
                        signal VARCHAR(10) NOT NULL,
                        current_price NUMERIC(20,8),
                        upper_band NUMERIC(20,8),
                        lower_band NUMERIC(20,8),
                        potential_return NUMERIC(10,4),
                        total_return NUMERIC(10,4),
                        sharpe_ratio NUMERIC(10,4),
                        max_drawdown NUMERIC(10,4),
                        degree INTEGER,
                        kstd NUMERIC(5,2),
                        analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create vectorbt_analysis table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trading.vectorbt_analysis (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        interval VARCHAR(10) NOT NULL,
                        analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        current_price NUMERIC(20,8),
                        lower_band NUMERIC(20,8),
                        upper_band NUMERIC(20,8),
                        signal VARCHAR(10),
                        potential_return NUMERIC(10,4),
                        total_return NUMERIC(10,4),
                        sharpe_ratio NUMERIC(10,4),
                        max_drawdown NUMERIC(10,4),
                        degree INTEGER,
                        kstd NUMERIC(5,2),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON trading.alerts(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_signal ON trading.alerts(signal)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_date ON trading.alerts(analysis_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectorbt_symbol ON trading.vectorbt_analysis(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectorbt_date ON trading.vectorbt_analysis(analysis_date)")
                
                self.connection.commit()
                logger.info("Tables created/verified successfully")
                
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.connection.rollback()
            raise
    
    def ingest_alerts(self, results: List[Dict]) -> int:
        """
        Ingest alert signals into the database
        
        Args:
            results: List of validated analysis results
        
        Returns:
            Number of alerts ingested
        """
        try:
            ingested_count = 0
            
            with self.connection.cursor() as cursor:
                for result in results:
                    symbol = result['symbol']
                    signal = result.get('signal', 'HOLD')
                    
                    # Check if alert already exists for this symbol today
                    cursor.execute("""
                        SELECT id FROM trading.alerts 
                        WHERE symbol = %s AND analysis_date::date = CURRENT_DATE
                    """, (symbol,))
                    
                    existing_alert = cursor.fetchone()
                    
                    if existing_alert:
                        # Update existing alert
                        cursor.execute("""
                            UPDATE trading.alerts SET
                                signal = %s,
                                current_price = %s,
                                upper_band = %s,
                                lower_band = %s,
                                potential_return = %s,
                                total_return = %s,
                                sharpe_ratio = %s,
                                max_drawdown = %s,
                                degree = %s,
                                kstd = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            signal,
                            result.get('current_price'),
                            result.get('upper_band'),
                            result.get('lower_band'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd'),
                            existing_alert[0]
                        ))
                        logger.info(f"Updated alert for {symbol}")
                    else:
                        # Insert new alert
                        cursor.execute("""
                            INSERT INTO trading.alerts (
                                symbol, interval, signal, current_price, upper_band, lower_band,
                                potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            symbol,
                            result.get('interval', '1d'),
                            signal,
                            result.get('current_price'),
                            result.get('upper_band'),
                            result.get('lower_band'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd')
                        ))
                        logger.info(f"Inserted new alert for {symbol}")
                    
                    ingested_count += 1
            
            self.connection.commit()
            logger.info(f"Successfully ingested {ingested_count} alerts")
            return ingested_count
            
        except Exception as e:
            logger.error(f"Error ingesting alerts: {e}")
            self.connection.rollback()
            return 0
    
    def ingest_vectorbt_analysis(self, results: List[Dict]) -> int:
        """
        Ingest detailed VectorBTPro analysis into the database
        
        Args:
            results: List of validated analysis results
        
        Returns:
            Number of analysis records ingested
        """
        try:
            ingested_count = 0
            
            with self.connection.cursor() as cursor:
                for result in results:
                    symbol = result['symbol']
                    
                    # Check if analysis already exists for this symbol today
                    cursor.execute("""
                        SELECT id FROM trading.vectorbt_analysis 
                        WHERE symbol = %s AND analysis_date::date = CURRENT_DATE
                    """, (symbol,))
                    
                    existing_analysis = cursor.fetchone()
                    
                    if existing_analysis:
                        # Update existing analysis
                        cursor.execute("""
                            UPDATE trading.vectorbt_analysis SET
                                current_price = %s,
                                lower_band = %s,
                                upper_band = %s,
                                signal = %s,
                                potential_return = %s,
                                total_return = %s,
                                sharpe_ratio = %s,
                                max_drawdown = %s,
                                degree = %s,
                                kstd = %s
                            WHERE id = %s
                        """, (
                            result.get('current_price'),
                            result.get('lower_band'),
                            result.get('upper_band'),
                            result.get('signal'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd'),
                            existing_analysis[0]
                        ))
                        logger.info(f"Updated analysis for {symbol}")
                    else:
                        # Insert new analysis
                        cursor.execute("""
                            INSERT INTO trading.vectorbt_analysis (
                                symbol, interval, current_price, lower_band, upper_band,
                                signal, potential_return, total_return, sharpe_ratio, max_drawdown,
                                degree, kstd
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            symbol,
                            result.get('interval', '1d'),
                            result.get('current_price'),
                            result.get('lower_band'),
                            result.get('upper_band'),
                            result.get('signal'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd')
                        ))
                        logger.info(f"Inserted new analysis for {symbol}")
                    
                    ingested_count += 1
            
            self.connection.commit()
            logger.info(f"Successfully ingested {ingested_count} VectorBTPro analysis records")
            return ingested_count
            
        except Exception as e:
            logger.error(f"Error ingesting VectorBTPro analysis: {e}")
            self.connection.rollback()
            return 0
    
    def cleanup_old_data(self, days: int = 30):
        """
        Clean up old data to prevent database bloat
        
        Args:
            days: Number of days to keep data
        """
        try:
            with self.connection.cursor() as cursor:
                # Clean up old alerts
                cursor.execute("""
                    DELETE FROM trading.alerts 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days,))
                alerts_deleted = cursor.rowcount
                
                # Clean up old VectorBTPro analysis
                cursor.execute("""
                    DELETE FROM trading.vectorbt_analysis 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days,))
                analysis_deleted = cursor.rowcount
                
                self.connection.commit()
                logger.info(f"Cleanup completed: {alerts_deleted} alerts, {analysis_deleted} analysis records deleted")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            self.connection.rollback()
    
    def process_engine_results(self, engine_results_dir: str) -> Dict:
        """
        Main processing function: validate and ingest VectorBTPro results
        
        Args:
            engine_results_dir: Directory containing engine output files
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Connect to database
            self.connect_database()
            
            # Create tables if they don't exist
            self.create_tables_if_not_exist()
            
            # Find latest results files
            files = self.find_latest_results(engine_results_dir)
            if not files:
                return {'error': 'No VectorBTPro results files found'}
            
            # Validate and load results
            results, validation_errors = self.validate_and_load_results(files)
            
            if validation_errors:
                logger.error(f"Validation errors found: {validation_errors}")
                return {
                    'error': 'Validation failed',
                    'validation_errors': validation_errors,
                    'files_checked': list(files.values())
                }
            
            if not results:
                return {'error': 'No valid results found after validation'}
            
            # Ingest data
            alerts_ingested = self.ingest_alerts(results)
            analysis_ingested = self.ingest_vectorbt_analysis(results)
            
            # Cleanup old data
            self.cleanup_old_data()
            
            # Close database connection
            self.close_database()
            
            return {
                'success': True,
                'files_processed': list(files.values()),
                'total_results': len(results),
                'alerts_ingested': alerts_ingested,
                'analysis_ingested': analysis_ingested,
                'validation_errors': validation_errors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            if self.connection:
                self.close_database()
            return {'error': str(e)}

def main():
    """Main function for running the VectorBTPro ingestion system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest VectorBTPro analysis results into database')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--engine-results-dir', default='../autonama.engine/results', 
                       help='Directory containing engine results')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days to keep data')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    # Database configuration
    db_config = {
        'host': config.get('database_host', 'localhost'),
        'port': config.get('database_port', 5432),
        'database': config.get('database_name', 'autonama'),
        'user': config.get('database_user', 'postgres'),
        'password': config.get('database_password', 'postgres')
    }
    
    # Initialize and run ingestion
    processor = VectorBTIngestionProcessor(db_config)
    results = processor.process_engine_results(args.engine_results_dir)
    
    if 'error' in results:
        print(f"❌ Ingestion failed: {results['error']}")
        if 'validation_errors' in results:
            print("Validation errors:")
            for error in results['validation_errors']:
                print(f"  - {error}")
    else:
        print(f"✅ VectorBTPro ingestion completed successfully!")
        print(f"📁 Files processed: {', '.join(results['files_processed'])}")
        print(f"📊 Total results: {results['total_results']}")
        print(f"📊 Alerts ingested: {results['alerts_ingested']}")
        print(f"📈 Analysis ingested: {results['analysis_ingested']}")

if __name__ == "__main__":
    main() 
"""
VectorBTPro Results Ingestion System

This system acts as a clean bridge between the local VectorBTPro engine
and the main Docker system. It validates and processes output files
before ingestion into PostgreSQL.

Designed to run in the same conda environment as VectorBTPro.

Key Features:
- Validates output files for completeness and accuracy
- Processes both CSV and JSON formats
- Ensures data integrity before database insertion
- Provides detailed validation reports
- Clean error handling and logging
- Uses VectorBTPro for enhanced validation
"""

import os
import json
import logging
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import glob
from psycopg2.extras import RealDictCursor
import hashlib
import re

# Try to import VectorBTPro for enhanced validation
try:
    import vectorbtpro as vbt
    VECTORBT_AVAILABLE = True
    print(f"✅ VectorBTPro {vbt.__version__} available for enhanced validation")
except ImportError:
    VECTORBT_AVAILABLE = False
    print("⚠️ VectorBTPro not available, using basic validation")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("vectorbt_ingestion.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VectorBTIngestionValidator:
    """Validates VectorBTPro output files before ingestion"""
    
    def __init__(self):
        self.required_csv_columns = [
            'symbol', 'interval', 'current_price', 'lower_band', 'upper_band',
            'signal', 'potential_return', 'total_return', 'sharpe_ratio', 
            'max_drawdown', 'degree', 'kstd', 'analysis_date'
        ]
        
        self.required_json_fields = [
            'symbol', 'interval', 'current_price', 'lower_band', 'upper_band',
            'signal', 'potential_return', 'total_return', 'sharpe_ratio',
            'max_drawdown', 'degree', 'kstd', 'analysis_date'
        ]
        
        self.valid_signals = ['BUY', 'SELL', 'HOLD']
        self.valid_intervals = ['1d', '4h', '1h', '15m', '5m', '1m']
        
        # VectorBTPro validation settings
        self.use_vectorbt_validation = VECTORBT_AVAILABLE
    
    def validate_csv_file(self, filepath: str) -> Tuple[bool, List[str]]:
        """
        Validate CSV output file from VectorBTPro engine
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check file exists
            if not os.path.exists(filepath):
                errors.append(f"File does not exist: {filepath}")
                return False, errors
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                errors.append("File is empty")
                return False, errors
            
            # Read CSV
            df = pd.read_csv(filepath)
            
            # Check for required columns
            missing_columns = set(self.required_csv_columns) - set(df.columns)
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Check for empty dataframe
            if df.empty:
                errors.append("DataFrame is empty")
                return False, errors
            
            # Validate data types and ranges
            for index, row in df.iterrows():
                row_errors = self._validate_row(row, index)
                errors.extend(row_errors)
            
            # Check for duplicate symbols
            duplicates = df['symbol'].duplicated()
            if duplicates.any():
                duplicate_symbols = df[duplicates]['symbol'].tolist()
                errors.append(f"Duplicate symbols found: {duplicate_symbols}")
            
            # Validate analysis date format
            if 'analysis_date' in df.columns:
                try:
                    pd.to_datetime(df['analysis_date'])
                except:
                    errors.append("Invalid analysis_date format")
            
            # Enhanced validation with VectorBTPro if available
            if self.use_vectorbt_validation and not errors:
                vectorbt_errors = self._validate_with_vectorbt(df)
                errors.extend(vectorbt_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error reading CSV file: {str(e)}")
            return False, errors
    
    def validate_json_file(self, filepath: str) -> Tuple[bool, List[str]]:
        """
        Validate JSON output file from VectorBTPro engine
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check file exists
            if not os.path.exists(filepath):
                errors.append(f"File does not exist: {filepath}")
                return False, errors
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                errors.append("File is empty")
                return False, errors
            
            # Read JSON
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Check if data is a list
            if not isinstance(data, list):
                errors.append("JSON data must be a list of objects")
                return False, errors
            
            if len(data) == 0:
                errors.append("JSON data is empty")
                return False, errors
            
            # Validate each record
            symbols = set()
            for index, record in enumerate(data):
                if not isinstance(record, dict):
                    errors.append(f"Record {index} is not a dictionary")
                    continue
                
                # Check for required fields
                missing_fields = set(self.required_json_fields) - set(record.keys())
                if missing_fields:
                    errors.append(f"Record {index} missing fields: {missing_fields}")
                
                # Validate symbol format
                symbol = record.get('symbol', '')
                if not self._is_valid_symbol(symbol):
                    errors.append(f"Record {index} has invalid symbol: {symbol}")
                else:
                    if symbol in symbols:
                        errors.append(f"Duplicate symbol found: {symbol}")
                    else:
                        symbols.add(symbol)
                
                # Validate other fields
                row_errors = self._validate_record(record, index)
                errors.extend(row_errors)
            
            # Enhanced validation with VectorBTPro if available
            if self.use_vectorbt_validation and not errors:
                df = pd.DataFrame(data)
                vectorbt_errors = self._validate_with_vectorbt(df)
                errors.extend(vectorbt_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Error reading JSON file: {str(e)}")
            return False, errors
    
    def _validate_with_vectorbt(self, df: pd.DataFrame) -> List[str]:
        """
        Enhanced validation using VectorBTPro
        
        Args:
            df: DataFrame to validate
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if not VECTORBT_AVAILABLE:
            return errors
        
        try:
            # Check if results look like VectorBTPro output
            if 'total_return' in df.columns and 'sharpe_ratio' in df.columns:
                # Validate that returns are reasonable
                total_returns = pd.to_numeric(df['total_return'], errors='coerce')
                sharpe_ratios = pd.to_numeric(df['sharpe_ratio'], errors='coerce')
                
                # Check for extreme values
                if total_returns.max() > 1000:  # 1000% return
                    errors.append("Unrealistic total return values detected (>1000%)")
                
                if sharpe_ratios.max() > 10:  # Very high Sharpe ratio
                    errors.append("Unrealistic Sharpe ratio values detected (>10)")
                
                # Check for negative Sharpe ratios (might indicate poor strategy)
                negative_sharpe = (sharpe_ratios < 0).sum()
                if negative_sharpe > len(df) * 0.5:  # More than 50% negative
                    errors.append(f"High number of negative Sharpe ratios: {negative_sharpe}")
            
            # Validate price relationships
            if all(col in df.columns for col in ['current_price', 'lower_band', 'upper_band']):
                current_prices = pd.to_numeric(df['current_price'], errors='coerce')
                lower_bands = pd.to_numeric(df['lower_band'], errors='coerce')
                upper_bands = pd.to_numeric(df['upper_band'], errors='coerce')
                
                # Check for invalid band relationships
                invalid_bands = (lower_bands >= upper_bands).sum()
                if invalid_bands > 0:
                    errors.append(f"Invalid band relationships found: {invalid_bands} records")
                
                # Check for extreme price movements
                price_changes = ((upper_bands - lower_bands) / lower_bands * 100).abs()
                extreme_moves = (price_changes > 100).sum()  # >100% move
                if extreme_moves > len(df) * 0.1:  # More than 10% extreme moves
                    errors.append(f"High number of extreme price movements: {extreme_moves}")
            
        except Exception as e:
            errors.append(f"VectorBTPro validation error: {str(e)}")
        
        return errors
    
    def _validate_row(self, row: pd.Series, index: int) -> List[str]:
        """Validate a single CSV row"""
        errors = []
        
        # Validate symbol
        symbol = row.get('symbol', '')
        if not self._is_valid_symbol(symbol):
            errors.append(f"Row {index}: Invalid symbol format: {symbol}")
        
        # Validate interval
        interval = row.get('interval', '')
        if interval not in self.valid_intervals:
            errors.append(f"Row {index}: Invalid interval: {interval}")
        
        # Validate signal
        signal = row.get('signal', '')
        if signal not in self.valid_signals:
            errors.append(f"Row {index}: Invalid signal: {signal}")
        
        # Validate numeric fields
        numeric_fields = ['current_price', 'lower_band', 'upper_band', 'potential_return', 
                         'total_return', 'sharpe_ratio', 'max_drawdown', 'degree', 'kstd']
        
        for field in numeric_fields:
            value = row.get(field)
            if pd.isna(value):
                errors.append(f"Row {index}: Missing {field}")
            elif not isinstance(value, (int, float)):
                try:
                    float(value)
                except:
                    errors.append(f"Row {index}: Invalid {field}: {value}")
        
        # Validate price relationships
        current_price = row.get('current_price')
        lower_band = row.get('lower_band')
        upper_band = row.get('upper_band')
        
        if all(pd.notna([current_price, lower_band, upper_band])):
            if lower_band >= upper_band:
                errors.append(f"Row {index}: Lower band >= Upper band")
        
        return errors
    
    def _validate_record(self, record: Dict, index: int) -> List[str]:
        """Validate a single JSON record"""
        errors = []
        
        # Validate symbol
        symbol = record.get('symbol', '')
        if not self._is_valid_symbol(symbol):
            errors.append(f"Record {index}: Invalid symbol format: {symbol}")
        
        # Validate interval
        interval = record.get('interval', '')
        if interval not in self.valid_intervals:
            errors.append(f"Record {index}: Invalid interval: {interval}")
        
        # Validate signal
        signal = record.get('signal', '')
        if signal not in self.valid_signals:
            errors.append(f"Record {index}: Invalid signal: {signal}")
        
        # Validate numeric fields
        numeric_fields = ['current_price', 'lower_band', 'upper_band', 'potential_return', 
                         'total_return', 'sharpe_ratio', 'max_drawdown', 'degree', 'kstd']
        
        for field in numeric_fields:
            value = record.get(field)
            if value is None:
                errors.append(f"Record {index}: Missing {field}")
            elif not isinstance(value, (int, float)):
                try:
                    float(value)
                except:
                    errors.append(f"Record {index}: Invalid {field}: {value}")
        
        # Validate price relationships
        current_price = record.get('current_price')
        lower_band = record.get('lower_band')
        upper_band = record.get('upper_band')
        
        if all(v is not None for v in [current_price, lower_band, upper_band]):
            if lower_band >= upper_band:
                errors.append(f"Record {index}: Lower band >= Upper band")
        
        return errors
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol follows valid format"""
        if not isinstance(symbol, str):
            return False
        
        # Check for valid crypto symbol format (e.g., BTCUSDT, ETHUSDT)
        pattern = r'^[A-Z0-9]+USDT$'
        return bool(re.match(pattern, symbol))

class VectorBTIngestionProcessor:
    """Processes validated VectorBTPro results for database ingestion"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection = None
        self.validator = VectorBTIngestionValidator()
    
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
    
    def find_latest_results(self, engine_results_dir: str) -> Dict[str, str]:
        """
        Find the latest VectorBTPro results files
        
        Args:
            engine_results_dir: Directory containing engine results
        
        Returns:
            Dictionary with file paths for CSV and JSON
        """
        try:
            files = {}
            
            # Find latest CSV file
            csv_pattern = os.path.join(engine_results_dir, "vectorbt_analysis_results_*.csv")
            csv_files = glob.glob(csv_pattern)
            if csv_files:
                csv_files.sort(key=os.path.getmtime, reverse=True)
                files['csv'] = csv_files[0]
                logger.info(f"Found latest CSV file: {files['csv']}")
            
            # Find latest JSON file
            json_pattern = os.path.join(engine_results_dir, "vectorbt_analysis_results_*.json")
            json_files = glob.glob(json_pattern)
            if json_files:
                json_files.sort(key=os.path.getmtime, reverse=True)
                files['json'] = json_files[0]
                logger.info(f"Found latest JSON file: {files['json']}")
            
            if not files:
                logger.warning(f"No VectorBTPro results files found in {engine_results_dir}")
            
            return files
            
        except Exception as e:
            logger.error(f"Error finding latest results files: {e}")
            return {}
    
    def validate_and_load_results(self, files: Dict[str, str]) -> Tuple[List[Dict], List[str]]:
        """
        Validate and load results from files
        
        Args:
            files: Dictionary with file paths
        
        Returns:
            Tuple of (valid_results, validation_errors)
        """
        all_results = []
        all_errors = []
        
        # Validate and load CSV
        if 'csv' in files:
            is_valid, errors = self.validator.validate_csv_file(files['csv'])
            if is_valid:
                try:
                    df = pd.read_csv(files['csv'])
                    results = df.to_dict('records')
                    all_results.extend(results)
                    logger.info(f"Successfully loaded {len(results)} results from CSV")
                except Exception as e:
                    all_errors.append(f"Error loading CSV: {e}")
            else:
                all_errors.extend(errors)
                logger.error(f"CSV validation failed: {errors}")
        
        # Validate and load JSON
        if 'json' in files:
            is_valid, errors = self.validator.validate_json_file(files['json'])
            if is_valid:
                try:
                    with open(files['json'], 'r') as f:
                        results = json.load(f)
                    all_results.extend(results)
                    logger.info(f"Successfully loaded {len(results)} results from JSON")
                except Exception as e:
                    all_errors.append(f"Error loading JSON: {e}")
            else:
                all_errors.extend(errors)
                logger.error(f"JSON validation failed: {errors}")
        
        # Remove duplicates
        if all_results:
            seen = set()
            unique_results = []
            for result in all_results:
                key = f"{result.get('symbol')}_{result.get('interval', '1d')}"
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            all_results = unique_results
        
        return all_results, all_errors
    
    def create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist"""
        try:
            with self.connection.cursor() as cursor:
                # Create alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trading.alerts (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        interval VARCHAR(10) NOT NULL,
                        signal VARCHAR(10) NOT NULL,
                        current_price NUMERIC(20,8),
                        upper_band NUMERIC(20,8),
                        lower_band NUMERIC(20,8),
                        potential_return NUMERIC(10,4),
                        total_return NUMERIC(10,4),
                        sharpe_ratio NUMERIC(10,4),
                        max_drawdown NUMERIC(10,4),
                        degree INTEGER,
                        kstd NUMERIC(5,2),
                        analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create vectorbt_analysis table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trading.vectorbt_analysis (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        interval VARCHAR(10) NOT NULL,
                        analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        current_price NUMERIC(20,8),
                        lower_band NUMERIC(20,8),
                        upper_band NUMERIC(20,8),
                        signal VARCHAR(10),
                        potential_return NUMERIC(10,4),
                        total_return NUMERIC(10,4),
                        sharpe_ratio NUMERIC(10,4),
                        max_drawdown NUMERIC(10,4),
                        degree INTEGER,
                        kstd NUMERIC(5,2),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON trading.alerts(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_signal ON trading.alerts(signal)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_date ON trading.alerts(analysis_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectorbt_symbol ON trading.vectorbt_analysis(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vectorbt_date ON trading.vectorbt_analysis(analysis_date)")
                
                self.connection.commit()
                logger.info("Tables created/verified successfully")
                
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.connection.rollback()
            raise
    
    def ingest_alerts(self, results: List[Dict]) -> int:
        """
        Ingest alert signals into the database
        
        Args:
            results: List of validated analysis results
        
        Returns:
            Number of alerts ingested
        """
        try:
            ingested_count = 0
            
            with self.connection.cursor() as cursor:
                for result in results:
                    symbol = result['symbol']
                    signal = result.get('signal', 'HOLD')
                    
                    # Check if alert already exists for this symbol today
                    cursor.execute("""
                        SELECT id FROM trading.alerts 
                        WHERE symbol = %s AND analysis_date::date = CURRENT_DATE
                    """, (symbol,))
                    
                    existing_alert = cursor.fetchone()
                    
                    if existing_alert:
                        # Update existing alert
                        cursor.execute("""
                            UPDATE trading.alerts SET
                                signal = %s,
                                current_price = %s,
                                upper_band = %s,
                                lower_band = %s,
                                potential_return = %s,
                                total_return = %s,
                                sharpe_ratio = %s,
                                max_drawdown = %s,
                                degree = %s,
                                kstd = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (
                            signal,
                            result.get('current_price'),
                            result.get('upper_band'),
                            result.get('lower_band'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd'),
                            existing_alert[0]
                        ))
                        logger.info(f"Updated alert for {symbol}")
                    else:
                        # Insert new alert
                        cursor.execute("""
                            INSERT INTO trading.alerts (
                                symbol, interval, signal, current_price, upper_band, lower_band,
                                potential_return, total_return, sharpe_ratio, max_drawdown, degree, kstd
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            symbol,
                            result.get('interval', '1d'),
                            signal,
                            result.get('current_price'),
                            result.get('upper_band'),
                            result.get('lower_band'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd')
                        ))
                        logger.info(f"Inserted new alert for {symbol}")
                    
                    ingested_count += 1
            
            self.connection.commit()
            logger.info(f"Successfully ingested {ingested_count} alerts")
            return ingested_count
            
        except Exception as e:
            logger.error(f"Error ingesting alerts: {e}")
            self.connection.rollback()
            return 0
    
    def ingest_vectorbt_analysis(self, results: List[Dict]) -> int:
        """
        Ingest detailed VectorBTPro analysis into the database
        
        Args:
            results: List of validated analysis results
        
        Returns:
            Number of analysis records ingested
        """
        try:
            ingested_count = 0
            
            with self.connection.cursor() as cursor:
                for result in results:
                    symbol = result['symbol']
                    
                    # Check if analysis already exists for this symbol today
                    cursor.execute("""
                        SELECT id FROM trading.vectorbt_analysis 
                        WHERE symbol = %s AND analysis_date::date = CURRENT_DATE
                    """, (symbol,))
                    
                    existing_analysis = cursor.fetchone()
                    
                    if existing_analysis:
                        # Update existing analysis
                        cursor.execute("""
                            UPDATE trading.vectorbt_analysis SET
                                current_price = %s,
                                lower_band = %s,
                                upper_band = %s,
                                signal = %s,
                                potential_return = %s,
                                total_return = %s,
                                sharpe_ratio = %s,
                                max_drawdown = %s,
                                degree = %s,
                                kstd = %s
                            WHERE id = %s
                        """, (
                            result.get('current_price'),
                            result.get('lower_band'),
                            result.get('upper_band'),
                            result.get('signal'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd'),
                            existing_analysis[0]
                        ))
                        logger.info(f"Updated analysis for {symbol}")
                    else:
                        # Insert new analysis
                        cursor.execute("""
                            INSERT INTO trading.vectorbt_analysis (
                                symbol, interval, current_price, lower_band, upper_band,
                                signal, potential_return, total_return, sharpe_ratio, max_drawdown,
                                degree, kstd
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            symbol,
                            result.get('interval', '1d'),
                            result.get('current_price'),
                            result.get('lower_band'),
                            result.get('upper_band'),
                            result.get('signal'),
                            result.get('potential_return'),
                            result.get('total_return'),
                            result.get('sharpe_ratio'),
                            result.get('max_drawdown'),
                            result.get('degree'),
                            result.get('kstd')
                        ))
                        logger.info(f"Inserted new analysis for {symbol}")
                    
                    ingested_count += 1
            
            self.connection.commit()
            logger.info(f"Successfully ingested {ingested_count} VectorBTPro analysis records")
            return ingested_count
            
        except Exception as e:
            logger.error(f"Error ingesting VectorBTPro analysis: {e}")
            self.connection.rollback()
            return 0
    
    def cleanup_old_data(self, days: int = 30):
        """
        Clean up old data to prevent database bloat
        
        Args:
            days: Number of days to keep data
        """
        try:
            with self.connection.cursor() as cursor:
                # Clean up old alerts
                cursor.execute("""
                    DELETE FROM trading.alerts 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days,))
                alerts_deleted = cursor.rowcount
                
                # Clean up old VectorBTPro analysis
                cursor.execute("""
                    DELETE FROM trading.vectorbt_analysis 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days,))
                analysis_deleted = cursor.rowcount
                
                self.connection.commit()
                logger.info(f"Cleanup completed: {alerts_deleted} alerts, {analysis_deleted} analysis records deleted")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            self.connection.rollback()
    
    def process_engine_results(self, engine_results_dir: str) -> Dict:
        """
        Main processing function: validate and ingest VectorBTPro results
        
        Args:
            engine_results_dir: Directory containing engine output files
        
        Returns:
            Dictionary with processing results
        """
        try:
            # Connect to database
            self.connect_database()
            
            # Create tables if they don't exist
            self.create_tables_if_not_exist()
            
            # Find latest results files
            files = self.find_latest_results(engine_results_dir)
            if not files:
                return {'error': 'No VectorBTPro results files found'}
            
            # Validate and load results
            results, validation_errors = self.validate_and_load_results(files)
            
            if validation_errors:
                logger.error(f"Validation errors found: {validation_errors}")
                return {
                    'error': 'Validation failed',
                    'validation_errors': validation_errors,
                    'files_checked': list(files.values())
                }
            
            if not results:
                return {'error': 'No valid results found after validation'}
            
            # Ingest data
            alerts_ingested = self.ingest_alerts(results)
            analysis_ingested = self.ingest_vectorbt_analysis(results)
            
            # Cleanup old data
            self.cleanup_old_data()
            
            # Close database connection
            self.close_database()
            
            return {
                'success': True,
                'files_processed': list(files.values()),
                'total_results': len(results),
                'alerts_ingested': alerts_ingested,
                'analysis_ingested': analysis_ingested,
                'validation_errors': validation_errors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            if self.connection:
                self.close_database()
            return {'error': str(e)}

def main():
    """Main function for running the VectorBTPro ingestion system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest VectorBTPro analysis results into database')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--engine-results-dir', default='../autonama.engine/results', 
                       help='Directory containing engine results')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days to keep data')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    # Database configuration
    db_config = {
        'host': config.get('database_host', 'localhost'),
        'port': config.get('database_port', 5432),
        'database': config.get('database_name', 'autonama'),
        'user': config.get('database_user', 'postgres'),
        'password': config.get('database_password', 'postgres')
    }
    
    # Initialize and run ingestion
    processor = VectorBTIngestionProcessor(db_config)
    results = processor.process_engine_results(args.engine_results_dir)
    
    if 'error' in results:
        print(f"❌ Ingestion failed: {results['error']}")
        if 'validation_errors' in results:
            print("Validation errors:")
            for error in results['validation_errors']:
                print(f"  - {error}")
    else:
        print(f"✅ VectorBTPro ingestion completed successfully!")
        print(f"📁 Files processed: {', '.join(results['files_processed'])}")
        print(f"📊 Total results: {results['total_results']}")
        print(f"📊 Alerts ingested: {results['alerts_ingested']}")
        print(f"📈 Analysis ingested: {results['analysis_ingested']}")

if __name__ == "__main__":
    main() 
 