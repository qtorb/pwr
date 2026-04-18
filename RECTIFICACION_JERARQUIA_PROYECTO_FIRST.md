════════════════════════════════════════════════════════════════════════════════
RECTIFICACIÓN IMPORTANTE: Jerarquía Correcta = PROYECTO FIRST
════════════════════════════════════════════════════════════════════════════════

**Fecha:** 2026-04-18
**Estado:** Documentado para próximas iteraciones
**Impacto:** Crítico para propuestas de header/navegación superior

════════════════════════════════════════════════════════════════════════════════
1. RECTIFICACIÓN IDENTIFICADA
════════════════════════════════════════════════════════════════════════════════

### Secuencia INCORRECTA (que se había propuesto)
```
Tarea → Propuesta → Ejecutar → Resultado
```

Problema: Omite el contexto superior (PROYECTO), lo que hace que cada tarea
parezca aislada y temporal.

### Secuencia CORRECTA (verdadera jerarquía)
```
PROYECTO → Tarea → Propuesta → Ejecutar → Resultado
```

Beneficio: Deja claro el contenedor de trabajo y la continuidad.

════════════════════════════════════════════════════════════════════════════════
2. POR QUÉ PROYECTO ES EL PRIMER ELEMENTO
════════════════════════════════════════════════════════════════════════════════

### Pregunta que debe responder
User abre PWR: "¿Dónde estoy?"

### Respuesta debe ser PROYECTO primero
```
Respuesta correcta: "Estás en [PROYECTO], trabajando en [TAREA]"
Respuesta incorrecta: "Estás en [TAREA]..." (no dice dónde)
```

### 4 Razones por las que Proyecto es Contenedor

| Razón | Antes (sin proyecto visible) | Después (proyecto visible) |
|-------|------------------------------|--------------------------|
| Contexto | "¿Dónde vive esto?" | ✅ "En Proyecto X" |
| Pertenencia | "¿A qué proyecto pertenece?" | ✅ "A Proyecto X" |
| Persistencia | "¿Se guarda?" | ✅ "En Proyecto X, guardado" |
| Continuidad | "¿Por qué vuelvo a ver esto?" | ✅ "Porque está en Proyecto X" |

════════════════════════════════════════════════════════════════════════════════
3. IMPLICACIÓN PARA PRÓXIMOS BLOQUES (I, J, K...)
════════════════════════════════════════════════════════════════════════════════

### Si se diseña un Header Superior (reemplazo para sidebar)

Debe seguir estructura PROYECTO-FIRST:

**Opción 1: Breadcrumb lineal**
```
[Proyecto: Mi Proyecto] > [Tarea: Resume documento] > Propuesta
```

**Opción 2: Línea compacta**
```
Proyecto: Mi Proyecto · Tarea: Resume documento · Paso: Propuesta
```

**Opción 3: Dos líneas jerárquicas**
```
Línea 1: Proyecto · Mi Proyecto
Línea 2: Tarea · Resume documento  |  Paso actual: Propuesta
```

### Lo que NO hacer

❌ Mostrar solo "Resume documento" sin contexto de proyecto
❌ Usar secuencia Tarea → Propuesta → Ejecutar sin Proyecto
❌ Omitir proyecto en navegación superior

════════════════════════════════════════════════════════════════════════════════
4. CRITERIOS DE SOBRIEDAD PARA HEADER SUPERIOR
════════════════════════════════════════════════════════════════════════════════

Cuando se proponga un header/navegación superior, debe cumplir:

### ✅ DEBE cumplir

1. **Incluir PROYECTO primero**
   - Proyecto debe ser el elemento más visible
   - No puede estar escondido o secundario

2. **Ser SOBRIA (no decorativa)**
   - Sin barras de progreso
   - Sin números (1, 2, 3, 4)
   - Sin circles o checkmarks
   - Sin colores excesivos

3. **Dar contexto claro**
   - "Estoy en [Proyecto]"
   - "Trabajando en [Tarea]"
   - Nada de ambigüedad

