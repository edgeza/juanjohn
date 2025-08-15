#!/usr/bin/env python3
"""
Complete Optimization and Data Export Script

This script runs optimization on all 100 assets and exports the data in formats
that can be ingested by the Docker system for alerts, analytics, and plots.

Usage:
    python run_complete_optimization.py

The script will:
1. Run optimization on all 100 top assets
2. Export results in CSV and JSON formats
3. Generate summary statistics
4. Create files ready for Docker ingestion
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_engine import CryptoEngine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("complete_optimization.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CompleteOptimizationRunner:
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the complete optimization runner
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.engine = None
        self.base_results_dir = "export_results"
        
        # Create base results directory if it doesn't exist
        os.makedirs(self.base_results_dir, exist_ok=True)
        
        # Create single comprehensive results folder
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = os.path.join(self.base_results_dir, f"optimization_run_{self.timestamp}")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Create subdirectories for different data types
        self.alerts_dir = os.path.join(self.results_dir, "alerts")
        self.analytics_dir = os.path.join(self.results_dir, "analytics")
        self.plots_dir = os.path.join(self.results_dir, "plots")
        self.summary_dir = os.path.join(self.results_dir, "summary")
        self.raw_data_dir = os.path.join(self.results_dir, "raw_data")
        
        os.makedirs(self.alerts_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)
        os.makedirs(self.raw_data_dir, exist_ok=True)
        
        logger.info(f"Created comprehensive results directory: {self.results_dir}")
        logger.info(f"  - Alerts: {self.alerts_dir}")
        logger.info(f"  - Analytics: {self.analytics_dir}")
        logger.info(f"  - Plots: {self.plots_dir}")
        logger.info(f"  - Summary: {self.summary_dir}")
        logger.info(f"  - Raw Data: {self.raw_data_dir}")
        
    def initialize_engine(self):
        """Initialize the crypto engine"""
        try:
            logger.info("Initializing Crypto Engine...")
            self.engine = CryptoEngine(self.config_file)
            logger.info("Crypto Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Crypto Engine: {e}")
            raise
    
    def run_optimization_all_assets(self, interval: str = '1d', days: int = 720) -> Dict:
        """
        Run optimization on all 100 assets
        
        Args:
            interval: Time interval for analysis
            days: Number of days of historical data
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        try:
            logger.info("="*80)
            logger.info("STARTING COMPLETE OPTIMIZATION FOR ALL 100 ASSETS")
            logger.info("="*80)
            logger.info(f"Interval: {interval}")
            logger.info(f"Days: {days}")
            logger.info(f"Optimization: ENABLED for all assets")
            
            # Get top 100 assets
            symbols = self.engine.get_top_100_assets()
            logger.info(f"Found {len(symbols)} assets for analysis")
            
            # Run complete analysis with optimization enabled
            start_time = datetime.now()
            
            analysis_result = self.engine.run_complete_analysis(
                symbols=symbols,
                interval=interval,
                days=days,
                optimize_all_assets=True,  # This ensures optimization runs for ALL assets
                output_format='both'  # Export both CSV and JSON
            )
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("="*80)
            logger.info("OPTIMIZATION COMPLETE")
            logger.info("="*80)
            logger.info(f"Total duration: {duration}")
            logger.info(f"Assets analyzed: {len(analysis_result['results'])}")
            logger.info(f"CSV file: {analysis_result['csv_filepath']}")
            logger.info(f"JSON file: {analysis_result['json_filepath']}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error running optimization: {e}")
            raise
    
    def create_docker_ingestion_files(self, analysis_result: Dict) -> Dict:
        """
        Create files specifically formatted for Docker ingestion
        
        Args:
            analysis_result: Results from the optimization analysis
            
        Returns:
            Dictionary with file paths for Docker ingestion
        """
        try:
            logger.info("Creating Docker ingestion files...")
            
            # 1. Create alerts file (for real-time alerts)
            alerts_file = self.create_alerts_file(analysis_result['results'], self.timestamp)
            
            # 2. Create analytics file (for detailed analytics)
            analytics_file = self.create_analytics_file(analysis_result, self.timestamp)
            
            # 3. Create summary file (for dashboard overview)
            summary_file = self.create_summary_file(analysis_result, self.timestamp)
            
            # 4. Create plots data file (for chart generation)
            plots_file = self.create_plots_data_file(analysis_result['results'], self.timestamp)
            
            ingestion_files = {
                'alerts_file': alerts_file,
                'analytics_file': analytics_file,
                'summary_file': summary_file,
                'plots_file': plots_file,
                'original_csv': analysis_result['csv_filepath'],
                'original_json': analysis_result['json_filepath'],
                'timestamp': self.timestamp
            }
            
            logger.info("Docker ingestion files created successfully:")
            for key, filepath in ingestion_files.items():
                if key != 'timestamp':
                    logger.info(f"  {key}: {filepath}")
            
            return ingestion_files
            
        except Exception as e:
            logger.error(f"Error creating Docker ingestion files: {e}")
            raise
    
    def create_alerts_file(self, results: List[Dict], timestamp: str) -> str:
        """Create alerts file for real-time alerting system"""
        try:
            alerts_data = []
            
            for result in results:
                # Include ALL assets with their signals (BUY, SELL, HOLD)
                alert = {
                    'symbol': result['symbol'],
                    'signal': result.get('signal', 'HOLD'),
                    'current_price': result.get('current_price', 0),
                    'potential_return': result.get('potential_return', 0),
                    'signal_strength': result.get('signal_strength', 0),
                    'risk_level': result.get('risk_level', 'MEDIUM'),
                    'timestamp': datetime.now().isoformat(),
                    'interval': result.get('interval', '1d'),
                    'optimized_degree': result.get('optimized_degree'),
                    'optimized_kstd': result.get('optimized_kstd'),
                    'optimized_lookback': result.get('optimized_lookback'),
                    'total_return': result.get('total_return', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'data_points': result.get('data_points', 0),
                    'total_available': result.get('total_available', 0)
                }
                alerts_data.append(alert)
            
            filename = f"alerts_{timestamp}.json"
            filepath = os.path.join(self.alerts_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            logger.info(f"Created alerts file with {len(alerts_data)} alerts: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating alerts file: {e}")
            raise
    
    def create_analytics_file(self, analysis_result: Dict, timestamp: str) -> str:
        """Create detailed analytics file for comprehensive analysis"""
        try:
            # Ensure all results have consistent fields
            processed_results = []
            for result in analysis_result['results']:
                processed_result = {
                    'symbol': result['symbol'],
                    'signal': result.get('signal', 'HOLD'),
                    'current_price': result.get('current_price', 0),
                    'potential_return': result.get('potential_return', 0),
                    'total_return': result.get('total_return', 0),
                    'signal_strength': result.get('signal_strength', 0),
                    'risk_level': result.get('risk_level', 'MEDIUM'),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'optimized_degree': result.get('optimized_degree'),
                    'optimized_kstd': result.get('optimized_kstd'),
                    'optimized_lookback': result.get('optimized_lookback'),
                    'degree': result.get('degree'),
                    'kstd': result.get('kstd'),
                    'lookback': result.get('lookback'),
                    'interval': result.get('interval', '1d'),
                    'data_points': result.get('data_points', 0),
                    'total_available': result.get('total_available', 0),
                    'analysis_date': result.get('analysis_date', datetime.now().isoformat())
                }
                processed_results.append(processed_result)
            
            analytics_data = {
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'total_assets': len(processed_results),
                    'optimization_enabled': True,
                    'interval': processed_results[0].get('interval', '1d') if processed_results else '1d'
                },
                'summary': analysis_result['summary'],
                'individual_analyses': processed_results,
                'optimization_results': []
            }
            
            # Extract optimization results
            for result in processed_results:
                if result.get('optimized_degree') is not None:
                    opt_result = {
                        'symbol': result['symbol'],
                        'optimized_degree': result.get('optimized_degree'),
                        'optimized_kstd': result.get('optimized_kstd'),
                        'optimized_lookback': result.get('optimized_lookback'),
                        'original_degree': result.get('degree'),
                        'original_kstd': result.get('kstd'),
                        'optimization_improvement': result.get('optimization_improvement', 0)
                    }
                    analytics_data['optimization_results'].append(opt_result)
            
            filename = f"analytics_{timestamp}.json"
            filepath = os.path.join(self.analytics_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(analytics_data, f, indent=2, default=str)
            
            logger.info(f"Created analytics file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating analytics file: {e}")
            raise
    
    def create_summary_file(self, analysis_result: Dict, timestamp: str) -> str:
        """Create summary file for dashboard overview"""
        try:
            summary_data = {
                'timestamp': datetime.now().isoformat(),
                'total_assets_analyzed': len(analysis_result['results']),
                'optimization_enabled': True,
                'analysis_summary': analysis_result['summary'],
                'top_performers': {
                    'buy_signals': sorted(
                        [r for r in analysis_result['results'] if r.get('signal') == 'BUY'],
                        key=lambda x: x.get('potential_return', 0) or 0,
                        reverse=True
                    )[:10],
                    'sell_signals': sorted(
                        [r for r in analysis_result['results'] if r.get('signal') == 'SELL'],
                        key=lambda x: x.get('potential_return', 0) or 0,
                        reverse=True
                    )[:10]
                },
                'optimization_stats': {
                    'assets_optimized': len([r for r in analysis_result['results'] if r.get('optimized_degree') is not None]),
                    'avg_optimization_improvement': sum([r.get('optimization_improvement', 0) for r in analysis_result['results']]) / len(analysis_result['results'])
                }
            }
            
            filename = f"summary_{timestamp}.json"
            filepath = os.path.join(self.summary_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            
            logger.info(f"Created summary file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating summary file: {e}")
            raise
    
    def create_plots_data_file(self, results: List[Dict], timestamp: str) -> str:
        """Create data file for generating charts and plots"""
        try:
            plots_data = {
                'timestamp': datetime.now().isoformat(),
                'potential_returns': [
                    {
                        'symbol': r['symbol'],
                        'signal': r.get('signal', 'HOLD'),
                        'current_price': r.get('current_price', 0),
                        'potential_return': r.get('potential_return', 0),
                        'total_return': r.get('total_return', 0),
                        'sharpe_ratio': r.get('sharpe_ratio', 0),
                        'max_drawdown': r.get('max_drawdown', 0),
                        'optimized_degree': r.get('optimized_degree'),
                        'optimized_kstd': r.get('optimized_kstd'),
                        'optimized_lookback': r.get('optimized_lookback'),
                        'interval': r.get('interval', '1d'),
                        'data_points': r.get('data_points', 0),
                        'total_available': r.get('total_available', 0)
                    }
                    for r in results
                ],
                'signal_distribution': {
                    'labels': ['BUY', 'SELL', 'HOLD'],
                    'values': [
                        len([r for r in results if r.get('signal') == 'BUY']),
                        len([r for r in results if r.get('signal') == 'SELL']),
                        len([r for r in results if r.get('signal') == 'HOLD'])
                    ]
                },
                'optimization_comparison': [
                    {
                        'symbol': r['symbol'],
                        'original_degree': r.get('degree'),
                        'optimized_degree': r.get('optimized_degree'),
                        'original_kstd': r.get('kstd'),
                        'optimized_kstd': r.get('optimized_kstd'),
                        'improvement': r.get('optimization_improvement', 0)
                    }
                    for r in results if r.get('optimized_degree') is not None
                ]
            }
            
            filename = f"plots_data_{timestamp}.json"
            filepath = os.path.join(self.plots_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(plots_data, f, indent=2, default=str)
            
            logger.info(f"Created plots data file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating plots data file: {e}")
            raise
    
    def create_ingestion_manifest(self, ingestion_files: Dict) -> str:
        """Create a manifest file listing all files for ingestion"""
        try:
            manifest = {
                'ingestion_timestamp': datetime.now().isoformat(),
                'files': ingestion_files,
                'instructions': {
                    'alerts_file': 'Use for real-time alerting system',
                    'analytics_file': 'Use for detailed analytics and reporting',
                    'summary_file': 'Use for dashboard overview and summaries',
                    'plots_file': 'Use for generating charts and visualizations',
                    'original_csv': 'Original CSV export from VectorBT analysis',
                    'original_json': 'Original JSON export from VectorBT analysis'
                },
                'total_assets_analyzed': len(self.engine.get_top_100_assets()),
                'optimization_enabled': True
            }
            
            manifest_file = os.path.join(self.results_dir, f"manifest_{self.timestamp}.json")
            
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Created ingestion manifest: {manifest_file}")
            return manifest_file
            
        except Exception as e:
            logger.error(f"Error creating ingestion manifest: {e}")
            raise
    
    def run_complete_pipeline(self, interval: str = '1d', days: int = 720) -> Dict:
        """
        Run the complete optimization and export pipeline
        
        Args:
            interval: Time interval for analysis
            days: Number of days of historical data
            
        Returns:
            Dictionary with all results and file paths
        """
        try:
            logger.info("Starting complete optimization pipeline...")
            
            # Step 1: Initialize engine
            self.initialize_engine()
            
            # Step 2: Check data status and update efficiently
            logger.info("="*80)
            logger.info("STEP 1: CHECKING DATA STATUS")
            logger.info("="*80)
            
            # Get current data status
            data_status = self.engine.get_data_status(interval=interval)
            logger.info(f"Data Status Summary:")
            logger.info(f"  Total symbols: {data_status.get('total_symbols', 0)}")
            logger.info(f"  Symbols with data: {data_status.get('symbols_with_data', 0)}")
            logger.info(f"  Symbols up to date: {data_status.get('symbols_up_to_date', 0)}")
            logger.info(f"  Symbols needing update: {data_status.get('symbols_needing_update', 0)}")
            logger.info(f"  Symbols with no data: {data_status.get('symbols_no_data', 0)}")
            
            # Update data efficiently
            logger.info("="*80)
            logger.info("STEP 2: UPDATING DATA EFFICIENTLY")
            logger.info("="*80)
            update_success = self.engine.update_all_data(interval=interval, days=days)
            if update_success:
                logger.info("SUCCESS: Data update completed successfully")
            else:
                logger.warning("WARNING: Some data updates failed, but continuing with optimization")
            
            # Step 3: Run optimization on all assets
            logger.info("="*80)
            logger.info("STEP 3: RUNNING OPTIMIZATION ON ALL ASSETS")
            logger.info("="*80)
            analysis_result = self.run_optimization_all_assets(interval, days)
            
            # Step 4: Save raw optimization results
            logger.info("="*80)
            logger.info("STEP 4: SAVING RAW OPTIMIZATION RESULTS")
            logger.info("="*80)
            
            # Copy raw results to raw_data directory
            if analysis_result.get('csv_filepath'):
                import shutil
                csv_filename = f"optimization_results_{self.timestamp}.csv"
                csv_dest = os.path.join(self.raw_data_dir, csv_filename)
                shutil.copy2(analysis_result['csv_filepath'], csv_dest)
                logger.info(f"Saved raw CSV results: {csv_dest}")
            
            if analysis_result.get('json_filepath'):
                import shutil
                json_filename = f"optimization_results_{self.timestamp}.json"
                json_dest = os.path.join(self.raw_data_dir, json_filename)
                shutil.copy2(analysis_result['json_filepath'], json_dest)
                logger.info(f"Saved raw JSON results: {json_dest}")
            
            # Step 5: Create Docker ingestion files
            logger.info("="*80)
            logger.info("STEP 5: CREATING DOCKER INGESTION FILES")
            logger.info("="*80)
            ingestion_files = self.create_docker_ingestion_files(analysis_result)
            
            # Step 6: Create ingestion manifest
            logger.info("="*80)
            logger.info("STEP 6: CREATING INGESTION MANIFEST")
            logger.info("="*80)
            manifest_file = self.create_ingestion_manifest(ingestion_files)
            
            # Step 7: Create final summary
            logger.info("="*80)
            logger.info("STEP 7: CREATING FINAL SUMMARY")
            logger.info("="*80)
            final_result = {
                'status': 'success',
                'timestamp': self.timestamp,
                'analysis_result': analysis_result,
                'ingestion_files': ingestion_files,
                'manifest_file': manifest_file,
                'instructions': {
                    'next_steps': [
                        "1. Copy all files from 'export_results' directory to your Docker ingestion system",
                        "2. Use the ingestion_manifest.json to understand what each file contains",
                        "3. Process alerts_file.json for real-time alerts",
                        "4. Use analytics_file.json for detailed analytics",
                        "5. Use summary_file.json for dashboard overview",
                        "6. Use plots_data_file.json for generating charts"
                    ]
                }
            }
            
            # Create comprehensive README
            readme_content = f"""# Optimization Run {self.timestamp}

## Overview
This directory contains the complete results from the optimization run performed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

## Directory Structure
- `alerts/` - Real-time trading alerts and signals
- `analytics/` - Detailed analytics and optimization results
- `plots/` - Chart data and visualization files
- `summary/` - Summary reports and overview data
- `raw_data/` - Raw optimization results (CSV/JSON)
- `manifest_{self.timestamp}.json` - Complete file manifest

## Analysis Details
- **Total Assets Analyzed**: {analysis_result['summary']['total_assets']}
- **BUY Signals**: {analysis_result['summary']['buy_signals']}
- **SELL Signals**: {analysis_result['summary']['sell_signals']}
- **HOLD Signals**: {analysis_result['summary']['hold_signals']}
- **Average Potential Return**: {analysis_result['summary']['avg_potential_return']:.2f}%
- **Optimization Enabled**: Yes
- **Data Interval**: 1d
- **Historical Days**: {days}

## Files Created
{chr(10).join([f"- {os.path.basename(file)}" for file in ingestion_files.values() if file != self.timestamp])}
- manifest_{self.timestamp}.json

## Usage
1. Use `alerts/` files for real-time trading signals
2. Use `analytics/` files for detailed analysis
3. Use `plots/` files for chart generation
4. Use `summary/` files for dashboard overview
5. Use `raw_data/` files for custom analysis

## Docker Integration
All files are formatted for immediate Docker ingestion.
"""
            
            readme_file = os.path.join(self.results_dir, "README.md")
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            logger.info("="*80)
            logger.info("COMPLETE PIPELINE FINISHED SUCCESSFULLY")
            logger.info("="*80)
            logger.info(f"All files exported to: {self.results_dir}")
            logger.info(f"Manifest file: {manifest_file}")
            logger.info(f"README created: {readme_file}")
            logger.info("Ready for Docker ingestion!")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

def main():
    """Main function to run the complete optimization pipeline"""
    try:
        # Initialize the runner
        runner = CompleteOptimizationRunner()
        
        # Run the complete pipeline
        result = runner.run_complete_pipeline(
            interval='1d',  # Daily analysis
            days=720        # 2 years of historical data
        )
        
        # Print final summary
        print("\n" + "="*80)
        print("OPTIMIZATION COMPLETE - FILES READY FOR DOCKER INGESTION")
        print("="*80)
        print(f"Results directory: {runner.results_dir}")
        print(f"Total assets analyzed: {result['analysis_result']['summary']['total_assets']}")
        print(f"BUY signals: {result['analysis_result']['summary']['buy_signals']}")
        print(f"SELL signals: {result['analysis_result']['summary']['sell_signals']}")
        print(f"HOLD signals: {result['analysis_result']['summary']['hold_signals']}")
        print(f"Average potential return: {result['analysis_result']['summary']['avg_potential_return']:.2f}%")
        print("\nFiles created:")
        for key, filepath in result['ingestion_files'].items():
            if key != 'timestamp':
                print(f"  {key}: {filepath}")
        print(f"\nManifest: {result['manifest_file']}")
        print("\nNext steps:")
        for step in result['instructions']['next_steps']:
            print(f"  {step}")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 