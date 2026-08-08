from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.core import TaskStatus


class CommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, max_length=64)
    user_id: str | None = Field(default=None, max_length=128)


class AgentRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_type: str
    instruction: str
    status: str
    created_at: datetime


class TaskLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    level: str
    event: str
    message: str
    created_at: datetime


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    command: str
    intent: str
    status: TaskStatus
    response: str | None
    created_at: datetime
    updated_at: datetime
    agent_requests: list[AgentRequestRead] = []
    logs: list[TaskLogRead] = []


class CommandResponse(BaseModel):
    task: TaskRead
    response_pipeline: list[str]
