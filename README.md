 # AI-Powered Support Co-Pilot

## Sobre el Proyecto
Sistema de tickets con IA que recibe solicitudes de soporte, las procesa
mediante agentes de lenguaje para categorizarlas y analizar su sentimiento, y
las visualiza en tiempo real en un dashboard.

## Tech Stack
- Python 3.11
- FastAPI
- LangChain
- HuggingFace / Mock LLM
- Supabase
- Docker
- Render

## Endpoints
- POST /process-ticket
- GET /health

## Deployment
Deployed on Render using Docker.

## URL
- Python API: https://support-copilot-owbl.onrender.com/docs

## Estructura del Proyecto
```
.
├── api
│   ├── app
│   │   ├── routers
│   │   │   ├── __init__.py
│   │   │   └── tickets.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py
│   │   │   └── supabase_service.py
│   │   ├── __init__.py
│   │   └── models.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt

