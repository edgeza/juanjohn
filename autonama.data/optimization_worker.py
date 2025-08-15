#!/usr/bin/env python3
"""
Optimization Ingestion Worker

This worker processes optimization ingestion tasks from the queue.
It scans the hotbox folder for latest export data and ingests it into PostgreSQL.
"""

import os
import sys
import json
import logging
import redis
from datetime import datetime
from typing import Dict, Any

# Add the tasks directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tasks.optimization_ingestion import OptimizationDataIngestion

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("optimization_worker.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class OptimizationIngestionWorker:
    def __init__(self):
        """Initialize the worker"""
        self.redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.queue_name = "optimization_ingestion_queue"
        self.ingestion = OptimizationDataIngestion()
        
    def process_job(self, job_message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single job"""
        try:
            logger.info(f"Processing job: {job_message['task_id']}")
            
            # Update job status to processing
            self._update_job_status(job_message['task_id'], 'processing')
            
            # Run the ingestion
            results = self.ingestion.ingest_latest_data()
            
            # Update job status to completed
            self._update_job_status(job_message['task_id'], 'completed', results=results)
            
            logger.info(f"Job {job_message['task_id']} completed successfully")
            return {
                'status': 'success',
                'task_id': job_message['task_id'],
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing job {job_message['task_id']}: {e}")
            
            # Update job status to failed
            self._update_job_status(job_message['task_id'], 'failed', error=str(e))
            
            return {
                'status': 'error',
                'task_id': job_message['task_id'],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_job_status(self, task_id: str, status: str, results: Dict = None, error: str = None):
        """Update job status in database"""
        try:
            # This would typically update a database table
            # For now, we'll just log the status
            logger.info(f"Job {task_id} status updated to: {status}")
            if results:
                logger.info(f"Job {task_id} results: {results}")
            if error:
                logger.error(f"Job {task_id} error: {error}")
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    def run(self):
        """Main worker loop"""
        logger.info("Starting Optimization Ingestion Worker")
        logger.info(f"Listening on queue: {self.queue_name}")
        
        while True:
            try:
                # Wait for a job
                result = self.redis_client.brpop(self.queue_name, timeout=1)
                
                if result:
                    queue_name, job_data = result
                    job_message = json.loads(job_data)
                    
                    logger.info(f"Received job: {job_message['task_id']}")
                    
                    # Process the job
                    result = self.process_job(job_message)
                    
                    logger.info(f"Job {job_message['task_id']} processed: {result['status']}")
                    
                else:
                    # No job available, continue loop
                    continue
                    
            except KeyboardInterrupt:
                logger.info("Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                continue

def main():
    """Main function"""
    try:
        worker = OptimizationIngestionWorker()
        worker.run()
    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 