#!/usr/bin/env python3
"""
Test script to validate SQL parameter formatting fixes
"""

import re

def test_sql_parameter_formatting():
    """Test that SQL queries use correct SQLAlchemy parameter format"""
    
    # Read the fixed file
    with open('v2/data/tasks/timescale_data_ingestion.py', 'r') as f:
        content = f.read()
    
    # Check for old psycopg2-style parameters (should be 0)
    old_params = re.findall(r'%\([a-zA-Z_]+\)s', content)
    old_params = [p for p in old_params if 'timestamp' not in p and 'level' not in p and 'message' not in p]  # Exclude logging
    
    # Check for new SQLAlchemy-style parameters (should be > 0)
    new_params = re.findall(r':[a-zA-Z_]+', content)
    sql_new_params = [p for p in new_params if p in [':symbol', ':exchange', ':timeframe', ':start_time', ':limit', ':indicator_name', ':indicator_value', ':created_at', ':timestamp']]
    
    print("🔍 SQL Parameter Formatting Test Results:")
    print("=" * 50)
    
    if old_params:
        print(f"❌ Found {len(old_params)} old-style parameters (%(param)s):")
        for param in old_params:
            print(f"   - {param}")
        return False
    else:
        print("✅ No old-style parameters found")
    
    if sql_new_params:
        print(f"✅ Found {len(sql_new_params)} new-style parameters (:param):")
        for param in set(sql_new_params):
            print(f"   - {param}")
    else:
        print("⚠️  No new-style parameters found")
    
    # Test specific SQL queries
    print("\n🔍 Testing Specific SQL Queries:")
    print("=" * 50)
    
    # Test SELECT query
    select_pattern = r'WHERE symbol = :symbol'
    if re.search(select_pattern, content):
        print("✅ SELECT query parameter format: FIXED")
    else:
        print("❌ SELECT query parameter format: NOT FIXED")
        return False
    
    # Test INSERT query  
    insert_pattern = r'VALUES \(:symbol, :timeframe, :timestamp'
    if re.search(insert_pattern, content):
        print("✅ INSERT query parameter format: FIXED")
    else:
        print("❌ INSERT query parameter format: NOT FIXED")
        return False
    
    print("\n🎉 All SQL parameter formatting issues have been FIXED!")
    return True

if __name__ == "__main__":
    success = test_sql_parameter_formatting()
    exit(0 if success else 1)