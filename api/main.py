import logging
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.tickets import router as tickets_router


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    load_dotenv()

    app = FastAPI(title="Support Copilot API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tickets_router)

    @app.get("/health")
    def health_check() -> Dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


logging.basicConfig(level=logging.INFO)
