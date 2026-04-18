from .domain import TaskInput, RoutingDecision, ExecutionMetrics
from .mode_registry import get_mode_config


class MetadataBuilder:
    def build_metrics(
        self,
        task: TaskInput,
        decision: RoutingDecision,
        latency_ms: int,
    ) -> ExecutionMetrics:
        config = get_mode_config(decision.mode)
        return ExecutionMetrics(
            latency_ms=latency_ms,
            estimated_cost=config.estimated_cost,
            provider_used=decision.provider,
            model_used=decision.model,
        )
