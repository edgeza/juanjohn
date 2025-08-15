#!/usr/bin/env python3
"""
Queue Service for Autonama API

This module provides a lightweight job queue management system for the API.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class QueueService:
    """Lightweight job queue service"""
    
    def __init__(self):
        self.jobs = {}
        self.job_history = []
    
    def submit_job(self, job_type: str, data: Dict[str, Any] = None) -> str:
        """
        Submit a new job to the queue
        
        Args:
            job_type: Type of job to submit
            data: Job data
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = {
            'id': job_id,
            'type': job_type,
            'data': data or {},
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.jobs[job_id] = job
        logger.info(f"Job submitted: {job_id} ({job_type})")
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, result: Any = None):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = status
            self.jobs[job_id]['updated_at'] = datetime.now().isoformat()
            if result is not None:
                self.jobs[job_id]['result'] = result
            logger.info(f"Job {job_id} status updated to: {status}")
    
    def complete_job(self, job_id: str, result: Any = None):
        """Mark job as completed"""
        self.update_job_status(job_id, 'completed', result)
        # Move to history
        if job_id in self.jobs:
            self.job_history.append(self.jobs.pop(job_id))
    
    def fail_job(self, job_id: str, error: str = None):
        """Mark job as failed"""
        self.update_job_status(job_id, 'failed', {'error': error})
        # Move to history
        if job_id in self.jobs:
            self.job_history.append(self.jobs.pop(job_id))
    
    def get_pending_jobs(self, job_type: str = None) -> list:
        """Get all pending jobs"""
        jobs = [job for job in self.jobs.values() if job['status'] == 'pending']
        if job_type:
            jobs = [job for job in jobs if job['type'] == job_type]
        return jobs
    
    def get_job_history(self, limit: int = 100) -> list:
        """Get job history"""
        return self.job_history[-limit:]
    
    def clear_history(self):
        """Clear job history"""
        self.job_history.clear()

# Global queue service instance
queue_service = QueueService() 