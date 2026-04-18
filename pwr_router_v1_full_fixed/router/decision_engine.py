from .domain import TaskInput, RoutingDecision
from .mode_registry import get_mode_config


class DecisionEngine:
    """
    Decide eco o racing según señales simples.
    No ejecuta nada. Solo decide.
    """

    def decide(self, task: TaskInput) -> RoutingDecision:
        if task.preferred_mode in {"eco", "racing"}:
            config = get_mode_config(task.preferred_mode)
            return RoutingDecision(
                mode=config.mode,
                provider=config.provider,
                model=config.model,
                reasoning_path=f"Modo forzado por usuario: {task.preferred_mode}.",
                complexity_score=0.5 if task.preferred_mode == "eco" else 0.9,
            )

        combined = f"{task.title} {task.description} {task.context}".lower()

        score = 0.0
        signals = []

        if task.task_type == "Programar":
            score += 0.5
            signals.append("lógica estructurada / código")
        elif task.task_type == "Decidir":
            score += 0.4
            signals.append("comparación de alternativas")
        elif task.task_type == "Revisar":
            score += 0.35
            signals.append("evaluación crítica")
        elif task.task_type == "Escribir":
            score += 0.25
            signals.append("generación estructurada de contenido")

        if len(combined) > 500:
            score += 0.25
            signals.append("alto volumen de contexto")

        strategic_terms = [
            "arquitectura", "estrategia", "trade-off",
            "prioridad", "roadmap", "decisión", "decision"
        ]
        if any(t in combined for t in strategic_terms):
            score += 0.3
            signals.append("razonamiento estratégico")

        tech_terms = [
            "api", "bug", "python", "sql", "backend",
            "frontend", "deploy"
        ]
        if any(t in combined for t in tech_terms):
            score += 0.25
            signals.append("complejidad técnica")

        mode = "racing" if score >= 0.5 else "eco"
        config = get_mode_config(mode)

        if not signals:
            signals.append("tarea acotada de baja complejidad")

        reasoning_path = (
            f"Decisión automática: modo {mode.upper()}.\n"
            f"Complejidad estimada: {round(score, 2)}.\n"
            f"Señales detectadas: {', '.join(signals)}.\n\n"
            f"Criterio: priorizar {'precisión y profundidad' if mode=='racing' else 'velocidad y coste'}."
        )

        return RoutingDecision(
            mode=config.mode,
            provider=config.provider,
            model=config.model,
            reasoning_path=reasoning_path,
            complexity_score=min(score, 1.0),
        )
