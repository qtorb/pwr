import time
from .domain import TaskInput


class BaseProvider:
    name: str

    def run(self, task: TaskInput, model: str) -> str:
        raise NotImplementedError


class MockEcoProvider(BaseProvider):
    name = "mock"

    def run(self, task: TaskInput, model: str) -> str:
        time.sleep(0.6)
        return (
            f"[ECO:{model}] Respuesta rápida simulada para la tarea '{task.title}'.\n\n"
            f"Resumen:\n{task.description}\n\n"
            "Siguiente paso sugerido:\n"
            "- concretar mejor el objetivo o pedir una mejora a modo racing."
        )


class MockRacingProvider(BaseProvider):
    name = "mock"

    def run(self, task: TaskInput, model: str) -> str:
        time.sleep(1.4)
        return (
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
