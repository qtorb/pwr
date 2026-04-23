"""Minimal operational contract for PWR task execution states.

This module keeps the current runtime truth intentionally small:
- what each persisted state means today
- which CTA it should expose
- which surfaces should show it
- which transitions are valid in the live runtime we have now
"""

from __future__ import annotations

from typing import Optional


TASK_EXECUTION_STATES = {"draft", "pending", "preview", "failed", "executed"}
LEGACY_TASK_STATES = {
    "borrador": "draft",
    "router_listo": "pending",
    "ejecutado": "executed",
}

HOME_ACTIVITY_STATES = ("pending", "preview", "failed", "executed")
HOME_RETAKE_STATES = ("pending", "preview", "failed")
REENTRY_CONTEXT_STATES = {"draft", "pending", "preview", "failed"}

STATE_CONTRACT = {
    "draft": {
        "definition": "Legacy compatibility state. Live UI does not create it.",
        "born_when": "Only through legacy/manual data or targeted tests.",
        "stability": "Stable compatibility state, but deprecated in the visible product.",
        "primary_cta": "Ejecutar ahora",
        "ui_label": "Pendiente de ejecucion",
        "home_surfaces": (),
        "reentry": True,
        "next_step": "Converge with pending and run a first execution.",
        "product_note": "Treat as pending until it disappears from active data.",
    },
    "pending": {
        "definition": "Task created and ready for a first execution.",
        "born_when": "Live task creation inserts status/execution_status = pending.",
        "stability": "Stable until execution runs.",
        "primary_cta": "Ejecutar ahora",
        "ui_label": "Pendiente de ejecucion",
        "home_surfaces": ("Hoy", "Para retomar"),
        "reentry": True,
        "next_step": "Execute for the first time.",
        "product_note": "Current source-of-truth state for not-yet-run tasks.",
    },
    "preview": {
        "definition": "A preview/propuesta previa was persisted instead of a real output.",
        "born_when": "Execution hits provider_not_available fallback and saves preview content.",
        "stability": "Stable until continued or retried.",
        "primary_cta": "Continuar",
        "ui_label": "Propuesta previa guardada",
        "home_surfaces": ("Hoy", "Para retomar"),
        "reentry": True,
        "next_step": "Continue from the saved proposal or rerun to get a real output.",
        "product_note": "Today it is a real runtime fallback, not a fake decorative state.",
    },
    "failed": {
        "definition": "A real execution attempt failed and the error was persisted.",
        "born_when": "Execution returns error other than provider_not_available.",
        "stability": "Stable until a retry produces preview or executed.",
        "primary_cta": "Reintentar",
        "ui_label": "Ejecucion fallida",
        "home_surfaces": ("Hoy", "Para retomar"),
        "reentry": True,
        "next_step": "Review the latest error and retry.",
        "product_note": "Failed should always expose the last visible error.",
    },
    "executed": {
        "definition": "A real output/result was persisted for the task.",
        "born_when": "Execution completes successfully and saves output.",
        "stability": "Stable until a new execution changes it.",
        "primary_cta": "Ejecutar de nuevo",
        "ui_label": "Resultado disponible",
        "home_surfaces": ("Hoy",),
        "reentry": False,
        "next_step": "Open the result or run again if it needs refresh.",
        "product_note": "Executed is a durable completed state, not an in-progress one.",
    },
}

# Valid runtime transitions after a CTA-driven execution attempt.
VALID_RUNTIME_TRANSITIONS = {
    "draft": {"preview", "failed", "executed"},
    "pending": {"preview", "failed", "executed"},
    "preview": {"preview", "failed", "executed"},
    "failed": {"preview", "failed", "executed"},
    "executed": {"preview", "failed", "executed"},
}

AMBIGUOUS_RUNTIME_TRANSITIONS = {
    ("draft", "pending"): "No live runtime path writes draft -> pending; draft is treated as pending compatibility state.",
}


def normalize_execution_state(value: str) -> str:
    state = str(value or "").strip().lower()
    if state in TASK_EXECUTION_STATES:
        return state
    return LEGACY_TASK_STATES.get(state, "")


def state_contract_entry(state: str) -> dict:
    normalized = normalize_execution_state(state) or "pending"
    return STATE_CONTRACT[normalized]


def task_state_caption(state: str) -> str:
    return state_contract_entry(state)["ui_label"]


def task_primary_action_label(state: str) -> str:
    return state_contract_entry(state)["primary_cta"]


def task_primary_action_hint(state: str) -> str:
    normalized = normalize_execution_state(state) or "pending"
    return {
        "failed": "Vas a reintentar usando el contexto actual y el intento previo visible.",
        "preview": "Vas a continuar desde la propuesta previa guardada.",
        "pending": "Vas a lanzar la primera ejecucion pendiente de esta tarea.",
        "draft": "Este borrador se tratara como pendiente y se ejecutara con el contexto actual.",
        "executed": "Vas a ejecutar de nuevo con el contexto visible.",
    }[normalized]


def resolve_runtime_execution_state(result_status: str, error_code: Optional[str]) -> str:
    """Map provider/runtime outcome to the persisted task state used by the app."""
    if result_status == "completed":
        return "executed"
    if str(error_code or "").strip().lower() == "provider_not_available":
        return "preview"
    return "failed"


def classify_runtime_transition(from_state: str, to_state: str) -> tuple[str, str]:
    src = normalize_execution_state(from_state)
    dst = normalize_execution_state(to_state)

    if not src or not dst:
        return ("invalid", "Unknown state outside the current contract.")

    if (src, dst) in AMBIGUOUS_RUNTIME_TRANSITIONS:
        return ("ambiguous", AMBIGUOUS_RUNTIME_TRANSITIONS[(src, dst)])

    if dst in VALID_RUNTIME_TRANSITIONS.get(src, set()):
        return ("valid", "Transition matches the current runtime contract.")

    return ("invalid", "Transition is not produced by the current live runtime.")
