"""
ModelCatalog: Abstracción de catálogo y configuración de modos/modelos.

HOY (Bloque A):
- Implementación estática que lee de mode_registry.py
- Mapeo fijo: eco → gemini-2.5-flash-lite, racing → gemini-2.5-pro

MAÑANA (Model Radar D+):
- Implementación dinámica que lee de BD (model_catalog table)
- Observador actualiza precios, capacidades, estado vivo
- Interfaz NO cambia (agnóstica a fuente de datos)

Beneficio:
- DecisionEngine, ExecutionService, app.py no necesitan refactor
- Costura limpia con futuro observatorio de LLMs
"""

from typing import List, Optional, Dict
import sqlite3
from .mode_registry import MODE_REGISTRY, ModeConfig


class ModelCatalog:
    """
    Abstracción para acceso a catálogo y configuración de modos/modelos (Bloque D+).

    Interfaz estable, agnóstica a dónde vienen los datos:
    - Bloque A-C: mode_registry.py (hardcoded)
    - Bloque D+: model_catalog BD table (observatorio vivo)

    ═══════════════════════════════════════════════════════════════════════════════════
    CAMPOS PÚBLICOS (Exposibles en /radar endpoint - Bloque E1):
    ═══════════════════════════════════════════════════════════════════════════════════
    - provider (str): Proveedor de LLM ("gemini", "mock", etc.)
    - model_name (str): Nombre del modelo ("gemini-2.5-flash-lite", etc.)
    - mode (str): Modo de operación ("eco", "racing") - BRIDGE TEMPORAL para transición
    - estimated_cost_per_run (float): Coste estimado por ejecución
    - context_window (int): Tamaño de ventana de contexto en tokens
    - capabilities_json (str): JSON con capacidades del modelo {"vision": bool, "reasoning": bool, ...}
    - status (str): Estado operativo ("active", "deprecated", "experimental")
    - is_internal (bool): Indica si es provider/modelo solo para testing (1=internal, 0=público)

    ═══════════════════════════════════════════════════════════════════════════════════
    CAMPOS INTERNOS (NO exposibles en /radar - solo uso en router):
    ═══════════════════════════════════════════════════════════════════════════════════
    - pricing_input_per_mtok (float): Precio por millón de tokens de entrada (datos BD brutos)
    - pricing_output_per_mtok (float): Precio por millón de tokens de salida (datos BD brutos)
    - deprecated_at (str): Timestamp de deprecación (si aplica)
    - mode (str): BRIDGE TEMPORAL - será eliminado cuando router_policy table esté lista.
      Actualmente mantiene mapeo eco↔gemini-2.5-flash-lite y racing↔gemini-2.5-pro.
      En futuro: router_policy table tendrá lógica de decisión independiente del catálogo.

    ═══════════════════════════════════════════════════════════════════════════════════
    GARANTÍAS FUNCIONALES:
    ═══════════════════════════════════════════════════════════════════════════════════
    - DecisionEngine: Consume mode_registry (fallback) o ModelCatalog._modes (BD)
    - ExecutionService: Resuelve providers desde código Python hardcoded, no desde BD
    - MetadataBuilder: Lee estimated_cost y model_name de catálogo para registro de métricas
    - get_capabilities(): Lee capabilities_json de BD si está disponible, fallback None

    NOTA: BD describe QUÉ existe (catálogo), código implementa CÓMO ejecutar (providers).
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        """
        Inicializa catálogo desde fuente.

        Args:
            conn: sqlite3.Connection. Si existe, carga desde BD.
                  Si es None, carga desde mode_registry (fallback).
        """
        if conn is not None:
            # Bloque D+: Leer desde BD (fuente viva)
            self._load_from_db(conn)
        else:
            # Fallback: Leer desde mode_registry (hardcoded)
            self._load_from_registry()

    def _load_from_registry(self) -> None:
        """Carga desde mode_registry.py (hardcoded, fallback)."""
        self._modes = MODE_REGISTRY
        self._provider_available = {"gemini", "mock"}
        self._catalog_rows = {}  # No usado en fallback

    def _load_from_db(self, conn: sqlite3.Connection) -> None:
        """
        Carga catálogo desde tabla model_catalog.

        Args:
            conn: sqlite3.Connection abierta
        """
        try:
            # Leer todos los modelos de la tabla (Bloque E1: incluye is_internal)
            rows = conn.execute(
                "SELECT id, provider, model_name, estimated_cost_per_run, mode, "
                "       capabilities_json, context_window, status, is_internal "
                "FROM model_catalog WHERE status = 'active'"
            ).fetchall()

            # Construir _modes dict: mode -> ModeConfig
            self._modes = {}
            self._catalog_rows = {}
            providers_set = set()

            for row in rows:
                model_id = row[0]
                provider = row[1]
                model_name = row[2]
                estimated_cost = row[3]
                mode = row[4]  # "eco" o "racing"
                capabilities_json = row[5]  # Bloque E0: Lee capabilities_json de BD
                context_window = row[6]
                status = row[7]
                is_internal = row[8]  # Bloque E1: is_internal para filtrado en /radar

                providers_set.add(provider)

                # Guardar fila raw para reference (Bloque E0/E1: incluye capabilities_json + is_internal)
                self._catalog_rows[model_name] = {
                    "provider": provider,
                    "model_name": model_name,
                    "estimated_cost_per_run": estimated_cost,
                    "mode": mode,
                    "capabilities_json": capabilities_json,  # Para get_capabilities()
                    "context_window": context_window,
                    "status": status,
                    "is_internal": is_internal,  # Bloque E1: Para filtrado en export_public_catalog()
                }

                # Crear ModeConfig si no existe para este modo
                if mode and mode not in self._modes:
                    self._modes[mode] = ModeConfig(
                        mode=mode,
                        provider=provider,
                        model=model_name,
                        estimated_cost=estimated_cost,
                    )

            self._provider_available = providers_set

        except Exception as e:
            # Fallback a hardcoded si BD falla
            print(f"⚠️ ModelCatalog: error leyendo BD: {e}. Usando mode_registry.")
            self._load_from_registry()

    def get_mode_config(self, mode: str) -> ModeConfig:
        """
        Obtiene configuración de un modo (eco o racing).

        Args:
            mode: "eco" o "racing"

        Returns:
            ModeConfig con provider, model, pricing, etc.

        Raises:
            ValueError si modo no existe
        """
        if mode not in self._modes:
            available = list(self._modes.keys())
            raise ValueError(
                f"Modo '{mode}' no soportado. Disponibles: {available}"
            )
        return self._modes[mode]

    def get_model(self, model_name: str) -> Optional[ModeConfig]:
        """
        Busca configuración por nombre de modelo.

        Args:
            model_name: e.g., "gemini-2.5-flash-lite"

        Returns:
            ModeConfig si existe, None si no.

        FUTURO (Model Radar):
        - Búsqueda en model_catalog BD table
        """
        for mode, config in self._modes.items():
            if config.model == model_name:
                return config
        return None

    def list_modes(self) -> List[str]:
        """
        Retorna lista de modos disponibles.

        Returns:
            ["eco", "racing"] (hoy)
            Lista dinámica desde BD (mañana)
        """
        return list(self._modes.keys())

    def list_providers(self) -> List[str]:
        """
        Retorna lista de providers registrados.

        Returns:
            ["gemini", "mock"] (hoy)
        """
        return list(self._provider_available)

    def is_provider_available(self, provider: str) -> bool:
        """
        Chequea si provider está registrado/disponible.

        Args:
            provider: e.g., "gemini", "mock", "claude"

        Returns:
            True si está disponible, False si no.

        FUTURO (Model Radar):
        - Chequea status en model_catalog BD
        - Incluye información de deprecación, limitaciones
        """
        return provider in self._provider_available

    def get_pricing(self, model_name: str) -> Optional[float]:
        """
        Obtiene coste estimado de un modelo.

        Args:
            model_name: e.g., "gemini-2.5-flash-lite"

        Returns:
            Coste estimado (ej. 0.05) o None si no existe

        FUTURO (Model Radar):
        - Leerá precio actual de BD (actualizado por observador)
        """
        config = self.get_model(model_name)
        if config:
            return config.estimated_cost
        return None

    def get_capabilities(self, model_name: str) -> Optional[dict]:
        """
        Obtiene capacidades de un modelo desde BD (Bloque E0).

        Args:
            model_name: e.g., "gemini-2.5-pro"

        Returns:
            Dict con capacidades {"vision": True, "reasoning": False} o None

        Bloque E0: Lee desde _catalog_rows que viene de BD (model_catalog.capabilities_json)
        Fallback: Si no hay BD o modelo no existe, retorna None.
        """
        # Intentar leer de BD (si está disponible en _catalog_rows)
        if hasattr(self, '_catalog_rows') and model_name in self._catalog_rows:
            capabilities_json = self._catalog_rows[model_name].get("capabilities_json")
            if capabilities_json:
                try:
                    import json
                    return json.loads(capabilities_json)
                except (json.JSONDecodeError, TypeError):
                    return {}

        # Fallback: Si sin BD o sin datos, retorna None
        return None

    def export_public_catalog(self, include_internal: bool = False) -> dict:
        """
        Exporta catálogo vivo como JSON para endpoint /radar v1.

        Bloque E1: Live Catalog Snapshot
        ═════════════════════════════════════════════════════════════════════

        Retorna estructura JSON con:
        - providers: Providers disponibles y sus modelos
        - modes: Modos de ejecución (eco, racing) - BRIDGE TEMPORAL
        - summary: Metadatos del catálogo

        Args:
            include_internal: Si False (default), filtra modelos con is_internal=1
                              Si True, incluye modelos internos (mock, test)

        Returns:
            Dict con estructura:
            {
              "providers": {
                "gemini": {
                  "name": "gemini",
                  "models": [...]
                }
              },
              "modes": {
                "eco": {
                  "name": "eco",
                  "label": "Económico",
                  "description": "...",
                  "models": [...]
                }
              },
              "summary": {
                "total_providers": 1,
                "total_models": 2,
                "providers_list": ["gemini"],
                "modes_list": ["eco", "racing"],
                "default_mode": "eco"
              }
            }

        NOTA: Esta es la "live catalog snapshot" de /radar v1.
        NO es observatorio histórico, NO es health monitor, NO es scoring adaptativo.
        """
        import json

        # Estructura base
        catalog = {
            "providers": {},
            "modes": {},
            "summary": {}
        }

        # ==================== Construir providers ====================
        for model_name, row in self._catalog_rows.items():
            # FILTRO: Si is_internal=1 y no está autorizado, saltar
            is_internal = row.get("is_internal", 0)
            if is_internal == 1 and not include_internal:
                continue

            provider = row.get("provider", "")
            if not provider:
                continue

            # Inicializar provider si no existe
            if provider not in catalog["providers"]:
                catalog["providers"][provider] = {
                    "name": provider,
                    "models": []
                }

            # Serializar modelo solo con campos públicos (Bloque E1)
            model_entry = {
                "id": model_name,
                "name": model_name,
                "provider": provider,
                "mode": row.get("mode"),
                "status": row.get("status", "active"),
                "is_internal": is_internal,
                "estimated_cost_per_run": row.get("estimated_cost_per_run"),
                "context_window": row.get("context_window"),
            }

            # Parsear capabilities (Bloque E0: ya están en BD)
            capabilities_json = row.get("capabilities_json", "{}")
            try:
                capabilities = json.loads(capabilities_json) if isinstance(capabilities_json, str) else capabilities_json
                # Garantizar estructura mínima
                model_entry["capabilities"] = {
                    "vision": capabilities.get("vision", False),
                    "reasoning": capabilities.get("reasoning", False),
                    "code_execution": capabilities.get("code_execution", False),
                    **{k: v for k, v in capabilities.items() if k not in ["vision", "reasoning", "code_execution"]}
                }
            except (json.JSONDecodeError, TypeError, AttributeError):
                model_entry["capabilities"] = {}

            catalog["providers"][provider]["models"].append(model_entry)

        # ==================== Construir modes ====================
        # Nota: 'mode' es BRIDGE TEMPORAL (Bloque D)
        # En futuro: migrará a tabla separada router_policy
        for mode_name in self.list_modes():
            mode_config = self.get_mode_config(mode_name)
            if not mode_config:
                continue

            # Recolectar modelos que pertenecen a este modo
            mode_models = []
            for model_name, row in self._catalog_rows.items():
                if row.get("mode") == mode_name:
                    # Aplicar mismo filtro que providers
                    if row.get("is_internal") == 1 and not include_internal:
                        continue
                    mode_models.append(model_name)

            catalog["modes"][mode_name] = {
                "name": mode_name,
                "label": "Económico" if mode_name == "eco" else "Potencia máxima" if mode_name == "racing" else mode_name,
                "description": (
                    "Rápido, barato, para tareas simples" if mode_name == "eco"
                    else "Lento, caro, para tareas complejas" if mode_name == "racing"
                    else f"Modo {mode_name}"
                ),
                "models": mode_models
            }

        # ==================== Construir summary ====================
        all_providers = set()
        all_models = []
        for model_name, row in self._catalog_rows.items():
            if row.get("is_internal") == 1 and not include_internal:
                continue
            all_providers.add(row.get("provider", ""))
            all_models.append(model_name)

        catalog["summary"] = {
            "total_providers": len(all_providers),
            "total_models": len(all_models),
            "providers_list": sorted(list(all_providers)),
            "modes_list": self.list_modes(),
            "default_mode": "eco"
        }

        return catalog

    def __repr__(self) -> str:
        """Representación legible del catálogo."""
        modes_str = ", ".join(self.list_modes())
        providers_str = ", ".join(self.list_providers())
        return f"ModelCatalog(modes=[{modes_str}], providers=[{providers_str}])"
