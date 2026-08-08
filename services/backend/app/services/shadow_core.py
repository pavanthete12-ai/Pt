from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ShadowAIError
from app.models.core import AgentRequest, ConversationMessage, CoreLog, CoreTask, TaskStatus
from app.schemas.core import CommandRequest, CommandResponse, TaskRead
from app.services.agent_requests import AgentRequestFactory
from app.services.intent import IntentAnalyzer
from app.services.response_pipeline import ResponsePipelineBuilder


class ShadowCoreService:
    def __init__(self) -> None:
        self.intent_analyzer = IntentAnalyzer()
        self.agent_factory = AgentRequestFactory()
        self.pipeline_builder = ResponsePipelineBuilder()

    async def receive_command(self, payload: CommandRequest, session: AsyncSession) -> CommandResponse:
        conversation_id = payload.conversation_id or f'conv_{uuid4().hex}'
        intent = self.intent_analyzer.analyze(payload.command)
        pipeline = self.pipeline_builder.build(intent)

        user_message = ConversationMessage(conversation_id=conversation_id, role='user', content=payload.command)
        task = CoreTask(conversation_id=conversation_id, command=payload.command, intent=intent.name, status=TaskStatus.planning)
        session.add_all([user_message, task])
        await session.flush()

        agent_request = AgentRequest(
            task_id=task.id,
            agent_type=self.agent_factory.build_agent_type(intent),
            instruction=self.agent_factory.build_instruction(payload.command, intent)
        )
        session.add(agent_request)
        await self._log(session, task.id, 'info', 'intent_detected', f'{intent.name} ({intent.confidence:.2f})')
        await self._log(session, task.id, 'info', 'agent_request_created', agent_request.agent_type)

        task.status = TaskStatus.awaiting_agent
        task.response = self._compose_response(task.id, intent.summary, agent_request.agent_type)
        assistant_message = ConversationMessage(conversation_id=conversation_id, role='assistant', content=task.response)
        session.add(assistant_message)
        await self._log(session, task.id, 'info', 'response_pipeline_generated', ' -> '.join(pipeline))
        await session.commit()

        hydrated_task = await self.get_task(task.id, session)
        return CommandResponse(task=TaskRead.model_validate(hydrated_task), response_pipeline=pipeline)

    async def get_task(self, task_id: str, session: AsyncSession) -> CoreTask:
        statement = (
            select(CoreTask)
            .where(CoreTask.id == task_id)
            .options(selectinload(CoreTask.agent_requests), selectinload(CoreTask.logs))
        )
        task = (await session.scalars(statement)).one_or_none()
        if task is None:
            raise ShadowAIError(f'Task {task_id} was not found.', status_code=404)
        return task

    async def _log(self, session: AsyncSession, task_id: str, level: str, event: str, message: str) -> None:
        session.add(CoreLog(task_id=task_id, level=level, event=event, message=message))

    def _compose_response(self, task_id: str, intent_summary: str, agent_type: str) -> str:
        return f'Task {task_id} accepted. {intent_summary} Generated request for {agent_type} and queued execution tracking.'
