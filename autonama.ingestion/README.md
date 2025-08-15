# 🔄 Autonama Ingestion System

## Overview

The Autonama Ingestion System acts as a **clean bridge** between local analysis engines and the main Docker system. It validates and processes output files from local engines before safely ingesting them into the PostgreSQL database.

**Designed to run in the same conda environment as VectorBTPro** for seamless integration.

## 🎯 Key Features

### 🔍 **Comprehensive Validation**
- **File Integrity**: Checks file existence, size, and format
- **Data Validation**: Validates all required fields and data types
- **Business Logic**: Ensures price relationships and signal validity
- **Duplicate Detection**: Prevents duplicate data ingestion
- **VectorBTPro Enhanced**: Uses VectorBTPro for advanced validation when available

### 🛡️ **Safety & Reliability**
- **Validation First**: All files are validated before ingestion
- **Error Handling**: Detailed error reporting and logging
- **Rollback Support**: Database transactions with rollback capability
- **Data Integrity**: Ensures data consistency and accuracy

### 🔄 **Multi-Engine Support**
- **VectorBTPro Engine**: Processes VectorBTPro analysis results
- **Enhanced Engine**: Ready for enhanced analysis results
- **Extensible**: Easy to add support for new engines

### 📊 **Database Integration**
- **PostgreSQL Tables**: Creates and manages database tables
- **Data Cleanup**: Automatic cleanup of old data
- **Indexing**: Optimized database performance
- **Transaction Safety**: ACID-compliant database operations

## 🏗️ Architecture

```
Local Engine → Output Files → Ingestion System → Validation → Database → Web App
     ↓              ↓              ↓              ↓           ↓         ↓
autonama.engine  CSV/JSON    autonama.ingestion  Checks   PostgreSQL  Dashboard
```

## 📁 File Structure

```
autonama.ingestion/
├── __init__.py                 # Package initialization
├── vectorbt_ingestion.py       # VectorBTPro ingestion processor
├── run_ingestion.py           # Main ingestion runner
├── config.json                # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── logs/                     # Log files
    └── ingestion.log
```

## 🚀 Quick Start

### **Step 1: Activate Conda Environment**

```bash
# Activate the VectorBTPro conda environment
conda activate autonama_vectorbt

# Verify VectorBTPro is available
python -c "import vectorbtpro; print(f'VectorBTPro {vectorbtpro.__version__} available')"
```

### **Step 2: Install Dependencies**

```bash
# Install ingestion system dependencies (in same conda environment)
pip install -r requirements.txt
```

### **Step 3: Configure Database**

Edit `config.json` with your database settings:

```json
{
    "binance_api_key": "your_binance_api_key_here",
    "binance_api_secret": "your_binance_api_secret_here",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres"
}
```

### **Step 4: Run Ingestion**

```bash
# Ingest VectorBTPro results
python run_ingestion.py --engine vectorbt --config config.json

# Ingest with custom results directory
python run_ingestion.py --engine vectorbt --engine-results-dir /path/to/results

# Validate only (no database changes)
python run_ingestion.py --engine vectorbt --validate-only

# Skip conda environment check
python run_ingestion.py --engine vectorbt --skip-conda-check
```

## 📊 Validation Process

### **File Validation**
- ✅ File exists and is readable
- ✅ File size > 0 bytes
- ✅ Correct file format (CSV/JSON)
- ✅ File age within acceptable range

### **Data Validation**
- ✅ All required columns/fields present
- ✅ Correct data types (numeric, string, etc.)
- ✅ Valid symbol format (e.g., BTCUSDT)
- ✅ Valid signal values (BUY/SELL/HOLD)
- ✅ Valid interval values (1d, 4h, 1h, etc.)
- ✅ Price relationships (lower_band < upper_band)
- ✅ No duplicate symbols

### **VectorBTPro Enhanced Validation**
- ✅ Realistic return values (< 1000%)
- ✅ Reasonable Sharpe ratios (< 10)
- ✅ Valid price band relationships
- ✅ Extreme price movement detection
- ✅ Strategy performance analysis

