#!/usr/bin/env python3
"""
Simple PostgreSQL connection test that bypasses TimescaleDB issues.

This script tests basic PostgreSQL connectivity without TimescaleDB extensions.
"""

import os
import sys
import psycopg2
from datetime import datetime

def test_direct_connection():
    """Test direct PostgreSQL connection using psycopg2."""
    try:
        print("Testing direct PostgreSQL connection...")
        
        # Connection parameters
        host = os.getenv('POSTGRES_SERVER', 'postgres')
        port = os.getenv('POSTGRES_PORT', '5432')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        database = os.getenv('POSTGRES_DB', 'autonama')
        
        print(f"Connection parameters:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  User: {user}")
        print(f"  Database: {database}")
        
        # Try different connection approaches
        connection_strings = [
            f"host={host} port={port} dbname={database} user={user} password={password}",
            f"host={host} port={port} dbname=postgres user={user} password={password}",
            f"host={host} port={port} user={user} password={password}",
        ]
        
        for i, conn_str in enumerate(connection_strings, 1):
            try:
                print(f"\nAttempt {i}: {conn_str.replace(password, '***')}")
                
                conn = psycopg2.connect(conn_str)
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"✅ Connection successful!")
                print(f"   PostgreSQL version: {version}")
                
                # Test current user
                cursor.execute("SELECT current_user")
                current_user = cursor.fetchone()[0]
                print(f"   Current user: {current_user}")
                
                # Test database name
                cursor.execute("SELECT current_database()")
                current_db = cursor.fetchone()[0]
                print(f"   Current database: {current_db}")
                
                cursor.close()
                conn.close()
                return True
                
            except Exception as e:
                print(f"❌ Attempt {i} failed: {e}")
                continue
        
        print("❌ All connection attempts failed")
        return False
        
    except Exception as e:
        print(f"❌ Direct connection test failed: {e}")
        return False

def test_from_container():
    """Test connection from inside the container network."""
    try:
        print("\nTesting connection from container perspective...")
        
        # These are the connection parameters that should work from inside Docker
        connection_params = {
            'host': 'postgres',
            'port': '5432',
            'user': 'postgres',
            'password': 'postgres',
            'database': 'autonama'
        }
        
        conn_str = "host={host} port={port} dbname={database} user={user} password={password}".format(**connection_params)
        print(f"Connection string: {conn_str.replace('postgres', '***', 2)}")
        
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        
        # Test basic functionality
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()[0]
        print(f"✅ Basic query successful: {result}")
        
        # List databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = cursor.fetchall()
        print(f"✅ Available databases: {[db[0] for db in databases]}")
        
        # List users/roles
        cursor.execute("SELECT rolname FROM pg_roles")
        roles = cursor.fetchall()
        print(f"✅ Available roles: {[role[0] for role in roles]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Container connection test failed: {e}")
        return False

def test_create_simple_table():
    """Test creating a simple table without TimescaleDB extensions."""
    try:
        print("\nTesting table creation...")
        
        conn = psycopg2.connect(
            host='postgres',
            port='5432',
            user='postgres',
            password='postgres',
            database='autonama'
        )
        cursor = conn.cursor()
        
        # Create a simple test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                test_data TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_connection (test_data) VALUES (%s)", ("Connection test successful",))
        
        # Query test data
        cursor.execute("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        
        print(f"✅ Table operations successful:")
        print(f"   ID: {result[0]}")
        print(f"   Data: {result[1]}")
        print(f"   Created: {result[2]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Table creation test failed: {e}")
        return False

def main():
    """Main test function."""
    print("="*60)
    print("SIMPLE POSTGRESQL CONNECTION TEST")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    print()
    
    tests = [
        ("Direct Connection", test_direct_connection),
        ("Container Connection", test_from_container),
        ("Table Operations", test_create_simple_table),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("SIMPLE CONNECTION TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if passed > 0:
        print("\n✅ Basic PostgreSQL connection is working!")
        print("You can now proceed with TimescaleDB setup.")
        return 0
    else:
        print("\n❌ PostgreSQL connection is not working.")
        print("Please check the PostgreSQL service configuration.")
        return 1

if __name__ == "__main__":
    exit(main())
