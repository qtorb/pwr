# BLOQUE H: Persistencia Visible — Microplan Disciplinado

**Estado:** 📋 Microplan (NO IMPLEMENTAR AÚN)
**Objetivo:** PWR deja de sentirse como herramienta aislada, pasa a sentirse como workspace con memoria útil

---

## 1. QUÉ PROBLEMA DE PRODUCTO RESUELVE ESTE BLOQUE

### Problema núcleo

Hoy PWR **guarda todo técnicamente** (tareas, resultados, proyecto) pero el usuario **no lo siente**.

Usuario típico:
```
1. Hace tarea A
2. Ve resultado
3. Cierra
4. Vuelve después
5. ¿Dónde está lo que hice? ¿Se guardó? ¿Dónde lo encuentro?
```

**Síntomas:**
- ❌ Usuario no entiende dónde quedó su trabajo
- ❌ No sabe si puede retomar o si es "perdido"
- ❌ No ve continuidad entre sesiones
- ❌ Proyecto existe técnicamente pero no visualmente
- ❌ Resultado desaparece después de verlo (no retenido)
- ❌ Home no ayuda a responder "qué debo hacer ahora"

### Impacto de no resolver esto

```
Usuario piensa: "Ejecuté tarea, luego desapareció. ¿Se guardó?"
              → Desconfianza
              → Comportamiento: no confía en retomar
              → Adopción baja
              → PWR se siente como demostración, no como tool real
```

### Solución esperada

Persistencia **visible** = señales claras que PWR es un espacio donde el trabajo **queda guardado, reaparece, se puede retomar, tiene continuidad**.

---

## 2. QUÉ VE HOY EL USUARIO Y POR QUÉ NO BASTA

### HOY: Después de ejecutar una tarea

```
┌──────────────────────────────────────────────────┐
│  [Resultado del modelo]                          │
│  "Aquí está tu respuesta"                        │
│                                                  │
│  [3 CTAs:]                                       │
│  - Copiar resultado                             │
│  - Otra tarea rápida                            │
│  - Ver proyecto                                 │
│                                                  │
│  ¿Dónde está el contexto?                       │
│  - No ve: "guardé esto en Proyecto X"           │
│  - No ve: "resultado guardado como Task Y"      │
│  - No ve: "puedes volver a este en cualquier..."│
│  - No ve: "siguiente paso natural es..."        │
└──────────────────────────────────────────────────┘
```

**Lo que está pasando técnicamente:**
- ✅ Resultado guardado en BD (save_execution_result)
- ✅ Task creada en proyectos
- ✅ Proyecto existe

**Lo que el usuario VE:**
- ❌ "Resultado de modelo" (aislado)
- ❌ 3 botones desconectados (copiar, otra, proyecto)
- ❌ Nada que diga "esto quedó guardado aquí"

**Por qué no basta:**
- User no entiende dónde quedó el resultado
- User no entiende relación entre tarea/proyecto/resultado
- User no siente continuidad

---

### HOY: Home después de ejecutar

```
┌──────────────────────────────────────────────────┐
│  Mis tareas                                      │
│                                                  │
│  Trabajo en progreso:                           │
│  [Grid 3 cols - tareas recientes]               │
│  "Resume este documento" → Continuar             │
│                                                  │
│  Mis proyectos:                                 │
│  [Grid 2 cols - proyectos]                      │
│  "Mi primer proyecto" → Abrir                    │
│                                                  │
│  [Nueva tarea] [Crear proyecto]                 │
└──────────────────────────────────────────────────┘
```

**Lo que usuario ENTIENDE:**
- ✅ Acá están mis tareas
- ✅ Acá están mis proyectos
- ✅ Puedo continuar o crear

**Lo que usuario NO ENTIENDE:**
- ❌ Qué tarea ejecuté hace poco
- ❌ Dónde está el resultado que vi hace 5 minutos
- ❌ Relación entre esa tarea y este proyecto
- ❌ Cuál es mi siguiente acción natural
- ❌ Qué continuar primero

**Por qué no basta:**
- Grid genérico (no dice cuál fue reciente, cuál es urgente)
- No muestra resultados ejecutados (solo tareas)
- No hay "historia" de lo que pasó hoy
- Usuario sigue sin sentir continuidad

---

### HOY: Dentro de un proyecto

```
┌──────────────────────────────────────────────────┐
│  Mi primer proyecto                              │
│                                                  │
│  Tareas:                                         │
│  [Grid de tareas del proyecto]                  │
│  - Resume este documento                        │
│  - Escribe email                                │
│  - Analiza gráfico                              │
│                                                  │
│  Nueva tarea                                    │
│                                                  │
│  [Expandibles: Descripción, Context...]         │
└──────────────────────────────────────────────────┘
```

