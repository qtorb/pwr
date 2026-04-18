from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskInput:
    task_id: int
    title: str
    description: str
    task_type: str
    context: str = ""
    project_name: str = ""
    max_budget: Optional[int] = None
    preferred_mode: Optional[str] = None


@dataclass
class RoutingDecision:
    """Metadatos de DECISIÓN: qué modo, qué provider, por qué."""
    mode: str
    provider: str
    model: str
    reasoning_path: str
    complexity_score: float


@dataclass
class ExecutionMetrics:
    """Metadatos de EJECUCIÓN: latencia real, costo estimado, provider/model usado."""
    latency_ms: int
    estimated_cost: float
    provider_used: str
    model_used: str


@dataclass
class ExecutionError:
    """Error explícito de ejecución."""
    code: str  # "provider_unavailable", "invalid_key", "rate_limit", "network", etc.
    message: str


@dataclass
class ExecutionResult:
    """Resultado completo de ejecución."""
    task_id: int
    status: str  # "completed" o "error"
    output_text: str  # Solo si status=="completed"
    routing: RoutingDecision  # Decisión tomada
    metrics: ExecutionMetrics  # Métricas reales de ejecución
    error: Optional[ExecutionError] = None  # Solo si status=="error"
