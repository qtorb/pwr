import os
import time
from typing import Optional
from .domain import TaskInput, ExecutionError


class BaseProvider:
    """Interfaz base para todos los providers."""
    name: str

    def run(self, task: TaskInput, model: str) -> tuple[str, Optional[ExecutionError]]:
        """
        Ejecuta una tarea con el provider.

        Returns:
            (output_text, error)
            - Si success: (texto_output, None)
            - Si error: ("", ExecutionError(...))
        """
        raise NotImplementedError


class GeminiProvider(BaseProvider):
    """Provider real para Google Gemini usando google-genai SDK."""
    name = "gemini"

    def __init__(self):
        """Inicializa el provider y valida disponibilidad una sola vez."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY no configurada. "
                "Define la variable de entorno GEMINI_API_KEY con tu clave de Google AI Studio."
            )

        self.client = None
        self.validated_models = set()
        self._init_client()

        # Validar modelos esperados una sola vez al startup
        self._validate_expected_models()

    def _init_client(self):
        """Inicializa el cliente de Gemini y valida disponibilidad."""
        try:
            from google import genai
            self.genai = genai
        except ImportError:
            raise ImportError(
                "google-genai no está instalado. "
                "Instala con: pip install google-genai"
            )

        # Crear cliente con API key
        self.client = self.genai.Client(api_key=self.api_key)

        # Validar que el cliente funciona
        try:
            self._validate_api_connection()
        except Exception as e:
            raise ValueError(
                f"No se puede conectar con Gemini API: {str(e)}. "
                "Verifica que tu API key es válida."
            )

    def _validate_api_connection(self):
        """Valida que la API key funciona (llamada única)."""
        try:
            _ = self.client.models.list()
        except Exception as e:
            raise ValueError(f"API key inválida o conexión fallida: {str(e)}")

    def _validate_expected_models(self):
        """Valida que los modelos esperados (eco/racing) estén disponibles."""
        from .mode_registry import MODE_REGISTRY

        for mode, config in MODE_REGISTRY.items():
            if config.provider == "gemini":
                try:
                    # Cheque rápido: obtener info del modelo
                    _ = self.client.models.get(config.model)
                    self.validated_models.add(config.model)
                    print(f"✓ Modelo {config.model} ({mode}) disponible")
                except Exception as e:
                    # Advertencia pero no falla init - permite mock fallback
                    print(f"⚠️  Modelo {config.model} ({mode}) no disponible: {e}")

    def run(self, task: TaskInput, model: str) -> tuple[str, Optional[ExecutionError]]:
        """Ejecuta la tarea con Gemini (sin validación innecesaria)."""
        try:
            # Construir prompt desde la tarea
            prompt = self._build_prompt(task)

            # Llamar Gemini API
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
            )

            # Extraer texto de respuesta
            if response.text:
                return response.text, None
            else:
                error = ExecutionError(
                    code="empty_response",
                    message="Gemini devolvió respuesta vacía.",
                )
                return "", error

        except Exception as e:
            # Mapear excepciones comunes a códigos de error explícitos
            error_code, error_msg = self._classify_error(e)
            error = ExecutionError(code=error_code, message=error_msg)
            return "", error

    def _build_prompt(self, task: TaskInput) -> str:
        """Construye el prompt desde TaskInput."""
        return f"""Proyecto: {task.project_name or "Sin proyecto"}
Tipo de trabajo: {task.task_type}

Título: {task.title}

Descripción:
{task.description}

Contexto específico:
{task.context if task.context else "(Sin contexto adicional)"}

Ejecuta la tarea con precisión y claridad."""

    def _classify_error(self, exc: Exception) -> tuple[str, str]:
        """Clasifica excepciones en códigos de error explícitos."""
        exc_str = str(exc).lower()

        if "api_key" in exc_str or "authentication" in exc_str or "unauthorized" in exc_str or "invalid_key" in exc_str:
            return "invalid_key", "Clave API de Gemini inválida o expirada."

        if "rate_limit" in exc_str or "quota" in exc_str or "429" in exc_str or "too many requests" in exc_str:
            return "rate_limit", "Has alcanzado el límite de llamadas a Gemini. Intenta más tarde."

        if "connection" in exc_str or "timeout" in exc_str or "network" in exc_str:
            return "network", "Error de conexión con Gemini. Verifica tu conexión a internet."

        if "not found" in exc_str or "404" in exc_str or "model" in exc_str:
            return "model_not_found", f"Modelo no disponible: {exc_str}"

        # Error genérico
        return "provider_error", f"Error en Gemini: {str(exc)}"


class MockEcoProvider(BaseProvider):
    """Provider simulado para ECO (para testing sin credenciales)."""
    name = "mock"

    def run(self, task: TaskInput, model: str) -> tuple[str, Optional[ExecutionError]]:
        """Simula respuesta rápida."""
        time.sleep(0.6)
        output = (
            f"[ECO:{model}] Respuesta rápida simulada para la tarea '{task.title}'.\n\n"
            f"Resumen:\n{task.description}\n\n"
            "Siguiente paso sugerido:\n"
            "- concretar mejor el objetivo o pedir una mejora a modo racing."
        )
        return output, None


class MockRacingProvider(BaseProvider):
    """Provider simulado para RACING (para testing sin credenciales)."""
    name = "mock"

    def run(self, task: TaskInput, model: str) -> tuple[str, Optional[ExecutionError]]:
        """Simula respuesta profunda."""
        time.sleep(1.4)
        output = (
            f"[RACING:{model}] Respuesta profunda simulada para la tarea '{task.title}'.\n\n"
            "Diagnóstico:\n"
            f"- Tipo de tarea: {task.task_type}\n"
            f"- Proyecto: {task.project_name or 'sin proyecto'}\n\n"
            "Propuesta principal:\n"
            f"- {task.description}\n\n"
            "Riesgos o límites:\n"
            "- Esta es una ejecución simulada sin proveedor real.\n\n"
            "Siguiente paso concreto:\n"
            "- integrar un provider real manteniendo esta misma interfaz."
        )
        return output, None
