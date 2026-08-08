from fastapi import APIRouter

router = APIRouter(prefix='/plugins', tags=['plugins'])

@router.get('')
async def list_plugins() -> dict[str, list[dict[str, str]]]:
    return {'plugins': []}
