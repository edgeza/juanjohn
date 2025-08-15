#!/bin/bash

# Celery Management Script
# This script provides easy management of Celery workers and beat scheduler

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create runtime directory
mkdir -p runtime/celery
chmod 755 runtime/celery

# Function to show usage
show_usage() {
    echo "Usage: $0 {worker|beat|flower|status|stop|restart|logs|clean}"
    echo ""
    echo "Commands:"
    echo "  worker   - Start Celery worker"
    echo "  beat     - Start Celery beat scheduler"
    echo "  flower   - Start Flower monitoring"
    echo "  status   - Show Celery status"
    echo "  stop     - Stop all Celery processes"
    echo "  restart  - Restart all Celery processes"
    echo "  logs     - Show recent logs"
    echo "  clean    - Clean runtime files"
    echo ""
}

# Function to start worker
start_worker() {
    echo -e "${GREEN}🚀 Starting Celery Worker...${NC}"
    celery -A celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --pidfile=runtime/celery/worker.pid \
        --logfile=runtime/celery/worker.log
}

# Function to start beat
start_beat() {
    echo -e "${GREEN}🕐 Starting Celery Beat Scheduler...${NC}"
    
    # Clean up any existing schedule files
    rm -f runtime/celery/celerybeat-schedule*
    
    celery -A celery_app beat \
        --loglevel=info \
        --schedule=runtime/celery/celerybeat-schedule \
        --pidfile=runtime/celery/celerybeat.pid \
        --logfile=runtime/celery/beat.log
}

# Function to start flower
start_flower() {
    echo -e "${GREEN}🌸 Starting Flower Monitoring...${NC}"
    celery -A celery_app flower \
        --port=5555 \
        --pidfile=runtime/celery/flower.pid \
        --logfile=runtime/celery/flower.log
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Celery Status${NC}"
    echo "=================="
    
    # Check if processes are running
    if [ -f "runtime/celery/worker.pid" ]; then
        PID=$(cat runtime/celery/worker.pid 2>/dev/null || echo "")
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo -e "Worker:  ${GREEN}✅ Running (PID: $PID)${NC}"
        else
            echo -e "Worker:  ${RED}❌ Not running${NC}"
        fi
    else
        echo -e "Worker:  ${RED}❌ Not running${NC}"
    fi
    
    if [ -f "runtime/celery/celerybeat.pid" ]; then
        PID=$(cat runtime/celery/celerybeat.pid 2>/dev/null || echo "")
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo -e "Beat:    ${GREEN}✅ Running (PID: $PID)${NC}"
        else
            echo -e "Beat:    ${RED}❌ Not running${NC}"
        fi
    else
        echo -e "Beat:    ${RED}❌ Not running${NC}"
    fi
    
    if [ -f "runtime/celery/flower.pid" ]; then
        PID=$(cat runtime/celery/flower.pid 2>/dev/null || echo "")
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo -e "Flower:  ${GREEN}✅ Running (PID: $PID)${NC}"
        else
            echo -e "Flower:  ${RED}❌ Not running${NC}"
        fi
    else
        echo -e "Flower:  ${RED}❌ Not running${NC}"
    fi
    
    echo ""
    echo "Active tasks:"
    celery -A celery_app inspect active 2>/dev/null || echo "No active tasks"
    
    echo ""
    echo "Scheduled tasks:"
    celery -A celery_app inspect scheduled 2>/dev/null || echo "No scheduled tasks"
}

# Function to stop processes
stop_processes() {
    echo -e "${YELLOW}🛑 Stopping Celery processes...${NC}"
    
    # Stop worker
    if [ -f "runtime/celery/worker.pid" ]; then
        PID=$(cat runtime/celery/worker.pid 2>/dev/null || echo "")
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo "Stopping worker (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            sleep 2
            kill -KILL "$PID" 2>/dev/null || true
        fi
        rm -f runtime/celery/worker.pid
    fi
    
    # Stop beat
    if [ -f "runtime/celery/celerybeat.pid" ]; then
        PID=$(cat runtime/celery/celerybeat.pid 2>/dev/null || echo "")
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo "Stopping beat (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            sleep 2
            kill -KILL "$PID" 2>/dev/null || true
        fi
        rm -f runtime/celery/celerybeat.pid
    fi
    
    # Stop flower
    if [ -f "runtime/celery/flower.pid" ]; then
        PID=$(cat runtime/celery/flower.pid 2>/dev/null || echo "")
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo "Stopping flower (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            sleep 2
            kill -KILL "$PID" 2>/dev/null || true
        fi
        rm -f runtime/celery/flower.pid
    fi
    
    echo -e "${GREEN}✅ All processes stopped${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Recent Celery Logs${NC}"
    echo "====================="
    
    if [ -f "runtime/celery/worker.log" ]; then
        echo -e "${YELLOW}Worker logs (last 20 lines):${NC}"
        tail -20 runtime/celery/worker.log
        echo ""
    fi
    
    if [ -f "runtime/celery/beat.log" ]; then
        echo -e "${YELLOW}Beat logs (last 20 lines):${NC}"
        tail -20 runtime/celery/beat.log
        echo ""
    fi
    
    if [ -f "runtime/celery/flower.log" ]; then
        echo -e "${YELLOW}Flower logs (last 20 lines):${NC}"
        tail -20 runtime/celery/flower.log
        echo ""
    fi
}

# Function to clean runtime files
clean_runtime() {
    echo -e "${YELLOW}🧹 Cleaning runtime files...${NC}"
    
    # Stop processes first
    stop_processes
    
    # Remove runtime files
    rm -rf runtime/celery/*
    
    echo -e "${GREEN}✅ Runtime files cleaned${NC}"
}

# Main script logic
case "${1:-}" in
    worker)
        start_worker
        ;;
    beat)
        start_beat
        ;;
    flower)
        start_flower
        ;;
    status)
        show_status
        ;;
    stop)
        stop_processes
        ;;
    restart)
        stop_processes
        sleep 2
        echo -e "${GREEN}🔄 Restarting services...${NC}"
        # You can add specific restart logic here
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_runtime
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
