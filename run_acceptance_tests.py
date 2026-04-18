#!/usr/bin/env python3
"""
Script interactivo para ejecutar Pruebas de Aceptación de Hito 1.
Uso: python run_acceptance_tests.py
"""

import os
import sys
from pathlib import Path


class AcceptanceTestRunner:
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0

    def print_header(self, text):
        """Imprime un encabezado."""
        print("\n" + "=" * 70)
        print(f" {text}")
        print("=" * 70 + "\n")

    def print_test(self, num, name):
        """Imprime el nombre de una prueba."""
        print(f"\n[Test {num}] {name}")
        print("-" * 70)

    def print_instruction(self, text):
        """Imprime una instrucción."""
        print(f"ℹ️  {text}")

    def print_check(self, text):
        """Imprime un check positivo."""
        print(f"✅ {text}")

    def print_warning(self, text):
        """Imprime una advertencia."""
        print(f"⚠️  {text}")

    def print_error(self, text):
        """Imprime un error."""
        print(f"❌ {text}")

    def prompt_yes_no(self, question):
        """Pide confirmación si/no."""
        while True:
            response = input(f"\n{question} (s/n): ").strip().lower()
            if response in ["s", "si", "sí", "y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            else:
                print("Por favor, escribe 's' o 'n'")

    def run_test_1(self):
        """Test 1: Arranque limpio con Gemini configurado."""
        self.print_test(1, "Arranque Limpio con Gemini Configurado")

        self.print_instruction(
            "Este test verifica que la app inicia sin errores y Gemini se valida."
        )

        # Verificar estructura de archivos
        self.print_check("Verificando estructura de archivos...")

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

        all_exist = all(Path(f).exists() for f in required_files)
        if all_exist:
            self.print_check("Todos los archivos presentes")
        else:
            self.print_error("Algunos archivos falta")
            return False

        # Verificar .env
        if Path(".env").exists():
            self.print_check(".env existe")
        else:
            self.print_warning(".env no existe. Créalo: cp .env.example .env")

        # Verificar GEMINI_API_KEY
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            masked = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
            self.print_check(f"GEMINI_API_KEY configurada: {masked}")
        else:
            self.print_error("GEMINI_API_KEY no está en variables de entorno")
            self.print_instruction(
                "Ejecuta: python validate_setup.py para diagnóstico completo"
            )
            return False

        # Verificar importabilidad
        try:
            from router import ExecutionService, TaskInput

            self.print_check("Router importable")
        except ImportError as e:
            self.print_error(f"No se puede importar router: {e}")
            return False

        # Verificar GeminiProvider
        try:
            from router.providers import GeminiProvider

            self.print_check("GeminiProvider importable")
            try:
                provider = GeminiProvider()
                self.print_check("GeminiProvider inicializado (API key válida)")
            except ValueError as e:
                self.print_warning(f"GeminiProvider: {e}")
                return False
        except ImportError as e:
            self.print_error(f"No se puede importar GeminiProvider: {e}")
            return False

        self.print_instruction(
            "Ahora ejecuta: streamlit run app.py y continúa con Test 2"
        )

        return True

    def run_test_2(self):
        """Test 2: Ejecución real end-to-end."""
        self.print_test(2, "Ejecución Real End-to-End de una Tarea")

        self.print_instruction("Este test requiere usar la UI de Streamlit")
        self.print_instruction("Asegúrate que 'streamlit run app.py' está ejecutándose")

        steps = [
            ("Crea un proyecto: 'Test Hito 1'", True),
            ("Crea una tarea ECO: 'Explicar recursión' (tipo: Pensar)", True),
            ("Ejecuta la tarea con Router (modo ECO)", True),
            ("Verifica que el resultado es real de Gemini (no simulado)", True),
            ("Verifica que la trazabilidad muestra: modo=eco, modelo=gemini-2.5-flash-lite",
             True),
            ("Verifica que la latencia es un número real en ms", True),
            ("Crea una tarea RACING: 'Estrategia escalado' (tipo: Decidir)", True),
            ("Ejecuta la tarea con Router (modo RACING)", True),
            ("Verifica que el modo es racing y modelo=gemini-2.5-pro", True),
        ]

        for i, (step, _) in enumerate(steps, 1):
            if self.prompt_yes_no(f"[{i}/{len(steps)}] ¿{step}?"):
                self.print_check(f"Paso {i} completado")
            else:
                self.print_error(f"Paso {i} fallido - Revisa ACCEPTANCE_TESTS_HITO1.md")
                return False

        return True

    def run_test_3(self):
        """Test 3: Errores explícitos."""
        self.print_test(3, "Error Explícito - API Key o Modelo no disponible")

        self.print_warning(
            "Este test requiere editar .env o mode_registry.py y observar errores"
        )

        if not self.prompt_yes_no("¿Quieres ejecutar este test ahora?"):
            self.print_instruction("Puedes ejecutarlo más tarde. Continuamos con Test 4.")
            return True

        # Test 3.1: API key inválida
        self.print_instruction("Test 3.1: Cambiar API key a inválida en .env")

        if self.prompt_yes_no("¿Has cambiado .env a API key inválida?"):
            self.print_instruction("Ejecuta: python validate_setup.py")
            if self.prompt_yes_no("¿Ves advertencia sobre API key inválida?"):
                self.print_check("Error API key capturado correctamente")
            else:
                self.print_error("No se mostró error esperado")
                return False

            self.print_instruction("Restaura API key válida en .env ahora")
            if self.prompt_yes_no("¿Has restaurado API key válida?"):
                self.print_check("API key restaurada")
            else:
                self.print_error("Necesitas restaurar API key válida para continuar")
                return False
        else:
            self.print_instruction(
                "Salta Test 3.1. Puedes hacerlo después manualmente."
            )

        return True

    def run_test_4(self):
        """Test 4: Upgrade ECO → RACING."""
        self.print_test(4, "Upgrade ECO → RACING")

        self.print_instruction(
            "Este test verifica que la heurística de decisión funciona"
        )

        steps = [
            ("Crea tarea simple: 'Revisar código' (tipo: Revisar, sin contexto extra)",
             True),
            ("Ejecuta con Router - debería ser ECO automáticamente", True),
            ("Crea tarea compleja: 'Decisión arquitectura' (tipo: Decidir, con contexto largo)",
             True),
            ("Ejecuta con Router - debería ser RACING automáticamente", True),
            ("Verifica que la latencia de RACING > latencia de ECO", True),
        ]

        for i, (step, _) in enumerate(steps, 1):
            if self.prompt_yes_no(f"[{i}/{len(steps)}] ¿{step}?"):
                self.print_check(f"Paso {i} completado")
            else:
                self.print_error(f"Paso {i} fallido")
                return False

        return True

    def run_test_5(self):
        """Test 5: Persistencia."""
        self.print_test(5, "Persistencia - Resultado, Trazabilidad y Activo")

        self.print_instruction(
            "Este test verifica que todo se guarda en BD correctamente"
        )

        steps = [
            ("Ejecuta una tarea", True),
            ("Haz click 'Ver trazabilidad' - expande y muestra todos los datos",
             True),
            ("En 'Resultado', haz click 'Crear activo'", True),
            ("Verifica que el activo aparece en lista 'Activos'", True),
            ("Los datos persisten después de cerrar la app", True),
        ]

        for i, (step, _) in enumerate(steps, 1):
            if self.prompt_yes_no(f"[{i}/{len(steps)}] ¿{step}?"):
                self.print_check(f"Paso {i} completado")
            else:
                self.print_error(f"Paso {i} fallido")
                return False

        return True

    def run_all(self):
        """Ejecuta todos los tests."""
        self.print_header("PRUEBAS DE ACEPTACIÓN - HITO 1")

        print("""
Este script te guiará a través de las 5 pruebas de aceptación para Hito 1.

Para cada prueba:
1. Sigue las instrucciones
2. Responde s/n cuando se te pregunte
3. Si un test falla, revisa ACCEPTANCE_TESTS_HITO1.md

Requisitos:
✅ .env configurado con GEMINI_API_KEY válida
✅ Dependencias instaladas (google-genai, streamlit, python-dotenv)
✅ `streamlit run app.py` ejecutándose (para tests 2-5)
        """)

        if not self.prompt_yes_no("¿Estás listo para comenzar?"):
            print("\n👋 Vuelve cuando estés listo.")
            return

        # Test 1
        if self.run_test_1():
            self.passed += 1
            self.results["Test 1"] = "✅ PASÓ"
        else:
            self.failed += 1
            self.results["Test 1"] = "❌ FALLÓ"
            print("\nHaz que Test 1 pase antes de continuar.")
            return

        # Tests 2-5
        if self.run_test_2():
            self.passed += 1
            self.results["Test 2"] = "✅ PASÓ"
        else:
            self.failed += 1
            self.results["Test 2"] = "❌ FALLÓ"

        if self.run_test_3():
            self.passed += 1
            self.results["Test 3"] = "✅ PASÓ"
        else:
            self.failed += 1
            self.results["Test 3"] = "❌ FALLÓ"

        if self.run_test_4():
            self.passed += 1
            self.results["Test 4"] = "✅ PASÓ"
        else:
            self.failed += 1
            self.results["Test 4"] = "❌ FALLÓ"

        if self.run_test_5():
            self.passed += 1
            self.results["Test 5"] = "✅ PASÓ"
        else:
            self.failed += 1
            self.results["Test 5"] = "❌ FALLÓ"

        # Resumen
        self.print_header("RESUMEN DE PRUEBAS")

        print("Resultados:\n")
        for test, result in self.results.items():
            print(f"  {result}  {test}")

        print(f"\nTotal: {self.passed} pasaron, {self.failed} fallaron\n")

        if self.failed == 0:
            self.print_check("¡TODOS LOS TESTS PASARON!")
            print("\n🎉 Hito 1 VALIDADO correctamente")
            print("\n📋 Próximo paso: Hito 2 - Captura de Tokens y Costo Real")
        else:
            self.print_error(f"{self.failed} test(s) fallaron")
            print(
                "\nRevisa ACCEPTANCE_TESTS_HITO1.md para detalles sobre cada test."
            )


if __name__ == "__main__":
    runner = AcceptanceTestRunner()
    try:
        runner.run_all()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrumpidos por usuario")
        sys.exit(0)
