from dataclasses import dataclass


@dataclass(frozen=True)
class ModeConfig:
    mode: str
    provider: str
    model: str
    estimated_cost: float


MODE_REGISTRY: dict[str, ModeConfig] = {
    "eco": ModeConfig(
        mode="eco",
        provider="mock",
        model="fast-simulated",
        estimated_cost=1.0,
    ),
    "racing": ModeConfig(
        mode="racing",
        provider="mock",
        model="deep-simulated",
        estimated_cost=10.0,
    ),
}


def get_mode_config(mode: str) -> ModeConfig:
    if mode not in MODE_REGISTRY:
        raise ValueError(f"Modo no soportado: {mode}")
    return MODE_REGISTRY[mode]