### **Business Logic Validation**
- ✅ Current price within reasonable range
- ✅ Potential return calculations valid
- ✅ Sharpe ratio and drawdown values reasonable
- ✅ Analysis date format correct

## 🗄️ Database Tables

### **trading.alerts**
Stores signal alerts for the web application:

```sql
CREATE TABLE trading.alerts (
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
);
```

### **trading.vectorbt_analysis**
Stores detailed VectorBTPro analysis results:

```sql
CREATE TABLE trading.vectorbt_analysis (
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
);
```

## 🔧 Configuration

### **config.json Options**

```json
{
    "binance_api_key": "your_binance_api_key_here",
    "binance_api_secret": "your_binance_api_secret_here",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres",
    "engine_results_dir": "../autonama.engine/results",
    "cleanup_days": 30,
    "validation": {
        "strict_mode": true,
        "check_duplicates": true,
        "validate_prices": true,
        "max_file_age_hours": 24
    },
    "vectorbt": {
        "enabled": true,
        "results_pattern": "vectorbt_analysis_results_*.csv",
        "json_pattern": "vectorbt_analysis_results_*.json"
    },
    "logging": {
        "level": "INFO",
        "file": "ingestion.log",
        "max_size_mb": 10,
        "backup_count": 5
    }
}
```

## 🚨 Important Notes

### **Conda Environment**
- **Must run in VectorBTPro conda environment**: `conda activate autonama_vectorbt`
- **VectorBTPro License**: Requires active VectorBTPro license
- **Shared Dependencies**: Uses same environment as engine for consistency

### **Local Processing**
- All intensive computation runs locally using VectorBTPro
- No cloud costs for analysis processing
- Results are stored in cloud database for display

### **API Limits**
- Binance API has rate limits
- Use caching to minimize API calls
- Process assets in batches if needed

### **Data Retention**
- Historical data cached locally for 24 hours
- Database cleanup removes old data after 30 days
- Local SQLite database for historical data storage

## 🔄 Integration Workflow

### **Complete Workflow**
1. **Engine Analysis**: Run VectorBTPro engine locally
2. **File Generation**: Engine creates CSV/JSON output files
3. **Ingestion**: Run ingestion system to validate and process
4. **Database Update**: Results stored in PostgreSQL
5. **Web Display**: Dashboard shows updated alerts and analytics

### **Automation Script**
```bash
#!/bin/bash
# daily_analysis_and_ingestion.sh

# Activate conda environment
conda activate autonama_vectorbt

# Run VectorBTPro analysis
cd autonama.engine
python run_vectorbt_analysis.py --config config.json --top-100 --optimize

# Ingest results
cd ../autonama.ingestion
python run_ingestion.py --engine vectorbt --config config.json

echo "Daily VectorBTPro analysis and ingestion complete!"
```

## 📈 Usage Examples

### **Basic Ingestion**
```bash
# Activate conda environment
conda activate autonama_vectorbt

# Ingest latest VectorBTPro results
python run_ingestion.py --engine vectorbt
```

### **Custom Configuration**
```bash
# Use custom config and results directory
python run_ingestion.py \
    --engine vectorbt \
    --config custom_config.json \
    --engine-results-dir /custom/path/to/results
```

### **Validation Only**
```bash
# Validate files without database changes
python run_ingestion.py --engine vectorbt --validate-only
```

### **Cleanup Old Data**
```bash
# Keep only 7 days of data
python run_ingestion.py --engine vectorbt --cleanup-days 7
```

## 🔍 Monitoring & Logs

### **Log Files**
- `ingestion.log`: Main ingestion logs
- `vectorbt_ingestion.log`: VectorBTPro-specific logs

### **Log Levels**
- `INFO`: Normal operation messages
- `WARNING`: Validation warnings
- `ERROR`: Errors that prevent ingestion
- `DEBUG`: Detailed debugging information

### **Success Indicators**
- ✅ "Ingestion completed successfully" message
- ✅ Database records inserted/updated
- ✅ No validation errors in logs
- ✅ Web dashboard showing updated data

## 🚨 Error Handling

### **Common Issues**

