#!/usr/bin/env python3
"""
Test script to check if celery can start without problematic tasks
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from celery_app_minimal import celery_app
    print("✅ Celery app imported successfully")
    
    # Test basic celery functionality
    print("✅ Celery configuration loaded")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Result Backend: {celery_app.conf.result_backend}")
    print(f"Included tasks: {celery_app.conf.include}")
    
    print("✅ All tests passed - Celery should work!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1) 