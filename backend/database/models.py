from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class UserModel(Base):
    """User database model"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # "admin" or "user"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    last_login = Column(DateTime, nullable=True)

    # Usage tracking
    usage_quota = Column(Integer, default=100000)  # tokens per day
    usage_today = Column(Integer, default=0)
    total_usage = Column(Integer, default=0)
    usage_reset_date = Column(DateTime, default=utc_now)

    # Relationships
    api_keys = relationship("APIKeyModel", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLogModel", back_populates="user", cascade="all, delete-orphan")


class APIKeyModel(Base):
    """API Key database model"""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    hashed_key = Column(String(255), nullable=False)
    prefix = Column(String(11), nullable=False)  # "sk-" + 8 chars
    created_at = Column(DateTime, default=utc_now)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("UserModel", back_populates="api_keys")


class UsageLogModel(Base):
    """Usage log for tracking API usage"""
    __tablename__ = "usage_logs"
    __table_args__ = (
        Index('ix_usage_logs_timestamp', 'timestamp'),
        Index('ix_usage_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_usage_logs_provider', 'provider'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now)
    endpoint = Column(String(255))
    method = Column(String(10))
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    provider = Column(String(50))  # openai, anthropic, etc.
    model = Column(String(100))
    request_type = Column(String(50))  # chat, vision, embedding, etc.
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="usage_logs")


class WorkflowExecutionModel(Base):
    """Workflow execution history"""
    __tablename__ = "workflow_executions"
    __table_args__ = (
        Index('ix_workflow_executions_status', 'status'),
        Index('ix_workflow_executions_user_started', 'user_id', 'started_at'),
        Index('ix_workflow_executions_workflow_id', 'workflow_id'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=False)
    workflow_name = Column(String(255))
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")  # running, completed, failed
    steps_completed = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)  # JSON string


class AgentActivityModel(Base):
    """Agent activity log for dashboard"""
    __tablename__ = "agent_activities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=utc_now)
    agent_type = Column(String(50))  # orchestrator, researcher, coder, etc.
    action = Column(String(100))  # thinking, tool_call, response, etc.
    tool_name = Column(String(50), nullable=True)
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    details = Column(Text, nullable=True)  # JSON string


class ScheduledTaskModel(Base):
    """Persistent storage for scheduled workflow tasks"""
    __tablename__ = "scheduled_tasks"
    __table_args__ = (
        Index('ix_scheduled_tasks_enabled', 'enabled'),
        Index('ix_scheduled_tasks_workflow_id', 'workflow_id'),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    trigger_type = Column(String(20), nullable=False)  # cron, interval, date
    trigger_config = Column(Text, nullable=False)  # JSON string
    variables = Column(Text, nullable=True)  # JSON string
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
