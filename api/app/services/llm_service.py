import json

from pydantic import ValidationError

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.models import TicketProcessResponse


class LLMServiceError(Exception):
    """Error de servicio para procesamiento con LLM."""


class LLMService:
    """Servicio de clasificación de tickets usando un LLM."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ) -> None:
        """Inicializa el cliente del modelo y el prompt."""
        # Estrategia de prompt:
        # - Instrucciones estrictas y explícitas de formato JSON.
        # - Lista cerrada de categorías/sentimientos para evitar alucinaciones.
        # - Fallback conservador cuando no hay evidencia suficiente.
        # - Mantener el contexto mínimo reduce desviaciones del formato.
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Eres un clasificador de tickets de soporte. "
                        "Devuelve SOLO un JSON válido con las claves: "
                        "category, sentiment, confidence_score, reasoning. "
                        "No incluyas markdown ni texto adicional. "
                        "Usa únicamente estas categorías: "
                        "Técnico, Facturación, Comercial, Otro. "
                        "Usa únicamente estos sentimientos: "
                        "Positivo, Neutral, Negativo. "
                        "Si la evidencia es insuficiente, usa "
                        "category='Otro', sentiment='Neutral' y una "
                        "confidence_score <= 0.5."
                    ),
                ),
                (
                    "human",
                    (
                        "Ticket:\n{ticket_text}"
                    ),
                ),
            ]
        )

        self._llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        self._chain = self._prompt | self._llm

    def classify_ticket(self, ticket_text: str) -> TicketProcessResponse:
        """Clasifica un ticket y devuelve la salida estructurada."""
        if not ticket_text or not ticket_text.strip():
            raise ValueError("El texto del ticket no puede estar vacío.")

        result = self._chain.invoke(
            {
                "ticket_text": ticket_text.strip(),
            }
        )

        try:
            payload = json.loads(result.content)
        except json.JSONDecodeError as exc:
            raise LLMServiceError(
                "El LLM no devolvió un JSON válido."
            ) from exc

        try:
            if hasattr(TicketProcessResponse, "model_validate"):
                return TicketProcessResponse.model_validate(payload)
            return TicketProcessResponse.parse_obj(payload)
        except ValidationError as exc:
            raise LLMServiceError(
                "El JSON del LLM no cumple el esquema esperado."
            ) from exc
