# Guía: `.env` y credenciales de Supabase

Esta guía explica cómo crear el archivo `.env` con las credenciales necesarias para el **Support Co-Pilot** (Supabase y Hugging Face).

---

## 1. Dónde crear el `.env`

Crea el archivo **`api/.env`** (dentro de la carpeta `api`). La aplicación carga variables con `python-dotenv` desde el directorio de trabajo; si ejecutas la API desde `api/`, debe estar ahí.

```
support-copilot/
├── api/
│   ├── .env          ← aquí
│   ├── main.py
│   └── ...
```

---

## 2. Variables necesarias

### Supabase (obligatorias para la API)

| Variable | Uso | Dónde obtenerla |
|----------|-----|------------------|
| `SUPABASE_URL` | URL del proyecto | Dashboard → **Project Settings** → **API** → **Project URL** |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave privada para backend | Misma sección → **Project API keys** → **`service_role`** (secret) |

### Hugging Face (obligatoria para clasificación de tickets)

| Variable | Uso | Dónde obtenerla |
|----------|-----|------------------|
| `HUGGINGFACEHUB_API_TOKEN` | LLM (Hugging Face) para clasificar categoría y sentimiento | [Hugging Face Tokens](https://huggingface.co/settings/tokens) |

### Opcional

| Variable | Uso |
|----------|-----|
| `SUPABASE_ANON_KEY` | Frontend o n8n; la API Python no la usa. |
| `HF_MODEL_ID` | Modelo Hugging Face a usar. Por defecto: `microsoft/phi-2`. Ej.: `google/flan-t5-xxl`. |
| `MOCK_LLM` | Si es `true`, se usa un mock del LLM (sin Hugging Face). Sirve para probar el flujo end-to-end sin IA. |

---

## 3. Cómo obtener las credenciales de Supabase

1. Entra en [supabase.com](https://supabase.com) e inicia sesión.
2. Abre tu **proyecto** (o crea uno nuevo).
3. Ve a **Project Settings** (icono de engranaje en el menú lateral).
4. En el menú izquierdo, **API**.
5. Ahí encontrarás:
   - **Project URL** → valor de `SUPABASE_URL`.
   - **Project API keys**:
     - **`anon` `public`** → `SUPABASE_ANON_KEY` (si la usas en frontend/n8n).
     - **`service_role` `secret`** → `SUPABASE_SERVICE_ROLE_KEY`.  
       **Importante:** no la expongas en frontend ni en repositorios. Solo en backend.

---

## 4. Plantilla del archivo `api/.env`

Copia este contenido en `api/.env` y sustituye los valores por los tuyos:

```env
# Supabase
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Hugging Face (clasificación de tickets)
HUGGINGFACEHUB_API_TOKEN=hf_...
# HF_MODEL_ID=microsoft/phi-2   # opcional; por defecto phi-2
# MOCK_LLM=true                 # opcional; mock sin IA para probar flujo
```

- **SUPABASE_URL**: la URL completa de tu proyecto (p. ej. `https://abcdefgh.supabase.co`).
- **SUPABASE_SERVICE_ROLE_KEY** y **SUPABASE_ANON_KEY**: los JWT completos que te muestra Supabase.
- **HUGGINGFACEHUB_API_TOKEN**: token de Hugging Face (p. ej. `hf_...`). **HF_MODEL_ID**: modelo a usar; por defecto `microsoft/phi-2`.

---

## 5. Comprobar que funciona

1. Asegúrate de tener la base de datos configurada (`supabase/setup.sql`).
2. Con el `.env` en `api/`, desde `api/` ejecuta:

   ```bash
   uv run uvicorn main:app --reload
   ```

3. Prueba el health check:

   ```bash
   curl http://127.0.0.1:8000/health
   ```

4. Si faltan `SUPABASE_URL` o `SUPABASE_SERVICE_ROLE_KEY`, la API lanzará un error al usar el servicio de Supabase. Si falta `HUGGINGFACEHUB_API_TOKEN`, fallará al clasificar tickets.

### Probar sin Hugging Face (`MOCK_LLM=true`)

Para aislar fallos de Hugging Face y probar el flujo end-to-end sin IA:

1. En `api/.env` añade `MOCK_LLM=true`.
2. **No hace falta** `HUGGINGFACEHUB_API_TOKEN`; no se llama a Hugging Face.
3. Siguen siendo obligatorias `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` (el resultado se persiste en Supabase).
4. Levanta la API y llama a `POST /process-ticket`. La clasificación será siempre mock (p. ej. Técnico / Negativo).

---

## 6. Referencia rápida del uso en el código

- **`SupabaseService`** (`app/services/supabase_service.py`): usa `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` para actualizar la tabla `tickets`.
- **`LLMService`** (`app/services/llm_service.py`): usa `HUGGINGFACEHUB_API_TOKEN` y opcionalmente `HF_MODEL_ID` (vía LangChain/HuggingFaceHub) para clasificar categoría y sentimiento. Con `MOCK_LLM=true` se usa `MockLLMService` y no se llama a Hugging Face.

`.env` y `.env.local` están en `.gitignore`; no los subas al repositorio.
