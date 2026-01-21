import logging
import os
from typing import Optional
from uuid import UUID

from supabase import Client, create_client

from app.models import SentimentType, TicketCategory

logger = logging.getLogger(__name__)


class SupabaseServiceError(Exception):
    """Error de servicio para operaciones con Supabase."""


class SupabaseService:
    """Servicio de acceso a datos en Supabase (solo updates)."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
    ) -> None:
        """Inicializa el cliente de Supabase.

        Args:
            supabase_url: URL de Supabase.
            service_role_key: Service role key de Supabase.
        """
        url = supabase_url or os.getenv("SUPABASE_URL")
        key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            raise SupabaseServiceError(
                "Faltan variables SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY."
            )

        self._client: Client = create_client(url, key)

    def update_ticket_by_id(
        self,
        ticket_id: UUID,
        category: TicketCategory,
        sentiment: SentimentType,
        confidence_score: float,
        reasoning: str,
        processing_time_ms: int,
    ) -> None:
        """Actualiza un ticket con resultados de clasificación.

        Args:
            ticket_id: ID del ticket.
            category: Categoría clasificada.
            sentiment: Sentimiento clasificado.
            confidence_score: Score entre 0 y 1.
            reasoning: Razón corta de la clasificación.
            processing_time_ms: Tiempo de procesamiento en ms.

        Raises:
            SupabaseServiceError: Si falla la operación.
        """
        payload = {
            "category": category.value,
            "sentiment": sentiment.value,
            "confidence_score": confidence_score,
            "reasoning": reasoning,
            "processed": True,
            "processing_time_ms": processing_time_ms,
        }

        try:
            result = (
                self._client.table("tickets")
                .update(payload)
                .eq("id", str(ticket_id))
                .execute()
            )
        except Exception as exc:  # pragma: no cover - error externo
            logger.exception("Error al actualizar ticket en Supabase.")
            raise SupabaseServiceError(
                "Error al actualizar ticket en Supabase."
            ) from exc

        error = getattr(result, "error", None)
        if error:
            logger.error("Supabase error al actualizar ticket: %s", error)
            raise SupabaseServiceError(
                "Supabase devolvió un error al actualizar el ticket."
            )

        data = getattr(result, "data", None) or []
        if not data:
            logger.warning(
                "No se encontró el ticket para actualizar: %s",
                ticket_id,
            )
            raise SupabaseServiceError(
                "No se encontró el ticket para actualizar."
            )