#### **Conda Environment**
```
❌ VectorBTPro not found. Please activate the correct conda environment.
   Run: conda activate autonama_vectorbt
```
**Solution**: Activate the VectorBTPro conda environment before running ingestion.

#### **File Not Found**
```
❌ Error: Engine results directory does not exist
```
**Solution**: Ensure the engine has generated results before running ingestion.

#### **Validation Errors**
```
❌ Ingestion failed: Validation failed
🔍 VALIDATION ERRORS:
  - Row 5: Invalid symbol format: BTC
  - Row 12: Missing current_price
```
**Solution**: Check engine output files for data quality issues.

#### **Database Connection**
```
❌ Database connection failed
```
**Solution**: Verify database is running and credentials are correct.

#### **Permission Errors**
```
❌ Error: Permission denied
```
**Solution**: Check file permissions and database user privileges.

## 🔄 Integration with Main System

### **Data Flow**
```
Local Conda Environment → VectorBTPro Engine → CSV/JSON Results → Ingestion System → PostgreSQL → Web Application
```

### **Schedule Recommendations**
- **Daily Analysis**: Run analysis once per day
- **Weekly Optimization**: Re-optimize parameters weekly
- **Monthly Cleanup**: Database cleanup monthly

### **Automation Script**
```bash
#!/bin/bash
# daily_analysis_and_ingestion.sh

# Activate conda environment
conda activate autonama_vectorbt

# Run VectorBTPro analysis
cd autonama.engine
python run_vectorbt_analysis.py --config config.json --top-100 --optimize

# Ingest results
cd ../autonama.ingestion
python run_ingestion.py --engine vectorbt --config config.json

echo "Daily VectorBTPro analysis and ingestion complete!"
```

## 🛠️ Advanced Usage

### **Custom Validation**
```python
from vectorbt_ingestion import VectorBTIngestionValidator

# Create custom validator
validator = VectorBTIngestionValidator()

# Validate specific file
is_valid, errors = validator.validate_csv_file('path/to/file.csv')
if not is_valid:
    print(f"Validation errors: {errors}")
```

### **Custom Processor**
```python
from vectorbt_ingestion import VectorBTIngestionProcessor

# Create processor with custom config
processor = VectorBTIngestionProcessor(db_config)

# Process results
results = processor.process_engine_results('/path/to/results')
```

## 🎯 Best Practices

### **Conda Environment Management**
- ✅ Always activate conda environment before running
- ✅ Verify VectorBTPro is available
- ✅ Use same environment for engine and ingestion
- ✅ Keep environment dependencies updated

### **File Management**
- ✅ Keep engine results organized by date
- ✅ Archive old results files
- ✅ Monitor disk space usage
- ✅ Use consistent file naming

### **Database Management**
- ✅ Regular cleanup of old data
- ✅ Monitor database size
- ✅ Backup important data
- ✅ Use appropriate indexes

### **Validation**
- ✅ Always validate before ingestion
- ✅ Check file age and freshness
- ✅ Verify data relationships
- ✅ Monitor validation error rates

### **Monitoring**
- ✅ Check logs regularly
- ✅ Monitor ingestion success rates
- ✅ Track database performance
- ✅ Verify web dashboard updates

## 🚨 Troubleshooting

### **Conda Environment Issues**
1. Verify conda environment is activated
2. Check VectorBTPro installation
3. Ensure all dependencies are installed
4. Verify license is active

### **Validation Issues**
1. Check engine output file format
2. Verify all required fields are present
3. Ensure data types are correct
4. Check for duplicate entries

### **Database Issues**
1. Verify database connection
2. Check user permissions
3. Ensure tables exist
4. Monitor disk space

### **Performance Issues**
1. Optimize database queries
2. Use appropriate indexes
3. Clean up old data regularly
4. Monitor system resources

## 📞 Support

For issues with the ingestion system:
1. Check the log files for detailed error messages
2. Verify engine output files are valid
3. Ensure database connection is working
4. Validate configuration settings
5. Check file permissions and paths
6. Verify conda environment is activated

---

**The Autonama Ingestion System ensures clean, validated data flows from local VectorBTPro analysis engines to the main web application, providing a reliable bridge between local processing and cloud-based display.** 

## Overview

