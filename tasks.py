"""
Task Definitions and Registry.

This module contains the actual Python functions that represent tasks.
Any new task must be defined here and registered in the `TASK_REGISTRY`.
"""

import time
import random

def dummy_task(payload: dict):
    """
    A dummy task that simulates work by sleeping.
    It randomly fails to demonstrate retries and DLQ.
    """
    print(f"Executing dummy_task with payload: {payload}")
    time.sleep(2)  # Simulate some work
    
    should_fail = payload.get("should_fail", False)
    if should_fail:
        # Simulate a random failure if requested
        if random.random() < 0.7:  # 70% chance of failure
            raise Exception("Simulated random failure in dummy_task")
            
    return {"message": "Task completed successfully", "processed_data": payload.get("data", "")}

# A registry of available tasks
TASK_REGISTRY = {
    "dummy_task": dummy_task
}
