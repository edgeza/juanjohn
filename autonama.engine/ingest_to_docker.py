#!/usr/bin/env python3
"""
Autonama Engine to Docker Ingestion Script

This script takes the latest optimization export data and ingests it into the Docker system
so the web application can access it for generating pages and analytics.

Usage:
    python ingest_to_docker.py
"""

import os
import json
import shutil
import glob
import math
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clean_nan_values(obj):
    """Recursively clean NaN values from data structures"""
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj

class DockerIngestionManager:
    def __init__(self):
        self.engine_dir = Path(__file__).parent
        self.web_dir = self.engine_dir.parent / "autonama.web"
        self.export_dir = self.engine_dir / "export_results"
        self.docker_data_dir = self.web_dir / "public" / "data"
        
        # Ensure Docker data directory exists
        self.docker_data_dir.mkdir(parents=True, exist_ok=True)
        
    def find_latest_optimization_run(self):
        """Find the latest optimization run folder"""
        try:
            if not self.export_dir.exists():
                logger.error(f"Export directory not found: {self.export_dir}")
                return None
                
            # Find all optimization run folders
            run_folders = list(self.export_dir.glob("optimization_run_*"))
            
            if not run_folders:
                logger.error("No optimization run folders found")
                return None
                
            # Sort by creation time and get the latest
            latest_folder = max(run_folders, key=lambda x: x.stat().st_mtime)
            logger.info(f"Found latest optimization run: {latest_folder.name}")
            
            return latest_folder
            
        except Exception as e:
            logger.error(f"Error finding latest optimization run: {e}")
            return None
    
    def load_export_data(self, run_folder):
        """Load all export data from the optimization run"""
        data = {
            'alerts': [],
            'analytics': {},
            'plots': {},
            'summary': {},
            'metadata': {
                'run_folder': run_folder.name,
                'ingestion_time': datetime.now().isoformat(),
                'source_path': str(run_folder)
            }
        }
        
        try:
            # Load alerts
            alerts_dir = run_folder / "alerts"
            if alerts_dir.exists():
                alert_files = list(alerts_dir.glob("alerts_*.json"))
                if alert_files:
                    latest_alerts = max(alert_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_alerts, 'r') as f:
                        data['alerts'] = json.load(f)
                    logger.info(f"Loaded {len(data['alerts'])} alerts from {latest_alerts.name}")
            
            # Load analytics
            analytics_dir = run_folder / "analytics"
            if analytics_dir.exists():
                analytics_files = list(analytics_dir.glob("analytics_*.json"))
                if analytics_files:
                    latest_analytics = max(analytics_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_analytics, 'r') as f:
                        data['analytics'] = json.load(f)
                    logger.info(f"Loaded analytics from {latest_analytics.name}")
            
            # Load plots data
            plots_dir = run_folder / "plots"
            if plots_dir.exists():
                plots_files = list(plots_dir.glob("plots_data_*.json"))
                if plots_files:
                    latest_plots = max(plots_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_plots, 'r') as f:
                        data['plots'] = json.load(f)
                    logger.info(f"Loaded plots data from {latest_plots.name}")
            
            # Load summary
            summary_dir = run_folder / "summary"
            if summary_dir.exists():
                summary_files = list(summary_dir.glob("summary_*.json"))
                if summary_files:
                    latest_summary = max(summary_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_summary, 'r') as f:
                        data['summary'] = json.load(f)
                    logger.info(f"Loaded summary from {latest_summary.name}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading export data: {e}")
            return None
    
    def create_docker_api_data(self, data):
        """Create API-compatible data structure for Docker"""
        docker_data = {
            'alerts': [],
            'analytics': [],
            'summary': {},
            'assets': []
        }
        
        try:
            # Process alerts
            if data.get('alerts'):
                for i, alert in enumerate(data['alerts']):
                    alert_with_id = {
                        'id': i + 1,
                        **alert
                    }
                    docker_data['alerts'].append(alert_with_id)
            
            # Process analytics
            if data.get('analytics', {}).get('individual_analyses'):
                docker_data['analytics'] = data['analytics']['individual_analyses']
            
            # Process summary
            if data.get('summary'):
                docker_data['summary'] = data['summary']
            
            # Create assets list from analytics
            if docker_data['analytics']:
                for asset in docker_data['analytics']:
                    asset_info = {
                        'symbol': asset['symbol'],
                        'name': asset['symbol'],  # Use symbol as name for now
                        'category': 'crypto',
                        'price': asset.get('current_price', 0),
                        'change_24h': 0,  # Not available in analytics
                        'change_percent_24h': asset.get('potential_return', 0),
                        'volume_24h': 0,  # Not available in analytics
                        'market_cap': 0,  # Not available in analytics
                        'last_updated': asset.get('timestamp', datetime.now().isoformat())
                    }
                    docker_data['assets'].append(asset_info)
            
            # Clean NaN values
            docker_data = clean_nan_values(docker_data)
            
            return docker_data
            
        except Exception as e:
            logger.error(f"Error creating Docker API data: {e}")
            return None
    
    def save_to_docker(self, docker_data):
        """Save data to Docker accessible location"""
        try:
            # Save main data file
            main_data_file = self.docker_data_dir / "optimization_data.json"
            with open(main_data_file, 'w') as f:
                json.dump(docker_data, f, indent=2)
            logger.info(f"Saved main data to {main_data_file}")
            
            # Save individual files for API endpoints
            api_dir = self.docker_data_dir / "api"
            api_dir.mkdir(exist_ok=True)
            
            # Alerts endpoint
            alerts_file = api_dir / "alerts.json"
            with open(alerts_file, 'w') as f:
                json.dump(docker_data['alerts'], f, indent=2)
            logger.info(f"Saved alerts to {alerts_file}")
            
            # Analytics endpoint
            analytics_file = api_dir / "analytics.json"
            with open(analytics_file, 'w') as f:
                json.dump(docker_data['analytics'], f, indent=2)
            logger.info(f"Saved analytics to {analytics_file}")
            
            # Summary endpoint
            summary_file = api_dir / "summary.json"
            with open(summary_file, 'w') as f:
                json.dump(docker_data['summary'], f, indent=2)
            logger.info(f"Saved summary to {summary_file}")
            
            # Assets endpoint
            assets_file = api_dir / "assets.json"
            with open(assets_file, 'w') as f:
                json.dump(docker_data['assets'], f, indent=2)
            logger.info(f"Saved assets to {assets_file}")
            
            # Create individual asset files
            assets_dir = api_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            
            for asset in docker_data['analytics']:
                asset_file = assets_dir / f"{asset['symbol']}.json"
                with open(asset_file, 'w') as f:
                    json.dump(asset, f, indent=2)
            
            logger.info(f"Saved {len(docker_data['analytics'])} individual asset files")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to Docker: {e}")
            return False
    
    def create_ingestion_manifest(self, run_folder, docker_data):
        """Create a manifest file documenting the ingestion"""
        manifest = {
            'ingestion_time': datetime.now().isoformat(),
            'source_run': run_folder.name,
            'source_path': str(run_folder),
            'data_summary': {
                'total_alerts': len(docker_data['alerts']),
                'total_analytics': len(docker_data['analytics']),
                'total_assets': len(docker_data['assets']),
                'has_summary': bool(docker_data['summary'])
            },
            'docker_paths': {
                'main_data': str(self.docker_data_dir / "optimization_data.json"),
                'api_dir': str(self.docker_data_dir / "api"),
                'alerts': str(self.docker_data_dir / "api" / "alerts.json"),
                'analytics': str(self.docker_data_dir / "api" / "analytics.json"),
                'summary': str(self.docker_data_dir / "api" / "summary.json"),
                'assets': str(self.docker_data_dir / "api" / "assets.json")
            }
        }
        
        manifest_file = self.docker_data_dir / "ingestion_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Created ingestion manifest: {manifest_file}")
        return manifest
    
    def run_ingestion(self):
        """Main ingestion process"""
        logger.info("Starting Docker ingestion process...")
        
        # Find latest optimization run
        run_folder = self.find_latest_optimization_run()
        if not run_folder:
            logger.error("No optimization run found. Please run optimization first.")
            return False
        
        # Load export data
        data = self.load_export_data(run_folder)
        if not data:
            logger.error("Failed to load export data")
            return False
        
        # Create Docker-compatible data
        docker_data = self.create_docker_api_data(data)
        if not docker_data:
            logger.error("Failed to create Docker API data")
            return False
        
        # Save to Docker
        if not self.save_to_docker(docker_data):
            logger.error("Failed to save data to Docker")
            return False
        
        # Create manifest
        manifest = self.create_ingestion_manifest(run_folder, docker_data)
        
        logger.info("Docker ingestion completed successfully!")
        logger.info(f"Data summary: {manifest['data_summary']}")
        logger.info(f"Data available at: {self.docker_data_dir}")
        
        return True

def main():
    """Main entry point"""
    try:
        manager = DockerIngestionManager()
        success = manager.run_ingestion()
        
        if success:
            print("Docker ingestion completed successfully!")
            print("Data is now available for the Docker web application")
            print("You can now build and run the Docker container")
        else:
            print("Docker ingestion failed. Check the logs for details.")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 