The Autonama Ingestion System acts as a **clean bridge** between local analysis engines and the main Docker system. It validates and processes output files from local engines before safely ingesting them into the PostgreSQL database.

**Designed to run in the same conda environment as VectorBTPro** for seamless integration.

## 🎯 Key Features

### 🔍 **Comprehensive Validation**
- **File Integrity**: Checks file existence, size, and format
- **Data Validation**: Validates all required fields and data types
- **Business Logic**: Ensures price relationships and signal validity
- **Duplicate Detection**: Prevents duplicate data ingestion
- **VectorBTPro Enhanced**: Uses VectorBTPro for advanced validation when available

### 🛡️ **Safety & Reliability**
- **Validation First**: All files are validated before ingestion
- **Error Handling**: Detailed error reporting and logging
- **Rollback Support**: Database transactions with rollback capability
- **Data Integrity**: Ensures data consistency and accuracy

### 🔄 **Multi-Engine Support**
- **VectorBTPro Engine**: Processes VectorBTPro analysis results
- **Enhanced Engine**: Ready for enhanced analysis results
- **Extensible**: Easy to add support for new engines

### 📊 **Database Integration**
- **PostgreSQL Tables**: Creates and manages database tables
- **Data Cleanup**: Automatic cleanup of old data
- **Indexing**: Optimized database performance
- **Transaction Safety**: ACID-compliant database operations

## 🏗️ Architecture

```
Local Engine → Output Files → Ingestion System → Validation → Database → Web App
     ↓              ↓              ↓              ↓           ↓         ↓
autonama.engine  CSV/JSON    autonama.ingestion  Checks   PostgreSQL  Dashboard
```

## 📁 File Structure

```
autonama.ingestion/
├── __init__.py                 # Package initialization
├── vectorbt_ingestion.py       # VectorBTPro ingestion processor
├── run_ingestion.py           # Main ingestion runner
├── config.json                # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── logs/                     # Log files
    └── ingestion.log
```

## 🚀 Quick Start

### **Step 1: Activate Conda Environment**

```bash
# Activate the VectorBTPro conda environment
conda activate autonama_vectorbt

# Verify VectorBTPro is available
python -c "import vectorbtpro; print(f'VectorBTPro {vectorbtpro.__version__} available')"
```

### **Step 2: Install Dependencies**

```bash
# Install ingestion system dependencies (in same conda environment)
pip install -r requirements.txt
```

### **Step 3: Configure Database**

Edit `config.json` with your database settings:

```json
{
    "binance_api_key": "your_binance_api_key_here",
    "binance_api_secret": "your_binance_api_secret_here",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres"
}
```

### **Step 4: Run Ingestion**

```bash
# Ingest VectorBTPro results
python run_ingestion.py --engine vectorbt --config config.json

# Ingest with custom results directory
python run_ingestion.py --engine vectorbt --engine-results-dir /path/to/results

# Validate only (no database changes)
python run_ingestion.py --engine vectorbt --validate-only

# Skip conda environment check
python run_ingestion.py --engine vectorbt --skip-conda-check
```

## 📊 Validation Process

### **File Validation**
- ✅ File exists and is readable
- ✅ File size > 0 bytes
- ✅ Correct file format (CSV/JSON)
- ✅ File age within acceptable range

### **Data Validation**
- ✅ All required columns/fields present
- ✅ Correct data types (numeric, string, etc.)
- ✅ Valid symbol format (e.g., BTCUSDT)
- ✅ Valid signal values (BUY/SELL/HOLD)
- ✅ Valid interval values (1d, 4h, 1h, etc.)
- ✅ Price relationships (lower_band < upper_band)
- ✅ No duplicate symbols

### **VectorBTPro Enhanced Validation**
- ✅ Realistic return values (< 1000%)
- ✅ Reasonable Sharpe ratios (< 10)
- ✅ Valid price band relationships
- ✅ Extreme price movement detection
- ✅ Strategy performance analysis

### **Business Logic Validation**
- ✅ Current price within reasonable range
- ✅ Potential return calculations valid
- ✅ Sharpe ratio and drawdown values reasonable
- ✅ Analysis date format correct