**Lo que está pasando técnicamente:**
- ✅ Tareas guardadas en proyecto
- ✅ Contexto del proyecto existe

**Lo que usuario VE:**
- ❌ Lista de tareas sin histórico
- ❌ No sé cuál se ejecutó y cuál no
- ❌ No veo resultados de tareas ejecutadas
- ❌ No hay "qué cambió" o "dónde estamos"

**Por qué no basta:**
- Project view es "esqueleto" (tareas), no "workspace" (trabajo + resultados)
- No hay señal de "qué pasó aquí"

---

## 3. QUÉ CAMBIOS VISIBLES PROPONGO

### Cambio 1: Resultado es un "asset" guardado y visible

**HOY:**
```
[Resultado]
[Copiar] [Otra tarea] [Ver proyecto]
→ Desaparece
```

**PROPUESTO:**
```
[Resultado]

📌 Guardado automáticamente
   Proyecto: Mi primer proyecto
   Tarea: Resume este documento

[✅ Copiar resultado]
[📂 Ver en proyecto]
[🔄 Reutilizar]

Continuidad: "Puedes volver a este resultado en proyecto"
```

**Cambios visuales:**
- ✅ Aviso claro de guardado ("Guardado automáticamente")
- ✅ Contexto visible (proyecto, tarea)
- ✅ CTAs conectan con proyecto/tarea (no desconectadas)
- ✅ Señal de que existe continuidad

---

### Cambio 2: Home muestra "qué pasó hoy" no solo "qué existe"

**HOY:**
```
Trabajo en progreso:     [Grid de tareas]
Mis proyectos:          [Grid de proyectos]
```

**PROPUESTO:**
```
Hoy:
  ✅ Resume este documento     (ejecutado 10 min ago)
  ✅ Escribe email             (ejecutado 1 hora ago)

Trabajo en progreso:
  📌 Analiza gráfico           (sin ejecutar, en Mi primer proyecto)

Mis proyectos:
  📁 Mi primer proyecto        (3 tareas, 2 ejecutadas)
```

**Cambios visuales:**
- ✅ Sección "Hoy" muestra lo que pasó (resultados ejecutados)
- ✅ Badges de estado (✅ ejecutado, 📌 pendiente)
- ✅ Timestamps ("hace 10 min")
- ✅ Contexto claro de dónde pertenece

---

### Cambio 3: Dentro del proyecto, resultados son visibles

**HOY:**
```
Proyecto: Mi primer proyecto
Tareas:
  - Resume este documento
  - Escribe email
  - Analiza gráfico
```

**PROPUESTO:**
```
Proyecto: Mi primer proyecto    [3 tareas, 2 resultados]

Tareas ejecutadas:
  ✅ Resume este documento      [Resultado disponible]
  ✅ Escribe email              [Resultado disponible]

Tareas pendientes:
  📌 Analiza gráfico            [No ejecutada aún]

[Nueva tarea en este proyecto]
```

**Cambios visuales:**
- ✅ Separación clara: ejecutadas vs pendientes
- ✅ Badges de estado
- ✅ Acceso directo a resultados
- ✅ "Historial" visible del proyecto

---

### Cambio 4: Resultado es "reutilizable"

**HOY:**
```
[Resultado]
[Copiar] [Otra tarea] [Ver proyecto]
```

**PROPUESTO:**
```
[Resultado]

Guardado en:
  📂 Mi primer proyecto
  📌 Resume este documento

Puedes:
  ✅ Copiar resultado
  📂 Ver en proyecto (volver a este resultado después)
  🔄 Reutilizar en otra tarea (pasar como contexto)
  🎯 Basarse en esta propuesta (crear tarea similar)
```

**Cambios visuales:**
- ✅ Cada acción es clara y conecta con algo
- ✅ "Reutilizar" como concepto principal
- ✅ Resultado es "asset" persistente, no temporal

---

### Cambio 5: Continuidad post-resultado es clara

**HOY:**
```
[Resultado]
[Copiar] [Otra tarea] [Ver proyecto]
→ User piensa: "¿Qué hago ahora?"
```

**PROPUESTO:**
```
[Resultado]

Siguiente paso natural:
  - Refinar esta respuesta (editar en proyecto)
  - Usar en otra tarea (pasar como contexto)
  - Crear tarea relacionada (basarse en esto)
  - O volver a Home (ver qué más hay)

[CTA Primario: Ver en proyecto]
```

