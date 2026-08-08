from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class ShadowAIError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ShadowAIError)
    async def shadow_error_handler(_: Request, exc: ShadowAIError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={'error': exc.message})
