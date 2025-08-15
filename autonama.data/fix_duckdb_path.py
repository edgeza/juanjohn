#!/usr/bin/env python3
"""
Script to fix DuckDB path issues and test database connectivity.

This script helps resolve the path mismatch between the environment variable
and the actual DuckDB file location.
"""

import os
import sys
import duckdb
from pathlib import Path

def check_duckdb_files():
    """Check for existing DuckDB files and their validity."""
    print("Checking for DuckDB files...")
    
    # Paths to check
    paths_to_check = [
        "/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb",
        "/home/tawanda/dev/autonama/v2/data/data/financial_data.duckdb",
        "data/financial_data.duckdb",
        os.getenv('DUCKDB_PATH', 'not_set')
    ]
    
    for path in paths_to_check:
        if path == 'not_set':
            print(f"❌ DUCKDB_PATH environment variable not set")
            continue
            
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ Found: {path} (size: {size} bytes)")
            
            # Test if it's a valid DuckDB file
            try:
                conn = duckdb.connect(path, read_only=True)
                conn.execute("SELECT 1")
                conn.close()
                print(f"   ✅ Valid DuckDB file")
            except Exception as e:
                print(f"   ❌ Invalid DuckDB file: {e}")
        else:
            print(f"❌ Not found: {path}")

def create_fresh_duckdb():
    """Create a fresh DuckDB database at the correct location."""
    correct_path = "/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb"
    
    print(f"\nCreating fresh DuckDB database at: {correct_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(correct_path), exist_ok=True)
    
    # Remove existing file if it exists
    if os.path.exists(correct_path):
        print(f"Removing existing file...")
        os.remove(correct_path)
    
    # Create new database
    try:
        conn = duckdb.connect(correct_path)
        
        # Create a simple test table to ensure the database is valid
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER,
                name VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        conn.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")
        
        # Verify the data
        result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
        print(f"✅ Database created successfully with {result[0]} test record")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def test_environment_path():
    """Test if the environment path works correctly."""
    env_path = os.getenv('DUCKDB_PATH')
    if not env_path:
        print("❌ DUCKDB_PATH environment variable not set")
        return False
    
    print(f"\nTesting environment path: {env_path}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        
        # Test connection
        conn = duckdb.connect(env_path)
        conn.execute("SELECT 1")
        conn.close()
        print(f"✅ Environment path works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Environment path failed: {e}")
        return False

def fix_path_issues():
    """Fix common path issues."""
    print("\n" + "="*60)
    print("FIXING DUCKDB PATH ISSUES")
    print("="*60)
    
    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check environment variables
    env_path = os.getenv('DUCKDB_PATH', 'not_set')
    print(f"DUCKDB_PATH environment variable: {env_path}")
    
    # Remove any corrupted files
    corrupted_paths = [
        "/home/tawanda/dev/autonama/v2/data/data/financial_data.duckdb",
        "data/financial_data.duckdb"
    ]
    
    for path in corrupted_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size == 0:
                print(f"Removing corrupted empty file: {path}")
                os.remove(path)
            else:
                print(f"Found non-empty file at: {path} (size: {size} bytes)")
    
    # Ensure the correct path has a valid database
    correct_path = "/home/tawanda/dev/autonama/v2/data/duckdb/financial_data.duckdb"
    
    if not os.path.exists(correct_path) or os.path.getsize(correct_path) == 0:
        print(f"Creating fresh database at correct path...")
        create_fresh_duckdb()
    else:
        # Test existing database
        try:
            conn = duckdb.connect(correct_path, read_only=True)
            conn.execute("SELECT 1")
            conn.close()
            print(f"✅ Existing database at correct path is valid")
        except Exception as e:
            print(f"❌ Existing database is corrupted: {e}")
            print(f"Creating fresh database...")
            create_fresh_duckdb()

def main():
    """Main function."""
    print("="*60)
    print("DUCKDB PATH DIAGNOSTIC AND FIX TOOL")
    print("="*60)
    
    # Check current state
    check_duckdb_files()
    
    # Fix issues
    fix_path_issues()
    
    # Test final state
    print("\n" + "="*60)
    print("FINAL STATE CHECK")
    print("="*60)
    check_duckdb_files()
    test_environment_path()
    
    print("\n✅ DuckDB path issues should now be resolved!")
    print("You can restart your Celery workers to test the fix.")

if __name__ == "__main__":
    main()
