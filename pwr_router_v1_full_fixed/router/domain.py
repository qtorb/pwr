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
    mode: str
    provider: str
    model: str
    reasoning_path: str
    complexity_score: float


@dataclass
class ExecutionMetrics:
    latency_ms: int
    estimated_cost: float
    provider_used: str
    model_used: str


@dataclass
class ExecutionResult:
    task_id: int
    status: str
    output_text: str
    routing: RoutingDecision
    metrics: ExecutionMetrics
