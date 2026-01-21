from typing import Literal

from pydantic import BaseModel, Field, StrictFloat, StrictStr, UUID4


class TicketProcessRequest(BaseModel):
    """Solicitud para procesar un ticket con IA."""

    ticket_id: UUID4
    description: StrictStr = Field(..., min_length=10)


class TicketProcessResponse(BaseModel):
    """Respuesta estructurada del análisis de IA para un ticket."""

    category: Literal["Técnico", "Facturación", "Comercial", "Otro"]
    sentiment: Literal["Positivo", "Neutral", "Negativo"]
    confidence_score: StrictFloat = Field(..., ge=0, le=1)
    reasoning: StrictStr = Field(..., max_length=300)
