"""
Worker Daemon.

This module listens to the Redis ready queue and executes tasks.
It handles state transitions (PENDING -> RUNNING -> COMPLETED/FAILED/DLQ),
retries on failure, and moving exhausted tasks to the DLQ.
"""

import time
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Task, TaskStatus
import queue_manager
from tasks import TASK_REGISTRY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_task(task_id: str):
    """
    Retrieves the task from the database, executes the corresponding function
    from the TASK_REGISTRY, and updates the task status and result.
    If the task fails, it increments the retry count and re-enqueues it,
    or moves it to the Dead Letter Queue if max retries are exceeded.
    """
    db: Session = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found in database. Skipping.")
            return

        # Double check status to avoid reprocessing if another worker picked it up (though Redis pop should prevent this mostly)
        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            logger.info(f"Task {task_id} is already in status {task.status}. Skipping.")
            return

        # Mark as running
        task.status = TaskStatus.RUNNING
        db.commit()

        task_func = TASK_REGISTRY.get(task.task_name)
        if not task_func:
            raise ValueError(f"Task function '{task.task_name}' not found in registry.")

        logger.info(f"Executing task {task_id} ({task.task_name}) - Attempt {task.retries + 1}")
        
        # Execute the function
        result = task_func(task.payload or {})
        
        # Success
        task.status = TaskStatus.COMPLETED
        task.result = result
        db.commit()
        logger.info(f"Task {task_id} completed successfully.")

    except Exception as e:
        db.rollback()
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
            
        task.retries += 1
        task.error_message = str(e)
        logger.error(f"Task {task_id} failed: {e}")

        if task.retries < task.max_retries:
            logger.info(f"Re-enqueuing task {task_id} (Retry {task.retries}/{task.max_retries})")
            db.commit()
            # Push back to the end of the queue
            queue_manager.enqueue_task(task_id)
        else:
            logger.error(f"Task {task_id} exceeded max retries. Moving to DLQ.")
            task.status = TaskStatus.DLQ
            db.commit()
            queue_manager.move_to_dlq(task_id)
            
    finally:
        db.close()

def main():
    logger.info("Starting worker daemon...")
    while True:
        try:
            task_id = queue_manager.dequeue_task(timeout=5)
            if task_id:
                process_task(task_id)
        except Exception as e:
            logger.error(f"Worker encountered a generic error: {e}")
            time.sleep(1) # Prevent tight loop on Redis connection failure

if __name__ == "__main__":
    main()
