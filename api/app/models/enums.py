"""Enums reutilizables para el sistema de tickets.

Compatible con FastAPI (Pydantic), Supabase e IA.
"""

from enum import Enum


class TicketCategory(str, Enum):
    """Categorías de tickets soportadas."""

    TECNICO = "Técnico"
    FACTURACION = "Facturación"
    COMERCIAL = "Comercial"
    OTRO = "Otro"


class SentimentType(str, Enum):
    """Tipos de sentimiento en tickets."""

    POSITIVO = "Positivo"
    NEUTRAL = "Neutral"
    NEGATIVO = "Negativo"
