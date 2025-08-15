"""
Task handlers for processing different types of tasks from the queue.
These act as adapters between the queue system and existing task modules.
"""
import logging
from typing import Dict, Any, Callable
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def process_data_ingestion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a data ingestion task.
    
    Args:
        payload: Task payload containing ingestion parameters
        
    Returns:
        Dict with results or error information
    """
    try:
        from tasks.data_ingestion import update_market_data
        
        # Extract parameters from payload with defaults
        asset = payload.get('asset')
        timeframe = payload.get('timeframe', '1d')
        days_back = payload.get('days_back', 30)
        
        logger.info(f"Starting data ingestion for {asset} ({timeframe}), last {days_back} days")
        
        # Call the existing data ingestion function
        result = update_market_data(asset, timeframe, days_back)
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Error in data ingestion: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

def process_optimization(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an optimization task.
    
    Args:
        payload: Task payload containing optimization parameters
        
    Returns:
        Dict with results or error information
    """
    try:
        from tasks.optimization import run_optimization
        
        # Extract parameters from payload with defaults
        symbol = payload.get('symbol')
        category = payload.get('category', 'crypto')
        n_trials = payload.get('n_trials', 10)
        days_back = payload.get('days_back', 365)
        
        logger.info(f"Starting optimization for {symbol} ({category}), {n_trials} trials, {days_back} days back")
        
        # Call the existing optimization function
        result = run_optimization(symbol, category, n_trials, days_back)
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Error in optimization: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

# Map of task types to their handler functions
TASK_HANDLERS = {
    'data_ingestion': process_data_ingestion,
    'optimization': process_optimization
}

def get_task_handler(task_type: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Get the appropriate handler function for a task type.
    
    Args:
        task_type: Type of task to get handler for
        
    Returns:
        Handler function for the task type
        
    Raises:
        ValueError: If no handler exists for the task type
    """
    handler = TASK_HANDLERS.get(task_type)
    if not handler:
        raise ValueError(f"No handler found for task type: {task_type}")
    return handler
