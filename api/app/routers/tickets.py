import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models import TicketProcessRequest, TicketProcessResponse
from app.services.llm_service import LLMService
from app.services.supabase_service import (
    SupabaseService,
    SupabaseServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tickets"])


def get_llm_service() -> LLMService:
    """Dependencia para el servicio LLM."""
    return LLMService()


def get_supabase_service() -> SupabaseService:
    """Dependencia para el servicio de Supabase."""
    return SupabaseService()


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
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Procesa un ticket con IA y persiste resultados en Supabase."""
    try:
        request_data = TicketProcessRequest(**payload)
    except ValidationError as exc:
        logger.info("Entrada inválida para process-ticket: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_response(
                "error",
                "Entrada inválida.",
                data=None,
                errors=[str(exc)],
            ),
        )

    start_time = time.perf_counter()

    try:
        llm_result: TicketProcessResponse = llm_service.classify_ticket(
            request_data.description
        )
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        supabase_service.update_ticket_by_id(
            ticket_id=request_data.ticket_id,
            category=llm_result.category,
            sentiment=llm_result.sentiment,
            confidence_score=llm_result.confidence_score,
            reasoning=llm_result.reasoning,
            processing_time_ms=processing_time_ms,
        )
    except SupabaseServiceError as exc:
        logger.exception("Error al actualizar ticket en Supabase.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_response(
                "error",
                "Error al actualizar el ticket.",
                data=None,
                errors=[str(exc)],
            ),
        )
    except Exception as exc:  # pragma: no cover - error inesperado
        logger.exception("Error al procesar el ticket.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_response(
                "error",
                "Error al procesar el ticket.",
                data=None,
                errors=[str(exc)],
            ),
        )

    return _response(
        "success",
        "Ticket procesado correctamente.",
        data=llm_result.dict(),
        errors=None,
    )
