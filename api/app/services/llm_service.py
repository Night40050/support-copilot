import json
import logging
import os
from typing import Optional

from langchain_community.llms import HuggingFaceHub
from langchain_core.prompts import PromptTemplate
from pydantic import ValidationError

from app.models import TicketCategory, SentimentType, TicketProcessResponse

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Error de servicio para procesamiento con LLM."""


class MockLLMService:
    """Mock del servicio LLM: devuelve clasificación fija sin llamar a Hugging Face.

    Se usa cuando MOCK_LLM=true para probar el flujo end-to-end sin IA.
    """

    def classify_ticket(self, ticket_text: str) -> TicketProcessResponse:
        """Devuelve una clasificación fija compatible con TicketProcessResponse."""
        return TicketProcessResponse(
            category=TicketCategory.TECNICO,
            sentiment=SentimentType.NEGATIVO,
            confidence_score=0.93,
            reasoning="Clasificación mock (MOCK_LLM=true). Sin llamada a IA.",
        )


class LLMService:
    """Servicio de clasificación de tickets usando Hugging Face LLM."""

    def __init__(
        self,
        repo_id: Optional[str] = None,
        huggingface_api_token: Optional[str] = None,
    ) -> None:
        token = huggingface_api_token or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not token:
            raise LLMServiceError(
                "Falta la variable HUGGINGFACEHUB_API_TOKEN en el entorno."
            )

        model_repo = (
            repo_id
            or os.getenv("HF_MODEL_ID")
            or "HuggingFaceH4/zephyr-7b-beta"
        )
        model_kwargs = {
            "temperature": 0.0,
            "max_new_tokens": 256,
            "do_sample": False,
        }

        self.mock = os.getenv("MOCK_LLM", "false").lower() == "true"

        self._llm = HuggingFaceHub(
            repo_id=model_repo,
            huggingfacehub_api_token=token,
            model_kwargs=model_kwargs,
        )
        self._prompt = PromptTemplate(
            input_variables=["ticket_text"],
            template=(
                "Clasifica el siguiente ticket de soporte y responde ÚNICAMENTE con un "
                "JSON válido, sin texto adicional antes ni después.\n\n"
                "Categorías (usa exactamente una): Técnico, Facturación, Comercial, Otro\n"
                "Sentimientos (usa exactamente uno): Positivo, Neutral, Negativo\n\n"
                "Esquema JSON requerido:\n"
                '{{"category": "<categoría>", "sentiment": "<sentimiento>", '
                '"confidence_score": <0.0-1.0>, "reasoning": "<explicación breve>"}}\n\n'
                "Ticket:\n{ticket_text}\n\n"
                "Responde solo con el JSON:"
            ),
        )

    def classify_ticket(self, ticket_text: str) -> TicketProcessResponse:
        """Clasifica un ticket y devuelve la salida estructurada.

        Args:
            ticket_text: Texto del ticket a clasificar.

        Returns:
            TicketProcessResponse con la clasificación.

        Raises:
            LLMServiceError: Si falla el procesamiento o la validación.
        """
        if not ticket_text or not ticket_text.strip():
            raise LLMServiceError("El texto del ticket no puede estar vacío.")

        prompt_text = self._prompt.format(ticket_text=ticket_text.strip())
        logger.info("Classifying ticket (%d chars)", len(ticket_text.strip()))

        try:
            raw_output = self._llm.invoke(prompt_text)
        except Exception as exc:
            logger.error("LLM invoke failed: %s", exc)
            raise LLMServiceError(
                "Error al procesar el ticket con el LLM."
            ) from exc

        cleaned = self._extract_json(raw_output)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("LLM returned invalid JSON: %s", exc)
            raise LLMServiceError(
                "El LLM no devolvió un JSON válido."
            ) from exc

        try:
            if hasattr(TicketProcessResponse, "model_validate"):
                result = TicketProcessResponse.model_validate(payload)
            else:
                result = TicketProcessResponse.parse_obj(payload)
        except ValidationError as exc:
            logger.error("LLM output validation failed: %s", exc.errors())
            raise LLMServiceError(
                "El JSON del LLM no cumple el esquema esperado."
            ) from exc

        logger.info(
            "Classified: %s / %s (confidence %.2f)",
            result.category,
            result.sentiment,
            result.confidence_score,
        )
        return result

    def _extract_json(self, text: str) -> str:
        """Extrae JSON del texto de salida del LLM."""
        if not text:
            return "{}"
        cleaned = text.strip()
        start_idx = cleaned.find("{")
        if start_idx == -1:
            return cleaned
        depth = 0
        for i in range(start_idx, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    return cleaned[start_idx : i + 1]
        return cleaned
