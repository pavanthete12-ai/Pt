from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.core import CommandRequest, CommandResponse, TaskRead
from app.services.shadow_core import ShadowCoreService

router = APIRouter(prefix='/core', tags=['shadow-core'])
shadow_core = ShadowCoreService()


@router.post('/commands', response_model=CommandResponse, status_code=202)
async def receive_command(payload: CommandRequest, session: AsyncSession = Depends(get_session)) -> CommandResponse:
    return await shadow_core.receive_command(payload, session)


@router.get('/tasks/{task_id}', response_model=TaskRead)
async def get_task(task_id: str, session: AsyncSession = Depends(get_session)) -> TaskRead:
    task = await shadow_core.get_task(task_id, session)
    return TaskRead.model_validate(task)
