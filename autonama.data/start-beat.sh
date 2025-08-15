#!/bin/bash

# Celery Beat Startup Script
# This script properly starts Celery Beat with correct permissions and file paths

set -e

echo "🕐 Starting Celery Beat Scheduler..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create runtime directory
mkdir -p runtime/celery
chmod 755 runtime/celery

# Remove any existing schedule files to start fresh
rm -f runtime/celery/celerybeat-schedule*
rm -f celerybeat-schedule*

# Set proper permissions
chmod 755 runtime
chmod 755 runtime/celery

echo "📁 Runtime directory prepared: $(pwd)/runtime/celery"

# Start Celery Beat with proper configuration
echo "🚀 Starting Celery Beat..."
exec celery -A celery_app beat \
    --loglevel=info \
    --schedule=runtime/celery/celerybeat-schedule \
    --pidfile=runtime/celery/celerybeat.pid
