#!/usr/bin/env python3
"""
Test script for the updated data ingestion Celery tasks.

This script allows you to test the new data ingestion functionality
without running the full Celery worker.

Usage:
    python test_data_ingestion.py [--category CATEGORY] [--force]
"""

import argparse
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_data_processor_import():
    """Test if we can import the DuckDBDataProcessor"""
    try:
        from tasks.data_ingestion import setup_data_processor
        DuckDBDataProcessor = setup_data_processor()
        print("✅ Successfully imported DuckDBDataProcessor")
        return True
    except Exception as e:
        print(f"❌ Failed to import DuckDBDataProcessor: {e}")
        return False

def test_category_update(category: str, force_update: bool = False):
    """Test updating a specific category"""
    try:
        from tasks.data_ingestion import setup_data_processor, update_category_data
        
        print(f"Testing {category} data update...")
        DuckDBDataProcessor = setup_data_processor()
        processor = DuckDBDataProcessor(read_only=False)
        
        # Test the update
        stats = update_category_data(processor, category, force_update)
        
        print(f"✅ {category.upper()} update completed:")
        print(f"   Success: {stats.get('success', 0)}")
        print(f"   Failed: {stats.get('failed', 0)}")
        print(f"   Skipped: {stats.get('skipped', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {category} update: {e}")
        return False

def test_full_update(force_update: bool = False):
    """Test the full update process"""
    try:
        from tasks.data_ingestion import setup_data_processor, update_category_data
        
        print("Testing full data update process...")
        DuckDBDataProcessor = setup_data_processor()
        processor = DuckDBDataProcessor(read_only=False)
        
        categories = ["crypto", "forex", "stock", "commodity"]
        all_stats = {}
        
        for category in categories:
            print(f"\nProcessing {category.upper()}...")
            stats = update_category_data(processor, category, force_update)
            all_stats[category] = stats
            
            success = stats.get("success", 0)
            failed = stats.get("failed", 0)
            skipped = stats.get("skipped", 0)
            print(f"   Results: {success} success, {failed} failed, {skipped} skipped")
        
        # Summary
        total_success = sum(stats.get("success", 0) for stats in all_stats.values())
        total_failed = sum(stats.get("failed", 0) for stats in all_stats.values())
        total_skipped = sum(stats.get("skipped", 0) for stats in all_stats.values())
        
        print("\n" + "="*50)
        print("OVERALL SUMMARY")
        print("="*50)
        print(f"Total Success: {total_success}")
        print(f"Total Failed: {total_failed}")
        print(f"Total Skipped: {total_skipped}")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full update test: {e}")
        return False

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test Data Ingestion Tasks")
    parser.add_argument("--category", choices=["crypto", "forex", "stock", "commodity"], 
                       help="Test specific category only")
    parser.add_argument("--force", action="store_true", help="Force update all data")
    parser.add_argument("--import-only", action="store_true", help="Test imports only")
    
    args = parser.parse_args()
    
    print("="*60)
    print("AUTONAMA DATA INGESTION TEST")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Test imports first
    if not test_data_processor_import():
        print("❌ Import test failed. Cannot proceed with data tests.")
        return 1
    
    if args.import_only:
        print("✅ Import test completed successfully!")
        return 0
    
    # Test specific category or all categories
    success = True
    
    if args.category:
        success = test_category_update(args.category, args.force)
    else:
        success = test_full_update(args.force)
    
    if success:
        print("\n✅ All tests completed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
