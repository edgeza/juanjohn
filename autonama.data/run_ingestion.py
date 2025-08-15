#!/usr/bin/env python3
"""
Simple script to run optimization data ingestion
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks.optimization_ingestion import OptimizationDataIngestion

def main():
    """Run the ingestion"""
    try:
        print("Starting optimization data ingestion...")
        
        # Initialize ingestion system
        ingestion = OptimizationDataIngestion()
        
        # Run ingestion
        results = ingestion.ingest_latest_data()
        
        print("Ingestion completed successfully!")
        print(f"Results: {results}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 