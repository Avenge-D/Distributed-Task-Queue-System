from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DLQ = "DLQ"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    task_name = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    execute_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
