"""Schemas Pydantic para validación de datos."""

from pydantic import BaseModel, Field, StrictFloat, StrictStr, UUID4

from app.models.enums import SentimentType, TicketCategory


class TicketProcessRequest(BaseModel):
    """Solicitud para procesar un ticket con IA."""

    ticket_id: UUID4
    description: StrictStr = Field(..., min_length=10)


class TicketProcessResponse(BaseModel):
    """Respuesta estructurada del análisis de IA para un ticket."""

    category: TicketCategory
    sentiment: SentimentType
    confidence_score: StrictFloat = Field(..., ge=0, le=1)
    reasoning: StrictStr = Field(..., max_length=300)
