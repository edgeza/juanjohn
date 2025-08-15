#!/usr/bin/env python3
"""
Script to call the new data ingestion Celery tasks.

This script demonstrates how to call the updated data ingestion tasks
from your application or other scripts.

Usage:
    python call_data_tasks.py [--category CATEGORY] [--force] [--async]
"""

import argparse
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def call_update_market_data(categories=None, force_update=False, async_call=True):
    """Call the update_market_data Celery task"""
    try:
        from tasks.data_ingestion import update_market_data
        
        print(f"Calling update_market_data task...")
        print(f"Categories: {categories or 'All'}")
        print(f"Force update: {force_update}")
        print(f"Async: {async_call}")
        print()
        
        if async_call:
            # Call asynchronously (returns immediately with task ID)
            result = update_market_data.delay(categories=categories, force_update=force_update)
            print(f"✅ Task submitted successfully!")
            print(f"Task ID: {result.id}")
            print(f"Task State: {result.state}")
            
            # You can check the result later with:
            # result.get()  # This will block until completion
            # or result.ready()  # This returns True if completed
            
            return result
        else:
            # Call synchronously (blocks until completion)
            result = update_market_data(categories=categories, force_update=force_update)
            print(f"✅ Task completed successfully!")
            print(f"Result: {result}")
            return result
            
    except Exception as e:
        print(f"❌ Error calling update_market_data: {e}")
        return None

def call_update_single_category(category, force_update=False, async_call=True):
    """Call the update_single_category Celery task"""
    try:
        from tasks.data_ingestion import update_single_category
        
        print(f"Calling update_single_category task...")
        print(f"Category: {category}")
        print(f"Force update: {force_update}")
        print(f"Async: {async_call}")
        print()
        
        if async_call:
            # Call asynchronously
            result = update_single_category.delay(category=category, force_update=force_update)
            print(f"✅ Task submitted successfully!")
            print(f"Task ID: {result.id}")
            print(f"Task State: {result.state}")
            return result
        else:
            # Call synchronously
            result = update_single_category(category=category, force_update=force_update)
            print(f"✅ Task completed successfully!")
            print(f"Result: {result}")
            return result
            
    except Exception as e:
        print(f"❌ Error calling update_single_category: {e}")
        return None

def monitor_task(result):
    """Monitor a Celery task result"""
    if not result:
        return
    
    print(f"\nMonitoring task {result.id}...")
    
    try:
        import time
        
        while not result.ready():
            print(f"Task state: {result.state}")
            if result.state == 'PROGRESS':
                info = result.info
                if isinstance(info, dict):
                    current = info.get('current', 0)
                    total = info.get('total', 0)
                    status = info.get('status', 'Processing')
                    print(f"Progress: {current}/{total} - {status}")
            
            time.sleep(2)
        
        # Task completed
        print(f"Task completed with state: {result.state}")
        if result.successful():
            print(f"Result: {result.result}")
        else:
            print(f"Error: {result.result}")
            
    except Exception as e:
        print(f"Error monitoring task: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Call Data Ingestion Celery Tasks")
    parser.add_argument("--category", choices=["crypto", "forex", "stock", "commodity"], 
                       help="Update specific category only")
    parser.add_argument("--force", action="store_true", help="Force update all data")
    parser.add_argument("--sync", action="store_true", help="Call synchronously (blocks until completion)")
    parser.add_argument("--monitor", action="store_true", help="Monitor task progress (only works with async)")
    
    args = parser.parse_args()
    
    print("="*60)
    print("AUTONAMA DATA INGESTION TASK CALLER")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    async_call = not args.sync
    
    # Call the appropriate task
    if args.category:
        result = call_update_single_category(args.category, args.force, async_call)
    else:
        result = call_update_market_data(None, args.force, async_call)
    
    # Monitor if requested and async
    if args.monitor and async_call and result:
        monitor_task(result)
    
    print("\n✅ Task call completed!")

if __name__ == "__main__":
    main()
