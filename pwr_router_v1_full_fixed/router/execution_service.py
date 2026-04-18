import time
from .decision_engine import DecisionEngine
from .domain import ExecutionResult, TaskInput
from .metadata_builder import MetadataBuilder
from .providers import MockEcoProvider, MockRacingProvider


class ExecutionService:
    """
    Orquestador principal:
    - decide modo
    - ejecuta provider
    - construye metadatos
    - devuelve ExecutionResult
    """

    def __init__(self) -> None:
        self.decision_engine = DecisionEngine()
        self.metadata_builder = MetadataBuilder()
        self.providers = {
            ("mock", "eco"): MockEcoProvider(),
            ("mock", "racing"): MockRacingProvider(),
        }

    def _get_provider(self, provider_name: str, mode: str):
        key = (provider_name, mode)
        if key not in self.providers:
            raise ValueError(f"No hay provider registrado para {key}")
        return self.providers[key]

    def execute(self, task: TaskInput) -> ExecutionResult:
        started = time.perf_counter()

        decision = self.decision_engine.decide(task)
        provider = self._get_provider(decision.provider, decision.mode)
        output_text = provider.run(task, decision.model)

        latency_ms = int((time.perf_counter() - started) * 1000)
        metrics = self.metadata_builder.build_metrics(
            task=task,
            decision=decision,
            latency_ms=latency_ms,
        )

        return ExecutionResult(
            task_id=task.task_id,
            status="completed",
            output_text=output_text,
            routing=decision,
            metrics=metrics,
        )
