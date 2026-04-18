#!/usr/bin/env python3
"""
Script de validación de configuración del Router v1 + Gemini.
Ejecuta: python validate_setup.py
"""

import os
import sys
from pathlib import Path

print("\n" + "="*60)
print("VALIDACIÓN DE SETUP: PWR Router v1 + Gemini 2.5")
print("="*60 + "\n")

# 1. Verificar estructura de archivos
print("1. Verificando estructura de archivos...")
required_files = [
    "router/domain.py",
    "router/mode_registry.py",
    "router/providers.py",
    "router/execution_service.py",
    "router/decision_engine.py",
    "router/metadata_builder.py",
    "app.py",
    ".env.example",
]

all_exist = True
for file in required_files:
    if Path(file).exists():
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} FALTA")
        all_exist = False

if not all_exist:
    print("\n❌ Algunos archivos no existen. Verifica la instalación.")
    sys.exit(1)

print("   ✅ Todos los archivos presentes\n")

# 2. Verificar variable de entorno
print("2. Verificando GEMINI_API_KEY...")
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    masked = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    print(f"   ✅ GEMINI_API_KEY configurada: {masked}")
else:
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            if "GEMINI_API_KEY=" in content:
                print("   ⚠️  GEMINI_API_KEY está en .env pero no exportada")
                print("   → Ejecuta: export GEMINI_API_KEY=\"tu-clave-aquí\"")
            else:
                print("   ❌ GEMINI_API_KEY no configurada en .env")
    else:
        print("   ❌ .env no existe")
        print("   → Ejecuta: cp .env.example .env")
        print("   → Edita .env y pega tu API key")

print()

# 3. Verificar dependencias Python
print("3. Verificando dependencias Python...")
dependencies = {
    "google": "google-genai",
    "streamlit": "streamlit",
    "dotenv": "python-dotenv",
}

missing = []
for import_name, package_name in dependencies.items():
    try:
        if import_name == "google":
            from google import genai
        elif import_name == "dotenv":
            from dotenv import load_dotenv
        else:
            __import__(import_name)
        print(f"   ✅ {package_name}")
    except ImportError:
        print(f"   ❌ {package_name} NO INSTALADO")
        missing.append(package_name)

if missing:
    print(f"\n   → Instala faltantes: pip install {' '.join(missing)}")

print()

# 4. Verificar importabilidad del router
print("4. Verificando importabilidad del Router...")
try:
    from router import ExecutionService, TaskInput
    print("   ✅ Router importable")
except ImportError as e:
    print(f"   ❌ Error importando router: {e}")
    sys.exit(1)

print()

# 5. Verificar GeminiProvider
print("5. Verificando GeminiProvider...")
try:
    from router.providers import GeminiProvider
    print("   ✅ GeminiProvider importable")

    # Intentar inicializar (falla si no hay API key, pero eso es esperado)
    try:
        provider = GeminiProvider()
        print("   ✅ GeminiProvider inicializado (API key válida)")
    except ValueError as e:
        if "GEMINI_API_KEY no configurada" in str(e):
            print("   ⚠️  GeminiProvider necesita GEMINI_API_KEY configurada")
        else:
            print(f"   ⚠️  GeminiProvider: {e}")
except ImportError as e:
    print(f"   ❌ Error importando GeminiProvider: {e}")

print()

# 6. Resumen
print("="*60)
print("RESUMEN DE VALIDACIÓN")
print("="*60)
print("""
✅ Si ves este mensaje, la estructura está bien.
⚠️  Si falta GEMINI_API_KEY, configúrala antes de usar.
❌ Si ves errores, revisa SETUP_GEMINI.md

PRÓXIMOS PASOS:
1. cp .env.example .env
2. Edita .env y pega tu API key desde https://aistudio.google.com/app/apikey
3. pip install google-genai python-dotenv
4. streamlit run app.py

DOCUMENTACIÓN:
- SETUP_GEMINI.md: Configuración detallada
- router/: Código del Router
- app.py: Aplicación Streamlit
""")

print()
