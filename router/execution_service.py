import time
import sqlite3
from typing import Optional
from .decision_engine import DecisionEngine
from .domain import ExecutionResult, TaskInput, ExecutionError
from .metadata_builder import MetadataBuilder
from .model_catalog import ModelCatalog
from .providers import GeminiProvider, MockEcoProvider, MockRacingProvider, BaseProvider


class ExecutionService:
    """
    Orquestador principal:
    - decide modo (eco/racing) vía DecisionEngine + ModelCatalog
    - resuelve provider por nombre (hardcoded en _init_providers)
    - ejecuta provider (maneja errores explícitamente)
    - construye metadatos de decisión y ejecución
    - devuelve ExecutionResult

    IMPORTANTE (Bloque D):
    - ModelCatalog es agnóstico a fuente (BD o hardcoded)
    - Providers reales siguen siendo hardcoded (GeminiProvider, etc.)
    - Aunque el catálogo sea vivo en BD, los providers ejecutables son código Python

    Nota: Validación de API key y modelos ocurre al startup en GeminiProvider.__init__,
    no en cada ejecución, para evitar llamadas innecesarias.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        """
        Inicializa ExecutionService.

        Args:
            conn: sqlite3.Connection opcional para cargar ModelCatalog desde BD.
                  Si es None, usa fallback (mode_registry).
        """
        # Crear catálogo (desde BD si conn existe, sino fallback)
        catalog = ModelCatalog(conn) if conn else ModelCatalog()

        # Pasar catálogo a dependencias
        self.decision_engine = DecisionEngine(catalog)
        self.metadata_builder = MetadataBuilder(catalog)

        # Providers registrados por nombre (no por tupla)
        self.providers: dict[str, BaseProvider] = {}
        self.provider_errors: dict[str, str] = {}  # Almacenar errores de inicialización
        self._init_providers()

    def _init_providers(self) -> None:
        """Inicializa providers disponibles (con validación al startup)."""
        # Provider real: Gemini
        try:
            self.providers["gemini"] = GeminiProvider()
        except (ValueError, ImportError) as e:
            # Guardar error para reportarlo en ejecución
            self.provider_errors["gemini"] = str(e)
            print(f"⚠️ GeminiProvider no disponible: {e}")

        # Providers simulados para testing/fallback
        self.providers["mock"] = MockEcoProvider()  # Mock será eco

    def _get_provider(self, provider_name: str) -> BaseProvider:
        """
        Resuelve provider por nombre.

        Args:
            provider_name: nombre del provider ("gemini", "mock", etc.)

        Returns:
            Instancia del provider

        Raises:
            ValueError si el provider no está disponible
        """
        if provider_name not in self.providers:
            error_detail = self.provider_errors.get(provider_name, "no disponible")
            raise ValueError(
                f"Provider '{provider_name}' no disponible ({error_detail}). "
                f"Providers disponibles: {list(self.providers.keys())}"
            )
        return self.providers[provider_name]

    def execute(self, task: TaskInput) -> ExecutionResult:
        """
        Ejecuta una tarea:
        1. Decide modo (eco/racing)
        2. Resuelve provider
        3. Ejecuta provider (capturando errores explícitamente)
        4. Construye resultado con metadatos
        """
        started = time.perf_counter()

        # Paso 1: Decisión (nunca falla)
        decision = self.decision_engine.decide(task)

        # Paso 2: Resolver provider
        try:
            provider = self._get_provider(decision.provider)
        except ValueError as e:
            latency_ms = int((time.perf_counter() - started) * 1000)
            error = ExecutionError(
                code="provider_not_available",
                message=str(e),
            )
            metrics = self.metadata_builder.build_metrics(
                task=task,
                decision=decision,
                latency_ms=latency_ms,
            )
            return ExecutionResult(
                task_id=task.task_id,
                status="error",
                output_text="",
                routing=decision,
                metrics=metrics,
                error=error,
            )

        # Paso 3: Ejecutar provider (puede devolver error explícito)
        output_text, execution_error = provider.run(task, decision.model)

        latency_ms = int((time.perf_counter() - started) * 1000)
        metrics = self.metadata_builder.build_metrics(
            task=task,
            decision=decision,
            latency_ms=latency_ms,
        )

        # Paso 4: Construir resultado
        if execution_error:
            return ExecutionResult(
                task_id=task.task_id,
                status="error",
                output_text="",
                routing=decision,
                metrics=metrics,
                error=execution_error,
            )
        else:
            return ExecutionResult(
                task_id=task.task_id,
                status="completed",
                output_text=output_text,
                routing=decision,
                metrics=metrics,
                error=None,
            )
