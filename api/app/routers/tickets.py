import logging
import os
import time
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models import TicketProcessRequest, TicketProcessResponse
from app.services.llm_service import (
    LLMService,
    LLMServiceError,
    MockLLMService,
)
from app.services.supabase_service import (
    SupabaseService,
    SupabaseServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tickets"])


def get_llm_service() -> Union[LLMService, MockLLMService]:
    """Dependencia para el servicio LLM. Con MOCK_LLM=true no se usa Hugging Face."""
    if os.getenv("MOCK_LLM", "").lower() == "true":
        return MockLLMService()
    try:
        return LLMService()
    except Exception as exc:
        logger.exception("LLM service init failed: %s", exc)
        raise


def get_supabase_service() -> SupabaseService:
    """Dependencia para el servicio de Supabase."""
    try:
        return SupabaseService()
    except Exception as exc:
        logger.exception("Supabase service init failed: %s", exc)
        raise


def _response(
    status_value: str,
    message: str,
    data: Optional[Dict[str, Any]],
    errors: Optional[list[str]],
) -> Dict[str, Any]:
    return {
        "status": status_value,
        "message": message,
        "data": data,
        "errors": errors,
    }


@router.post("/process-ticket")
def process_ticket(
    payload: Dict[str, Any] = Body(...),
    llm_service: Union[LLMService, MockLLMService] = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Procesa un ticket con IA, clasifica categoría/sentimiento y persiste en Supabase."""
    t0 = time.perf_counter()
    ticket_id_raw = payload.get("ticket_id", "unknown")

    try:
        request_data = TicketProcessRequest(**payload)
    except ValidationError as exc:
        logger.error("Validation failed for ticket %s: %s", ticket_id_raw, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_response(
                "error",
                "Entrada inválida.",
                data=None,
                errors=[str(e) for e in exc.errors()],
            ),
        )

    logger.info("Processing ticket: %s", request_data.ticket_id)

    t_llm = time.perf_counter()
    try:
        llm_result: TicketProcessResponse = llm_service.classify_ticket(
            request_data.description
        )
    except LLMServiceError as exc:
        logger.error("LLM error for ticket %s: %s", request_data.ticket_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_response(
                "error",
                "Error al clasificar el ticket con IA.",
                data=None,
                errors=[str(exc)],
            ),
        )
    llm_ms = int((time.perf_counter() - t_llm) * 1000)

    t_supabase = time.perf_counter()
    try:
        supabase_service.update_ticket_by_id(
            ticket_id=request_data.ticket_id,
            category=llm_result.category,
            sentiment=llm_result.sentiment,
            confidence_score=llm_result.confidence_score,
            reasoning=llm_result.reasoning,
            processing_time_ms=llm_ms,
        )
    except SupabaseServiceError as exc:
        logger.error("Supabase error for ticket %s: %s", request_data.ticket_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_response(
                "error",
                "Error al actualizar el ticket.",
                data=None,
                errors=[str(exc)],
            ),
        )
    except Exception as exc:
        logger.exception("Unexpected error updating ticket %s", request_data.ticket_id)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_response(
                "error",
                "Error al procesar el ticket.",
                data=None,
                errors=[str(exc)],
            ),
        )
    supabase_ms = (time.perf_counter() - t_supabase) * 1000
    total_ms = (time.perf_counter() - t0) * 1000

    logger.info(
        "Ticket %s processed: %s / %s (%.2fms total, LLM %.0fms, Supabase %.0fms)",
        request_data.ticket_id,
        llm_result.category,
        llm_result.sentiment,
        total_ms,
        llm_ms,
        supabase_ms,
    )
    return _response(
        "success",
        "Ticket procesado correctamente.",
        data=llm_result.model_dump(mode="json"),
        errors=None,
    )
