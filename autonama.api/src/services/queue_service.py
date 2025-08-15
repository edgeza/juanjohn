"""
Queue Service - Lightweight job queue management

This service handles job queuing without importing heavy worker dependencies.
Uses Redis directly for simple message passing and database for job tracking.
"""

import json
import uuid
import redis
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db
from ..core.config import settings

class QueueService:
    """Lightweight queue service for job management"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        
    def submit_optimization_job(
        self, 
        job_type: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Submit an optimization job to the queue"""
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create job message
        job_message = {
            'task_id': task_id,
            'job_type': job_type,
            'parameters': parameters,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # Store job in database
        self._store_job_in_database(job_message)
        
        # Queue job in Redis - use different queues based on job type
        if job_type == "optimization_ingestion":
            queue_name = "optimization_ingestion_queue"
        else:
            queue_name = "optimization_queue"
            
        self.redis_client.lpush(queue_name, json.dumps(job_message))
        
        return task_id
    
    def get_job_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get job status from database"""
        
        db = next(get_db())
        try:
            # Query optimization tasks table
            query = text("""
                SELECT 
                    task_id,
                    status,
                    progress,
                    result_id,
                    error_message,
                    started_at,
                    completed_at,
                    created_at
                FROM optimization.tasks 
                WHERE task_id = :task_id
            """)
            
            result = db.execute(query, {"task_id": task_id}).fetchone()
            
            if result:
                job_data = {
                    'task_id': result.task_id,
                    'status': result.status,
                    'progress': result.progress or 0,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'started_at': result.started_at.isoformat() if result.started_at else None,
                    'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                    'error_message': result.error_message
                }
                
                # If completed, get results
                if result.status == 'completed' and result.result_id:
                    results = self._get_optimization_results(db, result.result_id)
                    if results:
                        job_data['results'] = results
                
                return job_data
            
            return None
            
        finally:
            db.close()
    
    def get_job_history(self, limit: int = 50) -> list:
        """Get optimization job history"""
        
        db = next(get_db())
        try:
            query = text("""
                SELECT 
                    t.task_id,
                    t.status,
                    t.progress,
                    t.error_message,
                    t.started_at,
                    t.completed_at,
                    t.created_at,
                    r.parameters
                FROM optimization.tasks t
                LEFT JOIN optimization.results r ON t.result_id = r.id
                ORDER BY t.created_at DESC
                LIMIT :limit
            """)
            
            results = db.execute(query, {"limit": limit}).fetchall()
            
            jobs = []
            for row in results:
                job = {
                    'task_id': row.task_id,
                    'status': row.status,
                    'progress': row.progress or 0,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'started_at': row.started_at.isoformat() if row.started_at else None,
                    'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                    'error_message': row.error_message,
                    'parameters': row.parameters if row.parameters else {}
                }
                jobs.append(job)
            
            return jobs
            
        finally:
            db.close()
    
    def _store_job_in_database(self, job_message: Dict[str, Any]):
        """Store job in database for tracking"""
        
        db = next(get_db())
        try:
            query = text("""
                INSERT INTO optimization.tasks 
                (task_id, strategy_name, symbol, timeframe, status, created_at)
                VALUES (:task_id, :strategy_name, :symbol, :timeframe, :status, :created_at)
            """)
            
            # Extract parameters
            params = job_message.get('parameters', {})
            
            db.execute(query, {
                'task_id': job_message['task_id'],
                'strategy_name': 'Autonama Channels',
                'symbol': params.get('symbol', 'MULTI'),
                'timeframe': '1h',
                'status': 'pending',
                'created_at': datetime.utcnow()
            })
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _get_optimization_results(self, db: Session, result_id: str) -> Optional[Dict[str, Any]]:
        """Get optimization results from database"""
        
        try:
            query = text("""
                SELECT 
                    total_return,
                    sharpe_ratio,
                    max_drawdown,
                    win_rate,
                    profit_factor,
                    parameters,
                    metrics
                FROM optimization.results 
                WHERE id = :result_id
            """)
            
            result = db.execute(query, {"result_id": result_id}).fetchone()
            
            if result:
                return {
                    'total_return': float(result.total_return) if result.total_return else 0,
                    'sharpe_ratio': float(result.sharpe_ratio) if result.sharpe_ratio else 0,
                    'max_drawdown': float(result.max_drawdown) if result.max_drawdown else 0,
                    'win_rate': float(result.win_rate) if result.win_rate else 0,
                    'profit_factor': float(result.profit_factor) if result.profit_factor else 0,
                    'parameters': result.parameters if result.parameters else {},
                    'metrics': result.metrics if result.metrics else {}
                }
            
            return None
            
        except Exception:
            return None

# Global queue service instance
queue_service = QueueService()