## 🗄️ Database Tables

### **trading.alerts**
Stores signal alerts for the web application:

```sql
CREATE TABLE trading.alerts (
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
);
```

### **trading.vectorbt_analysis**
Stores detailed VectorBTPro analysis results:

```sql
CREATE TABLE trading.vectorbt_analysis (
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
);
```

## 🔧 Configuration

### **config.json Options**

```json
{
    "binance_api_key": "your_binance_api_key_here",
    "binance_api_secret": "your_binance_api_secret_here",
    "database_host": "localhost",
    "database_port": 5432,
    "database_name": "autonama",
    "database_user": "postgres",
    "database_password": "postgres",
    "engine_results_dir": "../autonama.engine/results",
    "cleanup_days": 30,
    "validation": {
        "strict_mode": true,
        "check_duplicates": true,
        "validate_prices": true,
        "max_file_age_hours": 24
    },
    "vectorbt": {
        "enabled": true,
        "results_pattern": "vectorbt_analysis_results_*.csv",
        "json_pattern": "vectorbt_analysis_results_*.json"
    },
    "logging": {
        "level": "INFO",
        "file": "ingestion.log",
        "max_size_mb": 10,
        "backup_count": 5
    }
}
```

## 🚨 Important Notes

### **Conda Environment**
- **Must run in VectorBTPro conda environment**: `conda activate autonama_vectorbt`
- **VectorBTPro License**: Requires active VectorBTPro license
- **Shared Dependencies**: Uses same environment as engine for consistency

### **Local Processing**
- All intensive computation runs locally using VectorBTPro
- No cloud costs for analysis processing
- Results are stored in cloud database for display

### **API Limits**
- Binance API has rate limits
- Use caching to minimize API calls
- Process assets in batches if needed

### **Data Retention**
- Historical data cached locally for 24 hours
- Database cleanup removes old data after 30 days
- Local SQLite database for historical data storage

## 🔄 Integration Workflow

### **Complete Workflow**
1. **Engine Analysis**: Run VectorBTPro engine locally
2. **File Generation**: Engine creates CSV/JSON output files
3. **Ingestion**: Run ingestion system to validate and process
4. **Database Update**: Results stored in PostgreSQL
5. **Web Display**: Dashboard shows updated alerts and analytics

### **Automation Script**
```bash
#!/bin/bash
# daily_analysis_and_ingestion.sh

# Activate conda environment
conda activate autonama_vectorbt

# Run VectorBTPro analysis
cd autonama.engine
python run_vectorbt_analysis.py --config config.json --top-100 --optimize

# Ingest results
cd ../autonama.ingestion
python run_ingestion.py --engine vectorbt --config config.json

echo "Daily VectorBTPro analysis and ingestion complete!"
```

## 📈 Usage Examples

### **Basic Ingestion**
```bash
# Activate conda environment
conda activate autonama_vectorbt

# Ingest latest VectorBTPro results
python run_ingestion.py --engine vectorbt
```

### **Custom Configuration**
```bash
# Use custom config and results directory
python run_ingestion.py \
    --engine vectorbt \
    --config custom_config.json \
    --engine-results-dir /custom/path/to/results
```

### **Validation Only**
```bash
# Validate files without database changes
python run_ingestion.py --engine vectorbt --validate-only
```

### **Cleanup Old Data**
```bash
# Keep only 7 days of data
python run_ingestion.py --engine vectorbt --cleanup-days 7
```

## 🔍 Monitoring & Logs

### **Log Files**
- `ingestion.log`: Main ingestion logs
- `vectorbt_ingestion.log`: VectorBTPro-specific logs

### **Log Levels**
- `INFO`: Normal operation messages
- `WARNING`: Validation warnings
- `ERROR`: Errors that prevent ingestion
- `DEBUG`: Detailed debugging information

### **Success Indicators**
- ✅ "Ingestion completed successfully" message
- ✅ Database records inserted/updated
- ✅ No validation errors in logs
- ✅ Web dashboard showing updated data

## 🚨 Error Handling

### **Common Issues**