**Cambios visuales:**
- ✅ Sugiere próximas acciones claras
- ✅ Usuario no se siente "perdido" después
- ✅ Continuidad natural hacia siguiente paso

---

## 4. QUÉ ENTIDADES O ZONAS DEL PRODUCTO TOCARÍAS

### Zonas que cambian (visuales):

```
1. display_onboarding_result()
   - Añade sección "Guardado automáticamente"
   - Añade contexto (proyecto, tarea)
   - Reorganiza CTAs para que conecten visualmente

2. home_view()
   - Añade sección "Hoy" (historial del día)
   - Reorganiza grids con badges de estado
   - Añade timestamps "hace X minutos"

3. project_view() - sección de tareas
   - Separa tareas ejecutadas vs pendientes
   - Muestra resultados disponibles
   - Añade badges de estado

4. new_task_view() o task_detail_view()
   - (Futura) Mostrar histórico de tarea si se reutiliza
   - (Futura) Contexto disponible de ejecutadas anteriores
```

### Entidades que se tocan (visuales, no lógica):

```
✅ Task (tiene estado: ejecutada/pendiente)
✅ ExecutionResult (tiene visibilidad: mostrar en proyecto)
✅ Project (tiene "tareas ejecutadas" vs "pendientes")
✅ Home (tiene concepto de "qué pasó hoy")
```

### Lógica que NO CAMBIA:

```
❌ save_execution_result() - sigue igual
❌ create_task() - sigue igual
❌ ExecutionService - sin cambios
❌ BD schema - sin cambios
❌ router.py - sin cambios
```

---

## 5. QUÉ NO TOCARÍAS

```
❌ Backend de persistencia (BD schema, execute, save)
❌ Router (decisiones eco/racing)
❌ Auth/multiusuario
❌ Analytics o tracking
❌ Preferencias de usuario
❌ Sidebar (aunque pueda verse más "útil")
❌ Onboarding fundamental (solo resultado visible)
❌ Proyecto como CRUD complejo (solo visibilidad)
```

**Principio:** Solo cambios VISUALES y de INFORMACIÓN, no de arquitectura.

---

## 6. CÓMO CONECTAR CON LO YA CONSTRUIDO

### Construcción actual (G1-G4 + Sidebar):

```
onboarding_view()      → Escribe tarea → Resultado → Home
new_task_view()        → Escribe tarea → Resultado → Home
home_view()            → Navega       → Proyecto
project_view()         → Navega tareas
radar_view()           → Explora catálogo
```

### Después de Persistencia Visible:

```
onboarding_view()      → Escribe tarea → Resultado [GUARDADO VISIBLE] → Home
                                         ├─ "Guardado en proyecto X"
                                         └─ "Puedes retomar aquí"

home_view()            → [MUESTRA QUÉ PASÓ HOY]
                         ├─ Sección "Hoy" (resultados recientes)
                         └─ Sección "Proyectos" (con estado)

project_view()         → [SEPARA EJECUTADAS / PENDIENTES]
                         ├─ Tareas ejecutadas (con resultados)
                         └─ Tareas pendientes

new_task_view()        → (Futuro) Puede mostrar contexto
                         de tareas ejecutadas si aplica
```

**Conexión:**
- ✅ No rompe flujo actual
- ✅ Amplía información disponible
- ✅ Home se vuelve más útil
- ✅ Proyecto se vuelve "workspace" no "lista"
- ✅ Resultado se siente persistente

---

## 7. CÓMO VALIDARÍAS QUE PWR YA SE SIENTE COMO WORKSPACE

### Test 1: "¿Dónde quedó mi trabajo?"

**Setup:** Usuario ejecuta tarea en onboarding

```
Usuario entra → ejecuta tarea → ve resultado

Pregunta: "Sin leer instrucciones, ¿dónde está tu trabajo ahora?"

✅ ÉXITO: "Aquí [señala resultado], guardado en ese proyecto"
❌ FALLO: "No sé, desapareció cuando cerré"
```

**Métrica:** User entiende inmediatamente que está guardado

---

### Test 2: "¿Qué hice hoy?"

**Setup:** Usuario vuelve a Home después de ejecutar tareas

```
Usuario entra a Home

Pregunta: "Sin buscar, ¿qué tareas ejecutaste?"

✅ ÉXITO: "Mira, aquí dice 'Hoy: Resume este documento (10 min), Escribe email (1 hora)'"
❌ FALLO: "Tengo que buscar en los grids"
```

**Métrica:** Home muestra historial del día sin buscar

---

### Test 3: "¿Puedo reutilizar esto?"

**Setup:** Usuario ve resultado y quiere usarlo en otra tarea

