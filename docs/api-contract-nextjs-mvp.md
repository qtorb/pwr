# API Contract for Next.js MVP

## 1. Objetivo del contrato

Este documento fija el contrato mínimo que necesitará un futuro frontend Next.js para empezar a consumir el núcleo vivo de PWR a través de FastAPI, sin depender de Streamlit.

El objetivo no es rediseñar el producto ni abrir una arquitectura grande. Es dejar claro:

- qué pantallas MVP puede cubrir ya la API actual
- qué datos necesita cada una
- qué huecos reales siguen existiendo
- en qué orden conviene migrar el frontend

La regla de esta fase es simple:

- Streamlit sigue siendo el frontend vivo actual
- Next.js empezará como frontend paralelo
- FastAPI será la fuente de datos del nuevo frontend

## 2. Pantallas MVP de Next.js

### Home

La Home MVP de Next.js debe cubrir:

- actividad reciente (`Hoy`)
- trabajo retomable (`Para retomar`)
- acceso a proyectos

### Project workspace

El workspace de proyecto MVP debe cubrir:

- datos básicos del proyecto
- listado de tareas del proyecto
- creación de nueva tarea
- listado de activos relacionados

### Task detail / execution context

La vista de tarea MVP debe cubrir:

- detalle básico de la tarea
- estado actual
- última ejecución visible
- historial de ejecuciones si existe
- contexto suficiente para reentrada

### Assets panel

El panel de activos MVP debe cubrir:

- listado de activos por proyecto
- apertura de un activo concreto
- reutilización de activo como base de nueva tarea

## 3. Endpoints actuales disponibles

### Sistema

- `GET /`
  - root mínima del backend
- `GET /health`
  - health simple
- `GET /api/state-contract`
  - contrato mínimo de estados y transiciones válidas

### Home

- `GET /api/home/activity`
  - lista actividad reciente para `Hoy`
  - query params:
    - `limit`
    - `today_only`

- `GET /api/home/reentry`
  - lista tareas reabribles para `Para retomar`
  - query params:
    - `limit`

### Proyectos

- `GET /api/projects`
  - lista proyectos

- `GET /api/projects/{project_id}`
  - detalle básico de un proyecto

- `GET /api/projects/{project_id}/tasks`
  - lista tareas de proyecto
  - query params:
    - `search`

- `POST /api/projects/{project_id}/tasks`
  - crea tarea nueva en proyecto

### Tareas / ejecuciones

- `GET /api/tasks/{task_id}`
  - detalle básico de tarea

- `GET /api/tasks/{task_id}/executions`
  - historial de ejecuciones de la tarea
  - query params:
    - `limit`

- `GET /api/tasks/{task_id}/executions/latest`
  - última ejecución persistida de la tarea

### Activos reutilizables

- `GET /api/projects/{project_id}/assets`
  - lista activos del proyecto

- `POST /api/projects/{project_id}/assets`
  - crea activo nuevo

- `GET /api/assets/{asset_id}`
  - detalle de activo

- `POST /api/assets/{asset_id}/reuse`
  - devuelve payload de reutilización como base de nueva tarea

## 4. Qué datos necesita cada pantalla

### Home

Datos mínimos:

- items de actividad reciente
  - `id`
  - `project_id`
  - `project_name`
  - `title`
  - `task_type`
  - `execution_status`
  - `updated_at`
  - `suggested_model`

Endpoints actuales suficientes:

- `GET /api/home/activity`
- `GET /api/home/reentry`
- `GET /api/projects`

Observación:

Para una Home MVP, la API actual ya es suficiente.

### Project workspace

Datos mínimos:

- detalle de proyecto
  - `id`
  - `name`
  - `description`
  - `objective`
  - `base_context`
  - `base_instructions`
  - `task_count`
  - `asset_count`

- tareas del proyecto
  - `id`
  - `title`
  - `task_type`
  - `execution_status`
  - `updated_at`
  - `router_summary`
  - `suggested_model`

- activos del proyecto
  - `id`
  - `asset_type`
  - `title`
  - `summary`
  - `task_title`
  - `source_execution_status`
  - `created_at`
  - `updated_at`

Endpoints actuales suficientes:

- `GET /api/projects/{project_id}`
- `GET /api/projects/{project_id}/tasks`
- `GET /api/projects/{project_id}/assets`
- `POST /api/projects/{project_id}/tasks`

Observación:

También es viable ya con la API actual, aunque obliga a hacer varias llamadas.

### Task detail / execution context

Datos mínimos:

- tarea
  - `id`
  - `project_id`
  - `title`
  - `description`
  - `task_type`
  - `context`
  - `execution_status`
  - `router_summary`
  - `llm_output`
  - `suggested_model`
  - `updated_at`

- última ejecución
  - `execution_status`
  - `provider`
  - `model`
  - `prompt_text`
  - `output_text`
  - `error_code`
  - `error_message`
  - `artifact_md_path`
  - `artifact_json_path`
  - `executed_at`

- historial
  - lista de runs si hace falta

Endpoints actuales suficientes para MVP:

- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/executions/latest`
- `GET /api/tasks/{task_id}/executions`
- `GET /api/state-contract`

Observación:

La pantalla es factible ya, pero falta un endpoint agregado que reduzca round-trips y simplifique Next.js.

### Assets panel

Datos mínimos:

- lista de activos
  - `id`
  - `asset_type`
  - `title`
  - `summary`
  - `task_title`
  - `source_execution_status`
  - `source_provider`
  - `source_model`
  - `source_executed_at`
  - `artifact_md_path`
  - `artifact_json_path`

- detalle de activo
  - `content`
  - `summary`
  - `project_name`
  - `task_title`
  - `source_execution_id`
  - `source_execution_status`

- reutilización
  - `title`
  - `context`
  - `notice`

Endpoints actuales suficientes:

- `GET /api/projects/{project_id}/assets`
- `GET /api/assets/{asset_id}`
- `POST /api/assets/{asset_id}/reuse`
- `POST /api/projects/{project_id}/assets`

Observación:

El loop MVP de activos ya está cubierto por la API actual.

## 5. Gaps detectados en la API actual

### Gap 1 — Falta un endpoint agregado para task detail

Hoy Next.js tendría que llamar a:

- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/executions/latest`
- opcionalmente `GET /api/tasks/{task_id}/executions`
- `GET /api/state-contract`

Eso funciona, pero hace más compleja la capa de carga.

### Gap 2 — Falta un endpoint agregado para project workspace

Hoy el workspace necesita combinar:

- proyecto
- tareas
- activos

Eso también funciona, pero obliga a coordinar varias llamadas desde el cliente.

### Gap 3 — No existe todavía ejecución de tarea por HTTP

La API actual expone lectura, creación de tarea y activos, pero no la acción viva de ejecutar una tarea desde FastAPI.

Esto no bloquea la migración de Home ni de proyecto como vistas de lectura/creación básica, pero sí bloquea una migración completa del flujo de ejecución a Next.js.

### Gap 4 — No existe actualización/edición de tarea o proyecto por HTTP

No es imprescindible para el MVP inicial de lectura + creación, pero sí aparecerá pronto si el frontend nuevo quiere editar contexto o metadata.

## 6. Endpoints nuevos sugeridos, solo si son imprescindibles

No propongo añadir nada en esta iteración.

Pero para una migración Next.js con fricción razonable, los dos endpoints nuevos realmente útiles serían:

### Imprescindible 1 — `GET /api/tasks/{task_id}/workspace`

Payload agregado sugerido:

- `task`
- `project`
- `latest_execution`
- `execution_history`
- `state_contract_entry`
- `asset_list` opcional o resumida

Justificación:

Reduce carga de composición en el cliente para la pantalla más sensible del producto.

### Imprescindible 2 — `GET /api/projects/{project_id}/workspace`

Payload agregado sugerido:

- `project`
- `tasks`
- `assets`
- quizá bloques resumidos para sidebar/workspace

Justificación:

Reduce round-trips y simplifica la primera versión de `Project workspace` en Next.js.

### No imprescindible todavía

No considero imprescindibles todavía:

- endpoints de búsqueda semántica
- endpoints de tags avanzados
- endpoints de memoria
- endpoints de edición masiva

## 7. Orden recomendado de migración

### Fase 1 — Home

Primero migrar Home porque:

- usa endpoints simples
- tiene alto valor de visibilidad
- toca poco comportamiento delicado
- es buena prueba de consumo real desde Next.js

Base recomendada:

- `GET /api/home/activity`
- `GET /api/home/reentry`
- `GET /api/projects`

### Fase 2 — Project workspace

Después migrar el workspace de proyecto porque:

- ya hay lectura de proyecto, tareas y activos
- ya existe creación de tarea por HTTP
- permite validar navegación y continuidad real sin tocar todavía la ejecución viva

Base recomendada:

- `GET /api/projects/{project_id}`
- `GET /api/projects/{project_id}/tasks`
- `GET /api/projects/{project_id}/assets`
- `POST /api/projects/{project_id}/tasks`

### Fase 3 — Assets

Luego migrar activos porque:

- la capa ya existe
- su loop está bastante aislado
- permite demostrar reutilización real sin depender de todo el flujo de ejecución

Base recomendada:

- `GET /api/projects/{project_id}/assets`
- `GET /api/assets/{asset_id}`
- `POST /api/assets/{asset_id}/reuse`
- `POST /api/projects/{project_id}/assets`

## 8. Decisión explícita de transición

La decisión para la transición queda fijada así:

- Streamlit sigue vivo durante la transición
- Next.js empieza como frontend paralelo
- FastAPI será la fuente del nuevo frontend

Implicación práctica:

- no se migra todo de golpe
- no se duplica lógica en frontend nuevo
- el dominio sigue viviendo en `services/`
- FastAPI actúa como capa de exposición HTTP del núcleo
- Streamlit puede seguir siendo la referencia funcional mientras Next.js madura pantalla a pantalla

## 9. Conclusión operativa

La API actual ya permite arrancar una migración Next.js MVP por:

1. Home
2. Project workspace
3. Assets

Sin embargo, una migración limpia de `Task detail / execution context` agradecerá pronto uno o dos endpoints agregados.

La recomendación es no abrir esos endpoints todavía si no se empieza ya el frontend nuevo. Cuando empiece la implementación Next.js, convendrá añadir primero:

- `GET /api/projects/{project_id}/workspace`
- `GET /api/tasks/{task_id}/workspace`

No porque la API actual sea insuficiente, sino porque así el frontend paralelo tendrá menos lógica de composición dispersa desde el primer día.
