 # AI-Powered Support Co-Pilot

## Sobre el Proyecto
Sistema de tickets con IA que recibe solicitudes de soporte, las procesa
mediante agentes de lenguaje para categorizarlas y analizar su sentimiento, y
las visualiza en tiempo real en un dashboard.

## Arquitectura
Frontend → Supabase → n8n → Python API

## URLs en Producción
- Dashboard: [Pendiente deploy]
- Python API: [Pendiente deploy]

## Tech Stack
- React
- Python
- FastAPI
- Supabase
- n8n

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
├── frontend
│   └── README.md
├── n8n
│   └── README.md
├── supabase
│   ├── README.md
│   └── setup.sql
└── README.md
```

