import logging
import os
import time
from typing import Callable, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers.tickets import router as tickets_router

load_dotenv()

log_level = (
    logging.INFO
    if os.getenv("ENVIRONMENT") == "development"
    else logging.WARNING
)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        logger.info("%s %s", request.method, request.url.path)

        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                "%s %s - %d (%.2fms)",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )

            return response
        except Exception as exc:
            logger.error(
                "%s %s - Error: %s",
                request.method,
                request.url.path,
                str(exc),
            )
            raise


app = FastAPI(
    title="Support Copilot API",
    version="1.0.0",
    debug=os.getenv("ENVIRONMENT") == "development",
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tickets_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Maneja errores de validación de Pydantic."""
    logger.error("Validation error %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Error de validación en los datos de entrada.",
            "data": None,
            "errors": [str(e) for e in exc.errors()],
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Maneja errores no capturados."""
    logger.exception("Unhandled error in %s", request.url.path)

    error_detail = (
        str(exc)
        if os.getenv("ENVIRONMENT") == "development"
        else "Internal server error"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Error processing request",
            "errors": [error_detail],
        },
    )


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check para carga balancers y monitoreo."""
    return {"status": "ok"}