#### **Conda Environment**
```
❌ VectorBTPro not found. Please activate the correct conda environment.
   Run: conda activate autonama_vectorbt
```
**Solution**: Activate the VectorBTPro conda environment before running ingestion.

#### **File Not Found**
```
❌ Error: Engine results directory does not exist
```
**Solution**: Ensure the engine has generated results before running ingestion.

#### **Validation Errors**
```
❌ Ingestion failed: Validation failed
🔍 VALIDATION ERRORS:
  - Row 5: Invalid symbol format: BTC
  - Row 12: Missing current_price
```
**Solution**: Check engine output files for data quality issues.

#### **Database Connection**
```
❌ Database connection failed
```
**Solution**: Verify database is running and credentials are correct.

#### **Permission Errors**
```
❌ Error: Permission denied
```
**Solution**: Check file permissions and database user privileges.

## 🔄 Integration with Main System

### **Data Flow**
```
Local Conda Environment → VectorBTPro Engine → CSV/JSON Results → Ingestion System → PostgreSQL → Web Application
```

### **Schedule Recommendations**
- **Daily Analysis**: Run analysis once per day
- **Weekly Optimization**: Re-optimize parameters weekly
- **Monthly Cleanup**: Database cleanup monthly

### **Automation Script**
```bash
#!/bin/bash
# daily_analysis_and_ingestion.sh

# Activate conda environment
conda activate autonama_vectorbt

# Run VectorBTPro analysis
cd autonama.engine
python run_vectorbt_analysis.py --config config.json --top-100 --optimize

# Ingest results
cd ../autonama.ingestion
python run_ingestion.py --engine vectorbt --config config.json

echo "Daily VectorBTPro analysis and ingestion complete!"
```

## 🛠️ Advanced Usage

### **Custom Validation**
```python
from vectorbt_ingestion import VectorBTIngestionValidator

# Create custom validator
validator = VectorBTIngestionValidator()

# Validate specific file
is_valid, errors = validator.validate_csv_file('path/to/file.csv')
if not is_valid:
    print(f"Validation errors: {errors}")
```

### **Custom Processor**
```python
from vectorbt_ingestion import VectorBTIngestionProcessor

# Create processor with custom config
processor = VectorBTIngestionProcessor(db_config)

# Process results
results = processor.process_engine_results('/path/to/results')
```

## 🎯 Best Practices

### **Conda Environment Management**
- ✅ Always activate conda environment before running
- ✅ Verify VectorBTPro is available
- ✅ Use same environment for engine and ingestion
- ✅ Keep environment dependencies updated

### **File Management**
- ✅ Keep engine results organized by date
- ✅ Archive old results files
- ✅ Monitor disk space usage
- ✅ Use consistent file naming

### **Database Management**
- ✅ Regular cleanup of old data
- ✅ Monitor database size
- ✅ Backup important data
- ✅ Use appropriate indexes

### **Validation**
- ✅ Always validate before ingestion
- ✅ Check file age and freshness
- ✅ Verify data relationships
- ✅ Monitor validation error rates

### **Monitoring**
- ✅ Check logs regularly
- ✅ Monitor ingestion success rates
- ✅ Track database performance
- ✅ Verify web dashboard updates

## 🚨 Troubleshooting

### **Conda Environment Issues**
1. Verify conda environment is activated
2. Check VectorBTPro installation
3. Ensure all dependencies are installed
4. Verify license is active

### **Validation Issues**
1. Check engine output file format
2. Verify all required fields are present
3. Ensure data types are correct
4. Check for duplicate entries

### **Database Issues**
1. Verify database connection
2. Check user permissions
3. Ensure tables exist
4. Monitor disk space

### **Performance Issues**
1. Optimize database queries
2. Use appropriate indexes
3. Clean up old data regularly
4. Monitor system resources

## 📞 Support

For issues with the ingestion system:
1. Check the log files for detailed error messages
2. Verify engine output files are valid
3. Ensure database connection is working
4. Validate configuration settings
5. Check file permissions and paths
6. Verify conda environment is activated

---

**The Autonama Ingestion System ensures clean, validated data flows from local VectorBTPro analysis engines to the main web application, providing a reliable bridge between local processing and cloud-based display.** 
 