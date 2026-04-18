from dataclasses import dataclass


@dataclass(frozen=True)
class ModeConfig:
    """Mapeo: modo → provider (real) + model + costo estimado."""
    mode: str
    provider: str
    model: str
    estimated_cost: float


MODE_REGISTRY: dict[str, ModeConfig] = {
    "eco": ModeConfig(
        mode="eco",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        estimated_cost=0.05,  # Estimado: ultra rápido, ultra barato
    ),
    "racing": ModeConfig(
        mode="racing",
        provider="gemini",
        model="gemini-2.5-pro",
        estimated_cost=0.30,  # Estimado: análisis profundo, muy potente
    ),
}


def get_mode_config(mode: str) -> ModeConfig:
    """Obtener configuración de un modo."""
    if mode not in MODE_REGISTRY:
        raise ValueError(f"Modo no soportado: {mode}")
    return MODE_REGISTRY[mode]
