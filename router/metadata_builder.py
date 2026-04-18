from typing import Optional
from .domain import TaskInput, RoutingDecision, ExecutionMetrics
from .model_catalog import ModelCatalog


class MetadataBuilder:
    """Construye metadatos de ejecución (latencia, coste, proveedor, modelo)."""

    def __init__(self, catalog: Optional[ModelCatalog] = None):
        """
        Inicializa MetadataBuilder con catálogo.

        Args:
            catalog: ModelCatalog instance. Si es None, crea uno con fallback.
        """
        self.catalog = catalog or ModelCatalog()

    def build_metrics(
        self,
        task: TaskInput,
        decision: RoutingDecision,
        latency_ms: int,
    ) -> ExecutionMetrics:
        config = self.catalog.get_mode_config(decision.mode)
        return ExecutionMetrics(
            latency_ms=latency_ms,
            estimated_cost=config.estimated_cost,
            provider_used=decision.provider,
            model_used=decision.model,
        )
