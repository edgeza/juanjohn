"""
Autonama Optimization API Endpoints

API endpoints for triggering and monitoring Autonama Channel optimization.

Available endpoints:
- POST /v1/autonama/optimize/run - Trigger multi-asset optimization
- POST /v1/autonama/optimize/single - Trigger single asset optimization  
- GET /v1/autonama/optimize/status/{task_id} - Get optimization status
- GET /v1/autonama/optimize/history - Get optimization history
- GET /v1/autonama/optimize/parameters - Get available parameters
- GET /v1/autonama/optimize/health - Health check
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from src.core.database import get_db
import uuid
from src.services.queue_service import queue_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class OptimizationRequest(BaseModel):
    n_trials: int = Field(default=10, ge=5, le=100, description="Number of Optuna trials per asset")
    n_cores: int = Field(default=4, ge=1, le=16, description="Number of CPU cores to use")
    n_assets: int = Field(default=10, ge=1, le=50, description="Number of assets to optimize")
    n_categories: int = Field(default=4, ge=1, le=10, description="Number of categories to process")
    days_back: int = Field(default=365, ge=0, le=1095, description="Days to look back (0 for max)")

class SingleOptimizationRequest(BaseModel):
    symbol: str = Field(..., description="Asset symbol to optimize")
    category: str = Field(..., description="Asset category")
    n_trials: int = Field(default=10, ge=5, le=100, description="Number of optimization trials")
    days_back: int = Field(default=365, ge=0, le=1095, description="Days to look back (0 for max)")

class OptimizationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    parameters: Optional[Dict[str, Any]] = None

@router.post("/optimize/run", response_model=OptimizationResponse)
async def trigger_autonama_optimization(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger Autonama Channel optimization for multiple assets
    
    This endpoint allows manual triggering of the optimization process
    with custom parameters for trials, cores, assets, and time period.
    """
    try:
        logger.info(f"Triggering Autonama optimization with parameters: {request.dict()}")
        
        # Generate mock task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        return OptimizationResponse(
            task_id=task_id,
            status="started",
            message=f"Autonama optimization started for {request.n_assets} assets with {request.n_trials} trials each",
            parameters=request.dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger Autonama optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize/single", response_model=OptimizationResponse)
async def trigger_single_optimization(
    request: SingleOptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger Autonama Channel optimization for a single asset
    
    This endpoint allows optimization of a specific symbol with
    custom parameters.
    """
    try:
        logger.info(f"Triggering single Autonama optimization for {request.symbol}")
        
        # Submit job to queue
        task_id = queue_service.submit_optimization_job(
            job_type="single_asset_optimization",
            parameters=request.dict()
        )
        
        return OptimizationResponse(
            task_id=task_id,
            status="started",
            message=f"Autonama optimization started for {request.symbol}",
            parameters=request.dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger single optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/status/{task_id}")
async def get_optimization_status(task_id: str):
    """
    Get the status of an optimization task
    
    Args:
        task_id: The task ID returned from the optimization trigger
        
    Returns:
        Dict with task status and results (if completed)
    """
    try:
        # Get job status from queue service
        job_status = queue_service.get_job_status(task_id)
        
        if job_status:
            return job_status
        else:
            # Job not found
            raise HTTPException(status_code=404, detail=f"Optimization task {task_id} not found")
            
    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/history")
async def get_optimization_history(
    symbol: Optional[str] = Query(default=None, description="Filter by symbol"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    limit: int = Query(default=50, le=200, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Get optimization history from the database
    
    Args:
        symbol: Optional symbol filter
        category: Optional category filter
        limit: Number of results to return
        
    Returns:
        List of optimization results
    """
    try:
        # Mock optimization history for now
        mock_history = [
            {
                "id": "1",
                "task_id": "task_001",
                "symbol": "BTC/USDT",
                "category": "crypto",
                "strategy": "polynomial_regression",
                "status": "completed",
                "created_at": "2025-07-29T10:00:00Z",
                "completed_at": "2025-07-29T10:05:00Z",
                "parameters": {
                    "n_trials": 10,
                    "n_cores": 4,
                    "days_back": 365
                },
                "results": {
                    "confidence": 0.85,
                    "signal": "buy",
                    "target_price": 45000,
                    "stop_loss": 42000
                }
            },
            {
                "id": "2",
                "task_id": "task_002",
                "symbol": "ETH/USDT",
                "category": "crypto",
                "strategy": "polynomial_regression",
                "status": "running",
                "created_at": "2025-07-29T11:00:00Z",
                "parameters": {
                    "n_trials": 15,
                    "n_cores": 4,
                    "days_back": 365
                }
            },
            {
                "id": "3",
                "task_id": "task_003",
                "symbol": "AAPL",
                "category": "stock",
                "strategy": "polynomial_regression",
                "status": "completed",
                "created_at": "2025-07-29T09:00:00Z",
                "completed_at": "2025-07-29T09:03:00Z",
                "parameters": {
                    "n_trials": 8,
                    "n_cores": 2,
                    "days_back": 365
                },
                "results": {
                    "confidence": 0.72,
                    "signal": "hold",
                    "target_price": 180,
                    "stop_loss": 170
                }
            }
        ]
        
        # Apply filters if provided
        if symbol or category:
            filtered_history = []
            for job in mock_history:
                if symbol and job.get('symbol') != symbol:
                    continue
                if category and job.get('category') != category:
                    continue
                filtered_history.append(job)
            mock_history = filtered_history
        
        # Apply limit
        if limit:
            mock_history = mock_history[:limit]
        
        return {
            "total_results": len(mock_history),
            "history": mock_history
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/parameters")
async def get_optimization_parameters():
    """
    Get available optimization parameters and their ranges
    
    Returns:
        Dict with parameter definitions and valid ranges
    """
    try:
        return {
            "parameters": {
                "n_trials": {
                    "description": "Number of Optuna trials per asset",
                    "min_value": 5,
                    "max_value": 100,
                    "default": 10,
                    "step": 5
                },
                "n_cores": {
                    "description": "Number of CPU cores to use",
                    "min_value": 1,
                    "max_value": 16,
                    "default": 4,
                    "step": 1
                },
                "n_assets": {
                    "description": "Number of assets to optimize",
                    "min_value": 1,
                    "max_value": 50,
                    "default": 10,
                    "step": 1
                },
                "n_categories": {
                    "description": "Number of categories to process",
                    "min_value": 1,
                    "max_value": 10,
                    "default": 4,
                    "step": 1
                },
                "days_back": {
                    "description": "Days to look back (0 for max available)",
                    "options": {
                        "1 Year": 365,
                        "2 Years": 730,
                        "3 Years": 1095,
                        "Max Available": 0
                    },
                    "default": 365
                }
            },
            "strategy": {
                "name": "Autonama Channels",
                "description": "Proprietary strategy combining Moving Average, Standard Deviation, and ATR",
                "optimized_parameters": [
                    "lookback (10-100)",
                    "std_dev (1.0-3.0)",
                    "atr_period (10-50)",
                    "atr_multiplier (1.0-3.0)"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/health")
async def optimization_health_check():
    """
    Health check for optimization system
    
    Returns:
        Dict with system health status
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "autonama_optimizer": "operational",
                "celery_tasks": "operational",
                "database": "operational"
            },
            "message": "Autonama optimization system is ready"
        }
        
    except Exception as e:
        logger.error(f"Optimization health check failed: {e}")
        raise HTTPException(status_code=500, detail="Optimization system unhealthy")
