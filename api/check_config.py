#!/usr/bin/env python3
"""Script de diagnóstico para verificar la configuración de la API.

Ejecuta este script para verificar que todas las variables de entorno
están configuradas correctamente antes de probar con Postman.
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=" * 80)
print("DIAGNÓSTICO DE CONFIGURACIÓN - Support Copilot API")
print("=" * 80)
print()

# Verificar variables de entorno
errors = []
warnings = []

# Variables requeridas para Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("1. VARIABLES DE SUPABASE")
print("-" * 40)
if not supabase_url:
    errors.append("❌ SUPABASE_URL no está definida")
    print("   ❌ SUPABASE_URL: NO DEFINIDA")
else:
    print(f"   ✅ SUPABASE_URL: {supabase_url}")

if not supabase_key:
    errors.append("❌ SUPABASE_SERVICE_ROLE_KEY no está definida")
    print("   ❌ SUPABASE_SERVICE_ROLE_KEY: NO DEFINIDA")
else:
    print(f"   ✅ SUPABASE_SERVICE_ROLE_KEY: {'*' * 20} (definida)")

print()

# Variables para LLM
mock_llm = os.getenv("MOCK_LLM", "").lower() == "true"
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
hf_model = os.getenv("HF_MODEL_ID")

print("2. VARIABLES DE LLM")
print("-" * 40)
print(f"   MOCK_LLM: {mock_llm}")
if mock_llm:
    print("   ✅ Modo MOCK activado - no se requiere Hugging Face")
else:
    if not hf_token:
        errors.append("❌ HUGGINGFACEHUB_API_TOKEN no está definida (requerida si MOCK_LLM=false)")
        print("   ❌ HUGGINGFACEHUB_API_TOKEN: NO DEFINIDA")
    else:
        print(f"   ✅ HUGGINGFACEHUB_API_TOKEN: {'*' * 20} (definida)")
    
    if hf_model:
        print(f"   ✅ HF_MODEL_ID: {hf_model}")
    else:
        print("   ℹ️  HF_MODEL_ID: no definida (usará default: HuggingFaceH4/zephyr-7b-beta)")

print()

# Variable de entorno
environment = os.getenv("ENVIRONMENT", "development")
print("3. CONFIGURACIÓN GENERAL")
print("-" * 40)
print(f"   ENVIRONMENT: {environment}")
if environment == "development":
    print("   ✅ Modo desarrollo - logging en nivel DEBUG")
else:
    print("   ℹ️  Modo producción - logging en nivel INFO")

print()

# Intentar importar servicios
print("4. VERIFICACIÓN DE SERVICIOS")
print("-" * 40)

try:
    from app.services.supabase_service import SupabaseService
    print("   ✅ SupabaseService: importado correctamente")
    
    if supabase_url and supabase_key:
        try:
            service = SupabaseService()
            print("   ✅ SupabaseService: inicializado correctamente")
        except Exception as exc:
            errors.append(f"❌ Error al inicializar SupabaseService: {exc}")
            print(f"   ❌ SupabaseService: Error al inicializar - {exc}")
    else:
        warnings.append("⚠️  No se puede inicializar SupabaseService (faltan variables)")
        print("   ⚠️  SupabaseService: No se puede inicializar (faltan variables)")
except ImportError as exc:
    errors.append(f"❌ Error al importar SupabaseService: {exc}")
    print(f"   ❌ SupabaseService: Error al importar - {exc}")

print()

try:
    from app.services.llm_service import LLMService, MockLLMService
    print("   ✅ LLMService: importado correctamente")
    
    if mock_llm:
        try:
            service = MockLLMService()
            print("   ✅ MockLLMService: inicializado correctamente")
        except Exception as exc:
            errors.append(f"❌ Error al inicializar MockLLMService: {exc}")
            print(f"   ❌ MockLLMService: Error al inicializar - {exc}")
    else:
        if hf_token:
            try:
                service = LLMService()
                print("   ✅ LLMService: inicializado correctamente")
            except Exception as exc:
                errors.append(f"❌ Error al inicializar LLMService: {exc}")
                print(f"   ❌ LLMService: Error al inicializar - {exc}")
        else:
            warnings.append("⚠️  No se puede inicializar LLMService (falta HUGGINGFACEHUB_API_TOKEN)")
            print("   ⚠️  LLMService: No se puede inicializar (falta token)")
except ImportError as exc:
    errors.append(f"❌ Error al importar LLMService: {exc}")
    print(f"   ❌ LLMService: Error al importar - {exc}")

print()
print("=" * 80)
print("RESUMEN")
print("=" * 80)

if errors:
    print("❌ ERRORES ENCONTRADOS:")
    for error in errors:
        print(f"   {error}")
    print()
    print("⚠️  La API NO funcionará correctamente hasta resolver estos errores.")
    sys.exit(1)
elif warnings:
    print("⚠️  ADVERTENCIAS:")
    for warning in warnings:
        print(f"   {warning}")
    print()
    print("✅ La API debería funcionar, pero revisa las advertencias.")
    sys.exit(0)
else:
    print("✅ TODO CORRECTO")
    print()
    print("La API está configurada correctamente. Puedes probar con Postman.")
    sys.exit(0)