4. **Aclarar paso actual**
   - "Estoy en el paso: [Propuesta/Ejecutar/Resultado]"
   - No puede ser confuso cuál es el estado

5. **Hacer obvio el siguiente paso**
   - Botón principal que muestra qué sigue
   - No requiere pensar qué hacer después

### ❌ NO debe tener

- Barra de pasos numerada (1. 2. 3. 4.)
- Indicadores visuales de progreso (barras, porcentajes)
- Elementos decorativos (líneas, íconos sin propósito)
- Animaciones o transiciones complejas
- Más de 2-3 líneas de altura

════════════════════════════════════════════════════════════════════════════════
5. CÓMO ESTA RECTIFICACIÓN AFECTA BLOQUE H
════════════════════════════════════════════════════════════════════════════════

### Bloque H (actual): Persistencia Visible

**Implementado:** ✅ Correctamente

```
PROYECTO (visible en display_onboarding_result): ✅ "En: Mi proyecto"
TAREA (visible): ✅ "Tarea: Resume documento"
```

Bloque H YA SIGUE la secuencia correcta. El bloque "Guardado en" muestra:
```
✅ Guardado
En: **Mi primer proyecto**     ← PROYECTO visible
Tarea: **Resume documento**    ← TAREA visible
```

### Próximos Bloques (I, J, K...)

Cuando se diseñe navegación superior/header, RECORDAR esta rectificación
para asegurar que PROYECTO siempre aparece primero.

════════════════════════════════════════════════════════════════════════════════
6. EJEMPLO DE APLICACIÓN FUTURA
════════════════════════════════════════════════════════════════════════════════

### Si se propone: "Header superior para reemplazar sidebar dormida"

**Propuesta INCORRECTA (evitar):**
```
┌─────────────────────────────────────────────────────────┐
│ PWR > Resume documento > Propuesta > Ejecutar > Resultado│
└─────────────────────────────────────────────────────────┘
```
❌ Omite PROYECTO

**Propuesta CORRECTA (aceptable):**
```
┌─────────────────────────────────────────────────────────┐
│ Mi Proyecto > Resume documento > Propuesta              │
└─────────────────────────────────────────────────────────┘
```
✅ PROYECTO es el primer elemento visible
✅ Sobrio (sin números, sin decoración)
✅ Aclara contexto y paso actual
✅ Hace obvio qué sigue (Ejecutar es el botón primario)

════════════════════════════════════════════════════════════════════════════════
7. VALIDACIÓN CHECKLIST PARA FUTURAS PROPUESTAS
════════════════════════════════════════════════════════════════════════════════

Cuando se proponga una nueva navegación/header superior:

```
[ ] ¿Aparece PROYECTO como primer elemento?
[ ] ¿Aparece TAREA como segundo elemento?
[ ] ¿Es la propuesta SOBRIA (sin decoración)?
[ ] ¿Se entiende en qué paso se está?
[ ] ¿Queda claro cuál es el siguiente paso?
[ ] ¿Ocupa menos de 3 líneas de altura?
[ ] ¿No usa números (1, 2, 3)?
[ ] ¿No usa barras de progreso?
```

Si responde NO a alguno de los primeros 5, volver a diseñar.

════════════════════════════════════════════════════════════════════════════════
8. RESUMEN EJECUTIVO
════════════════════════════════════════════════════════════════════════════════

**Rectificación:** La jerarquía correcta de PWR es:
```
PROYECTO → Tarea → Propuesta → Ejecutar → Resultado
```

**Por qué:** PROYECTO es el contenedor de trabajo, debe ser visible primero
para dar contexto, claridad, y continuidad.

**Aplicación:** Esta rectificación debe estar en mente en cualquier propuesta
futura de header, navegación superior, o reorganización de la jerarquía visual.

**Bloque H:** Implementado correctamente (muestra PROYECTO en "Guardado en")

**Próximos bloques:** Recordar esta rectificación al diseñar.

════════════════════════════════════════════════════════════════════════════════
