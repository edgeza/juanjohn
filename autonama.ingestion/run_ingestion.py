
#!/usr/bin/env python3
"""
Autonama Ingestion Runner

Main script to run the ingestion system for different engine outputs.
Acts as a clean bridge between local analysis engines and the main Docker system.

This script is designed to run in the same conda environment as VectorBTPro.

Usage:
    python run_ingestion.py --engine vectorbt --config config.json
    python run_ingestion.py --engine enhanced --config config.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from vectorbt_ingestion import VectorBTIngestionProcessor

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def check_conda_environment():
    """Check if we're in the correct conda environment"""
    try:
        import vectorbtpro
        print(f"✅ VectorBTPro detected: {vectorbtpro.__version__}")
        return True
    except ImportError:
        print("❌ VectorBTPro not found. Please activate the correct conda environment.")
        print("   Run: conda activate autonama_vectorbt")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run Autonama Ingestion System')
    parser.add_argument('--engine', choices=['vectorbt', 'enhanced'], 
                       default='vectorbt', help='Engine type to ingest')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--engine-results-dir', help='Custom engine results directory')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days to keep data')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate files, do not ingest')
    parser.add_argument('--skip-conda-check', action='store_true',
                       help='Skip conda environment check')
    
    args = parser.parse_args()
    
    # Check conda environment
    if not args.skip_conda_check:
        if not check_conda_environment():
            sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Database configuration
    db_config = {
        'host': config.get('database_host', 'localhost'),
        'port': config.get('database_port', 5432),
        'database': config.get('database_name', 'autonama'),
        'user': config.get('database_user', 'postgres'),
        'password': config.get('database_password', 'postgres')
    }
    
    # Determine engine results directory
    if args.engine_results_dir:
        engine_results_dir = args.engine_results_dir
    else:
        if args.engine == 'vectorbt':
            engine_results_dir = '../autonama.engine/results'
        else:  # enhanced
            engine_results_dir = '../autonama.engine/results'
    
    print(f"🚀 Starting Autonama Ingestion System")
    print(f"📊 Engine type: {args.engine}")
    print(f"📁 Engine results directory: {engine_results_dir}")
    print(f"🗄️ Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    print(f"🔍 Validate only: {args.validate_only}")
    print(f"🐍 Conda environment: {os.environ.get('CONDA_DEFAULT_ENV', 'Not detected')}")
    
    # Check if engine results directory exists
    if not os.path.exists(engine_results_dir):
        print(f"❌ Error: Engine results directory does not exist: {engine_results_dir}")
        print(f"   Please ensure the {args.engine} engine has generated results.")
        print(f"   Expected path: {os.path.abspath(engine_results_dir)}")
        sys.exit(1)
    
    # Process based on engine type
    if args.engine == 'vectorbt':
        processor = VectorBTIngestionProcessor(db_config)
        results = processor.process_engine_results(engine_results_dir)
    else:
        print(f"❌ Engine type '{args.engine}' not yet implemented")
        sys.exit(1)
    
    # Display results
    print(f"\n{'='*60}")
    print(f"INGESTION RESULTS")
    print(f"{'='*60}")
    
    if 'error' in results:
        print(f"❌ Ingestion failed: {results['error']}")
        
        if 'validation_errors' in results:
            print(f"\n🔍 VALIDATION ERRORS:")
            for error in results['validation_errors']:
                print(f"  - {error}")
        
        if 'files_checked' in results:
            print(f"\n📁 Files checked: {', '.join(results['files_checked'])}")
        
        sys.exit(1)
    else:
        print(f"✅ Ingestion completed successfully!")
        print(f"📁 Files processed: {', '.join(results['files_processed'])}")
        print(f"📊 Total results: {results['total_results']}")
        print(f"📊 Alerts ingested: {results['alerts_ingested']}")
        print(f"📈 Analysis ingested: {results['analysis_ingested']}")
        print(f"⏰ Timestamp: {results['timestamp']}")
        
        # Show summary statistics
        if results['total_results'] > 0:
            print(f"\n📈 SUMMARY:")
            print(f"  - Successfully processed {results['total_results']} analysis results")
            print(f"  - Database updated with latest VectorBTPro analysis")
            print(f"  - Web application will now show updated alerts and analytics")
    
    print(f"\n🎯 Next steps:")
    print(f"  1. Check the web dashboard at http://localhost:3001")
    print(f"  2. Verify alerts are showing in the alerts page")
    print(f"  3. Monitor database for new analysis data")
    print(f"  4. Run ingestion again after next engine analysis")

if __name__ == "__main__":
    main() 
"""
Autonama Ingestion Runner

Main script to run the ingestion system for different engine outputs.
Acts as a clean bridge between local analysis engines and the main Docker system.

This script is designed to run in the same conda environment as VectorBTPro.

Usage:
    python run_ingestion.py --engine vectorbt --config config.json
    python run_ingestion.py --engine enhanced --config config.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from vectorbt_ingestion import VectorBTIngestionProcessor

def load_config(config_file: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def check_conda_environment():
    """Check if we're in the correct conda environment"""
    try:
        import vectorbtpro
        print(f"✅ VectorBTPro detected: {vectorbtpro.__version__}")
        return True
    except ImportError:
        print("❌ VectorBTPro not found. Please activate the correct conda environment.")
        print("   Run: conda activate autonama_vectorbt")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run Autonama Ingestion System')
    parser.add_argument('--engine', choices=['vectorbt', 'enhanced'], 
                       default='vectorbt', help='Engine type to ingest')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--engine-results-dir', help='Custom engine results directory')
    parser.add_argument('--cleanup-days', type=int, default=30, help='Days to keep data')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate files, do not ingest')
    parser.add_argument('--skip-conda-check', action='store_true',
                       help='Skip conda environment check')
    
    args = parser.parse_args()
    
    # Check conda environment
    if not args.skip_conda_check:
        if not check_conda_environment():
            sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Database configuration
    db_config = {
        'host': config.get('database_host', 'localhost'),
        'port': config.get('database_port', 5432),
        'database': config.get('database_name', 'autonama'),
        'user': config.get('database_user', 'postgres'),
        'password': config.get('database_password', 'postgres')
    }
    
    # Determine engine results directory
    if args.engine_results_dir:
        engine_results_dir = args.engine_results_dir
    else:
        if args.engine == 'vectorbt':
            engine_results_dir = '../autonama.engine/results'
        else:  # enhanced
            engine_results_dir = '../autonama.engine/results'
    
    print(f"🚀 Starting Autonama Ingestion System")
    print(f"📊 Engine type: {args.engine}")
    print(f"📁 Engine results directory: {engine_results_dir}")
    print(f"🗄️ Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    print(f"🔍 Validate only: {args.validate_only}")
    print(f"🐍 Conda environment: {os.environ.get('CONDA_DEFAULT_ENV', 'Not detected')}")
    
    # Check if engine results directory exists
    if not os.path.exists(engine_results_dir):
        print(f"❌ Error: Engine results directory does not exist: {engine_results_dir}")
        print(f"   Please ensure the {args.engine} engine has generated results.")
        print(f"   Expected path: {os.path.abspath(engine_results_dir)}")
        sys.exit(1)
    
    # Process based on engine type
    if args.engine == 'vectorbt':
        processor = VectorBTIngestionProcessor(db_config)
        results = processor.process_engine_results(engine_results_dir)
    else:
        print(f"❌ Engine type '{args.engine}' not yet implemented")
        sys.exit(1)
    
    # Display results
    print(f"\n{'='*60}")
    print(f"INGESTION RESULTS")
    print(f"{'='*60}")
    
    if 'error' in results:
        print(f"❌ Ingestion failed: {results['error']}")
        
        if 'validation_errors' in results:
            print(f"\n🔍 VALIDATION ERRORS:")
            for error in results['validation_errors']:
                print(f"  - {error}")
        
        if 'files_checked' in results:
            print(f"\n📁 Files checked: {', '.join(results['files_checked'])}")
        
        sys.exit(1)
    else:
        print(f"✅ Ingestion completed successfully!")
        print(f"📁 Files processed: {', '.join(results['files_processed'])}")
        print(f"📊 Total results: {results['total_results']}")
        print(f"📊 Alerts ingested: {results['alerts_ingested']}")
        print(f"📈 Analysis ingested: {results['analysis_ingested']}")
        print(f"⏰ Timestamp: {results['timestamp']}")
        
        # Show summary statistics
        if results['total_results'] > 0:
            print(f"\n📈 SUMMARY:")
            print(f"  - Successfully processed {results['total_results']} analysis results")
            print(f"  - Database updated with latest VectorBTPro analysis")
            print(f"  - Web application will now show updated alerts and analytics")
    
    print(f"\n🎯 Next steps:")
    print(f"  1. Check the web dashboard at http://localhost:3001")
    print(f"  2. Verify alerts are showing in the alerts page")
    print(f"  3. Monitor database for new analysis data")
    print(f"  4. Run ingestion again after next engine analysis")

if __name__ == "__main__":
    main() 
 