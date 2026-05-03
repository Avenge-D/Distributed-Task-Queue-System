import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from pydantic import BaseModel

from database import engine, Base, get_db
from models import Task, TaskStatus
import queue_manager

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Distributed Task Queue API")

app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = os.getenv("API_KEY", "super_secret_key_123")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

class TaskCreate(BaseModel):
    task_name: str
    idempotency_key: str
    payload: Optional[Dict[str, Any]] = None
    max_retries: int = 3
    execute_at: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: str
    idempotency_key: str
    task_name: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    task_id = str(uuid.uuid4())
    
    # Create DB entry. The unique constraint on idempotency_key prevents duplicates.
    new_task = Task(
        id=task_id,
        idempotency_key=task_in.idempotency_key,
        task_name=task_in.task_name,
        payload=task_in.payload,
        max_retries=task_in.max_retries,
        execute_at=task_in.execute_at,
        status=TaskStatus.PENDING
    )
    
    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
    except IntegrityError:
        db.rollback()
        # Find the existing task to return it
        existing_task = db.query(Task).filter(Task.idempotency_key == task_in.idempotency_key).first()
        if existing_task:
            return existing_task
        raise HTTPException(status_code=400, detail="Idempotency key collision")

    # Enqueue to Redis
    queue_manager.enqueue_task(task_id=task_id, execute_at=task_in.execute_at)
    
    return new_task

@app.get("/tasks/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "id": task.id,
        "idempotency_key": task.idempotency_key,
        "task_name": task.task_name,
        "status": task.status,
        "result": task.result,
        "error_message": task.error_message,
        "retries": task.retries,
        "execute_at": task.execute_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }

@app.get("/dlq")
def list_dlq(api_key: str = Depends(get_api_key)):
    """
    Simply list the task IDs in the DLQ from Redis.
    In a real app, you might want pagination and joining with DB data.
    """
    dlq_items = queue_manager.redis_client.lrange(queue_manager.QUEUE_DLQ, 0, -1)
    return {"dlq_count": len(dlq_items), "tasks": dlq_items}

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """
    Serves the simple HTML dashboard for live task execution monitoring.
    """
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/stats", tags=["Dashboard"])
def get_stats(db: Session = Depends(get_db)):
    """
    Returns current queue statistics and recent tasks for the dashboard.
    """
    # DB stats
    status_counts = db.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    db_stats = {status.value: count for status, count in status_counts}
    
    # Recent tasks
    recent_tasks = db.query(Task).order_by(Task.updated_at.desc().nulls_last(), Task.created_at.desc()).limit(10).all()
    recent_tasks_list = [
        {
            "id": t.id,
            "task_name": t.task_name,
            "status": t.status.value,
            "retries": t.retries,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None
        } for t in recent_tasks
    ]

    # Redis stats
    redis_queues = queue_manager.get_queue_stats()

    return {
        "db_stats": db_stats,
        "redis_queues": redis_queues,
        "recent_tasks": recent_tasks_list
    }
