from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex}'


class TaskStatus(StrEnum):
    queued = 'queued'
    planning = 'planning'
    awaiting_agent = 'awaiting_agent'
    completed = 'completed'
    failed = 'failed'


class ConversationMessage(Base):
    __tablename__ = 'conversation_messages'

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id('msg'))
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CoreTask(Base):
    __tablename__ = 'core_tasks'

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id('task'))
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    command: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.queued, index=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agent_requests: Mapped[list['AgentRequest']] = relationship(back_populates='task', cascade='all, delete-orphan')
    logs: Mapped[list['CoreLog']] = relationship(back_populates='task', cascade='all, delete-orphan')


class AgentRequest(Base):
    __tablename__ = 'agent_requests'

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id('agent_req'))
    task_id: Mapped[str] = mapped_column(ForeignKey('core_tasks.id'), index=True)
    agent_type: Mapped[str] = mapped_column(String(128), index=True)
    instruction: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default='pending', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[CoreTask] = relationship(back_populates='agent_requests')


class CoreLog(Base):
    __tablename__ = 'core_logs'

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id('log'))
    task_id: Mapped[str] = mapped_column(ForeignKey('core_tasks.id'), index=True)
    level: Mapped[str] = mapped_column(String(16), default='info')
    event: Mapped[str] = mapped_column(String(128), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[CoreTask] = relationship(back_populates='logs')
