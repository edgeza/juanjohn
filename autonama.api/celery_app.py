"""
Celery App Entry Point

This file serves as the entry point for Celery commands
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the celery app from src.core
from src.core.celery_app import celery_app

# Make it available for Celery commands
if __name__ == '__main__':
    celery_app.start() 