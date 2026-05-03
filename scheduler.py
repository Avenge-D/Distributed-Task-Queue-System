"""
Scheduler Daemon.

This module is responsible for polling the Redis scheduled queue
and promoting tasks to the ready queue when their execution time is due.
"""

import time
import logging
import queue_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main loop for the scheduler. 
    Continuously checks for due tasks and promotes them.
    """
    logger.info("Starting scheduler daemon...")
    while True:
        try:
            moved_count = queue_manager.promote_due_scheduled_tasks()
            if moved_count > 0:
                logger.info(f"Moved {moved_count} scheduled tasks to ready queue.")
            
            # Sleep a short duration to avoid high CPU usage
            time.sleep(1)
        except Exception as e:
            logger.error(f"Scheduler encountered an error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