```
Usuario en resultado

Pregunta: "¿Qué opciones tienes para usar esto en otro lado?"

✅ ÉXITO: "Puedo copiar, usarlo como contexto, o crear tarea basada en esto"
❌ FALLO: "Solo copiar el texto"
```

**Métrica:** Opciones de reutilización son claras y distintas

---

### Test 4: "¿Qué sigue?"

**Setup:** Usuario ejecuta tarea y ve resultado

```
Usuario ve resultado

Pregunta: "¿Qué debería hacer ahora?"

✅ ÉXITO: "Volver a proyecto, refinar, crear tarea relacionada, o explorar"
❌ FALLO: "No sé, copié el texto y quedé aquí"
```

**Métrica:** Siguiente paso natural es obvio

---

### Test 5: "¿Cómo es este proyecto?"

**Setup:** Usuario abre proyecto con algunas tareas ejecutadas

```
Usuario abre proyecto

Pregunta: "¿Qué pasó aquí? ¿Qué está hecho, qué pendiente?"

✅ ÉXITO: "Veo badges: 2 tareas hechas, 1 pendiente. Puedo ver resultados"
❌ FALLO: "Solo veo lista de tareas sin contexto"
```

**Métrica:** Project es "workspace con historia", no "lista"

---

### Test 6: "¿Vuelvo a esto?"

**Setup:** Usuario quiere retomar un resultado anterior

```
Usuario busca un resultado que vio hace días

Pregunta: "¿Dónde está lo que hiciste hace 2 días?"

✅ ÉXITO: "En Home/Hoy veo fecha, click y vuelvo. O en Proyecto veo historial"
❌ FALLO: "No está, desapareció"
```

**Métrica:** Continuidad a través del tiempo es visible

---

### Test 7: Métrica global - "¿Se siente como workspace?"

Pregunta abierta después de usar 20 minutos:

```
"¿Cómo describís PWR?"

✅ ÉXITO:
   - "Espacio donde mi trabajo queda guardado"
   - "Puedo ver lo que hice y retomar"
   - "Siento que tengo una historia de trabajo"

❌ FALLO:
   - "Tool que ejecuta tareas y desaparecen"
   - "No sé si se guardó o no"
   - "Cada tarea es aislada"
```

**Métrica:** Percepción cambió de "herramienta" a "espacio"

---

## STATUS TECH

### Objetivo actual
```
Pasar de "herramienta que ejecuta tareas aisladas"
a "workspace con continuidad real y visible"
```

### Hecho (anteriormente)
```
✅ G1-G3: Flujo principal (onboarding → new_task → home)
✅ G4: Jerarquía visual (INPUT protagonista)
✅ Sidebar: Dinámico (dormido/despierto)
✅ Persistencia técnica: Tareas, resultados, proyectos guardados en BD
```

### En progreso
```
🟡 Este microplan: Definir "persistencia visible"
```

### NO está listo (NO hacer ahora)
```
❌ Implementación
❌ Backend changes
❌ Auth/multiusuario
❌ Dashboard histórico complejo
❌ Analytics
```

### Bloqueos / riesgos
```
⚠️ Bajo: Solo cambios visuales, no lógica
⚠️ Bajo: BD ya guardando datos (no nuevo)
⚠️ Medio: Requiere revisión de "qué datos mostrar dónde"
```

### Siguiente paso recomendado
```
1. Albert aprueba dirección de persistencia visible
2. Se ajusta microplan si feedback
3. Cuando listo para implementar:
   → Abrir plan de implementación específico (H1)
   → Cubrir cambios por vista (resultado, home, proyecto)
   → Validación esperada
```

### Decisión que necesita Albert
```
¿Apruebas esta dirección de persistencia visible?
¿Hay cambios al microplan?
¿Cuándo quieres que detallemos implementación?
```

---

## SÍNTESIS

**Bloque H (Persistencia Visible)** transforma PWR de "herramienta que ejecuta tareas" a "workspace con memoria".

**Cambios visuales propuestos:**
1. Resultado muestra "guardado aquí" automáticamente
2. Home muestra "qué pasó hoy"
3. Proyecto separa ejecutadas/pendientes
4. Resultado es reutilizable (contexto, referencia)
5. Continuidad post-resultado es clara

**Impacto:**
- ✅ Usuario entiende dónde está su trabajo
- ✅ Siente continuidad entre sesiones
- ✅ Proyecto se siente como workspace
- ✅ Home es útil (no solo lista)

**Complejidad:**
- 🟢 Baja: Solo cambios visuales
- 🟢 Sin backend changes necesario
- 🟢 Sin complicaciones de auth/multiusuario

---

**Listo para aprobación y ajustes.**
