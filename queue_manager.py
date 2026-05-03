import os
import json
import redis
from datetime import datetime, timezone

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

QUEUE_READY = "queue:ready"
QUEUE_SCHEDULED = "queue:scheduled"
QUEUE_DLQ = "queue:dlq"

def enqueue_task(task_id: str, execute_at: datetime = None):
    """
    Enqueues a task to either the ready list or the scheduled sorted set.
    """
    if execute_at:
        # Ensure timezone awareness for comparison
        if execute_at.tzinfo is None:
            execute_at = execute_at.replace(tzinfo=timezone.utc)
            
        if execute_at > datetime.now(timezone.utc):
            # Schedule for later
            score = execute_at.timestamp()
            redis_client.zadd(QUEUE_SCHEDULED, {task_id: score})
            return

    # Ready to run immediately
    redis_client.rpush(QUEUE_READY, task_id)

def dequeue_task(timeout: int = 0):
    """
    Blocks until a task is available in the ready queue.
    """
    result = redis_client.blpop(QUEUE_READY, timeout=timeout)
    if result:
        return result[1] # Returns a tuple (queue_name, task_id)
    return None

def move_to_dlq(task_id: str):
    """
    Moves a failed task to the Dead Letter Queue.
    """
    redis_client.rpush(QUEUE_DLQ, task_id)

def get_queue_stats():
    """
    Returns the current sizes of the Redis queues.
    """
    return {
        "ready": redis_client.llen(QUEUE_READY),
        "scheduled": redis_client.zcard(QUEUE_SCHEDULED),
        "dlq": redis_client.llen(QUEUE_DLQ)
    }

PROMOTE_LUA_SCRIPT = """
local due_tasks = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
if #due_tasks > 0 then
    redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
    for i=1, #due_tasks do
        redis.call('RPUSH', KEYS[2], due_tasks[i])
    end
end
return #due_tasks
"""

# Register script to be executed
promote_script = redis_client.register_script(PROMOTE_LUA_SCRIPT)

def promote_due_scheduled_tasks():
    """
    Finds tasks in the scheduled queue that are due and moves them to the ready queue.
    Uses a Lua script for atomic execution.
    """
    now = datetime.now(timezone.utc).timestamp()
    count = promote_script(keys=[QUEUE_SCHEDULED, QUEUE_READY], args=[now])
    return count
