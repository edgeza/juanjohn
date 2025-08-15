#!/usr/bin/env python3
"""
DuckDB Synchronization Script

This script keeps the DuckDB files synchronized between the two paths:
1. /home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb (correct path)
2. /home/tawanda/dev/autonama/v2/data/data/financial_data.duckdb (expected by simple directory)

This ensures both the v2 system and the simple directory can access the same database.
"""

import os
import shutil
import time
from datetime import datetime

def sync_duckdb_files():
    """Synchronize DuckDB files between the two paths."""
    
    # Define paths
    correct_path = "/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb"
    expected_path = "/home/tawanda/dev/autonama/v2/data/data/financial_data.duckdb"
    
    print(f"Synchronizing DuckDB files...")
    print(f"Source (correct): {correct_path}")
    print(f"Target (expected): {expected_path}")
    
    # Check if source exists
    if not os.path.exists(correct_path):
        print(f"❌ Source file does not exist: {correct_path}")
        return False
    
    # Get source file info
    source_size = os.path.getsize(correct_path)
    source_mtime = os.path.getmtime(correct_path)
    
    print(f"Source file: {source_size} bytes, modified: {datetime.fromtimestamp(source_mtime)}")
    
    # Check if target exists and compare
    needs_sync = True
    if os.path.exists(expected_path):
        target_size = os.path.getsize(expected_path)
        target_mtime = os.path.getmtime(expected_path)
        
        print(f"Target file: {target_size} bytes, modified: {datetime.fromtimestamp(target_mtime)}")
        
        # Check if files are the same
        if source_size == target_size and abs(source_mtime - target_mtime) < 1:
            print("✅ Files are already synchronized")
            needs_sync = False
    else:
        print("Target file does not exist")
    
    if needs_sync:
        try:
            # Ensure target directory exists
            os.makedirs(os.path.dirname(expected_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(correct_path, expected_path)
            
            # Verify copy
            if os.path.exists(expected_path):
                new_size = os.path.getsize(expected_path)
                print(f"✅ File synchronized successfully ({new_size} bytes)")
                return True
            else:
                print("❌ File copy failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during synchronization: {e}")
            return False
    
    return True

def setup_sync_cron():
    """Setup a cron job to sync files periodically."""
    print("\nTo setup automatic synchronization, add this to your crontab:")
    print("# Sync DuckDB files every 5 minutes")
    print(f"*/5 * * * * cd /home/tawanda/dev/autonama/v2/data && python sync_duckdb.py")
    print("\nRun: crontab -e")

def main():
    """Main function."""
    print("="*60)
    print("DUCKDB SYNCHRONIZATION TOOL")
    print("="*60)
    
    success = sync_duckdb_files()
    
    if success:
        print("\n✅ DuckDB synchronization completed successfully!")
    else:
        print("\n❌ DuckDB synchronization failed!")
    
    setup_sync_cron()

if __name__ == "__main__":
    main()
