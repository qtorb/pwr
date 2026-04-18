# HOME - ONBOARDING + VERSIÓN AUSTERA

**Status**: ✅ Dos estados implementados

---

## Arquitectura de Dos Estados

```
┌─────────────────────────────────────────┐
│  ¿Hay actividad?                        │
│  (tareas ejecutadas O proyectos)        │
└─────────┬───────────────────────────────┘
          │
    ┌─────┴─────┐
    │           │
   SÍ          NO
    │           │
    v           v
 VERSIÓN    ONBOARDING
 AUSTERA    (GUIADO)
```

---

## ESTADO 1: SIN ACTIVIDAD (ONBOARDING)

Cuando el usuario es **completamente nuevo** (sin tareas ni proyectos):

### Estructura

```
┌─────────────────────────────────────────────┐
│  Trabaja mejor con IA, sin caos             │
│  Captura tareas, el sistema decide...       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Capturar tarea                              │
│ ┌───────────────────────────────────────┐   │
│ │ Ej: resume este documento • escribe   │   │
│ │ un email • analiza este texto...      │   │
│ └───────────────────────────────────────┘   │
│                                             │
│ El sistema elegirá el mejor modelo auto.    │
│                                             │
│ ┌─────────────────────┬──────────────────┐  │
│ │ 📝 Probar ejemplo   │ Capturar         │  │
│ └─────────────────────┴──────────────────┘  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Cómo funciona                               │
│                                             │
│ 1. Analizamos 🔍      2. Elegimos 🎯        │
│    Tu tarea entra        El mejor modelo     │
│                                             │
│ 3. Obtienes ✨                              │
│    Resultado editable                       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Proyectos                                   │
│ No tienes proyectos todavía. Tu primera     │
│ tarea creará uno automáticamente.           │
└─────────────────────────────────────────────┘
```

### Componentes

1. **Títulos Grandes**
   - Título: "Trabaja mejor con IA, sin caos"
   - Subtítulo: "Captura tareas, el sistema decide..."
   - Comunican propuesta de valor en 5 segundos

2. **Input Principal**
   - Placeholder con ejemplos: "Ej: resume... • escribe... • analiza..."
   - Caption: "El sistema elegirá el mejor modelo automáticamente"
   - Foco en claridad, no en complejidad

3. **Botón Ejemplo**
   - "📝 Probar con un ejemplo"
   - Rellena el input con una tarea de ejemplo aleatoria
   - NO ejecuta, solo sugiere para que vea cómo es

4. **Botón Capturar**
   - CTA principal, al lado del botón ejemplo
   - Al clickear sin proyecto:
     - Crea automáticamente "Mi primer proyecto"
     - Redirige al proyecto
   - Usuario no ve complejidad de proyectos

5. **Micro-guía** (3 columnas)
   - "1. Analizamos 🔍" → "Tu tarea entra al sistema"
   - "2. Elegimos 🎯" → "El mejor modelo para cada tipo"
   - "3. Obtienes ✨" → "Resultado editable y reutilizable"
   - Explica el flujo sin complejidad

6. **Proyectos Vacío**
   - Simple caption: "No tienes proyectos todavía..."
   - No muestra UI vacía
   - Tranquiliza que es normal

### Comportamiento

```
Usuario nuevo abre PWR
    ↓
Ve página de onboarding
    ↓
Opción A: Clickea "Probar ejemplo"
    → Input se llena con tarea random
    ↓
Opción B: Escribe su propia tarea
    ↓
Clickea "Capturar"
    → Crea proyecto default automático
    → Redirige a proyecto
    → Usuario captura tarea en proyecto
    ↓
Próxima vez que abre PWR
    → Tiene actividad (proyecto existe)
    → Ve versión austera normal
```

---

## ESTADO 2: CON ACTIVIDAD (VERSIÓN AUSTERA)

Cuando el usuario **tiene tareas o proyectos** (sesiones posteriores):

Igual a la versión anterior:
- Capturar (línea única)
- Continuar Trabajo (lista compacta)
- Proyectos Recientes (tarjetas)

La detección es automática: si hay al menos 1 tarea ejecutada O al menos 1 proyecto, muestra versión austera.

---

## Lógica de Detección

```python
# En home_view()
recent_tasks = get_recent_executed_tasks(limit=1)  # Solo chequea si existe 1
projects = get_projects()  # Obtiene todos

has_activity = len(recent_tasks) > 0 or len(projects) > 0

if not has_activity:
    # Mostrar onboarding
    # ... código onboarding ...
    return  # Termina aquí

# El resto es versión austera
# ... código versión austera ...
```

---

## Cambios Técnicos Mínimos

### Agregado
- ✅ Lógica de detección de actividad
- ✅ Onboarding UI (solo Streamlit nativo)
- ✅ Botón "Probar ejemplo" que rellena input
- ✅ Auto-creación de proyecto al capturar sin proyecto

### No Agregado
- ❌ Nuevas tablas en BD
- ❌ Nuevas funciones auxiliares (usa las existentes)
- ❌ HTML crudo
- ❌ Modales
- ❌ Lógica compleja

---

## User Journey Completo

### Primer uso
```
1. Usuario nuevo abre PWR
   ↓
2. Ve onboarding
   - Lee propuesta: "Trabaja mejor con IA..."
   - Ve ejemplo de tarea
   - Entiende flujo 1-2-3
   ↓
3. Opción A: Prueba con ejemplo
   - Input se llena automáticamente
   - Lee cómo funciona
   - Presume "Capturar"
   ↓
4. Opción B: Escribe su tarea
   - Presuma "Capturar"
   ↓
5. Sistema crea proyecto default
   - Redirecciona a proyecto
   - Usuario captura tarea ahí
   ↓
6. Tarea se ejecuta (con Router)
   - Genera resultado
   ↓
7. Próxima vez que abre PWR
   - Ha actividad (proyecto + tarea ejecutada)
   - Ve versión austera
```

### Uso posterior
```
1. Usuario con actividad abre PWR
   ↓
2. Ve versión austera
   - Captura rápida
   - Continuar trabajo reciente
   - Proyectos frecuentes
   ↓
3. Flujo normal de uso
```

---

## Criterios de Éxito

✓ **Claridad en <10 segundos**: Usuario nuevo lee los títulos y entiende qué es PWR
✓ **Guidance**: Pasos 1-2-3 explican el flujo sin complejidad
✓ **Sin fricción**: Botón ejemplo + auto-proyecto = experiencia suave
✓ **Escalabilidad**: Usuario con actividad no ve onboarding (versión austera rápida)
✓ **Austeridad**: Solo Streamlit, sin HTML, sin modales, sin UI innecesaria

---

## Testing Checklist

- [ ] Usuario nuevo ve onboarding
- [ ] Botón "Probar ejemplo" rellena input (aleatorio)
- [ ] Input vacío → botón "Capturar" deshabilitado
- [ ] Capturar sin proyecto → crea "Mi primer proyecto" automático
- [ ] Después de capturar → redirecciona a proyecto
- [ ] Usuario con proyectos ve versión austera
- [ ] Versión austera NO muestra onboarding
- [ ] Todos los botones funcionan (no HTML alerts)
- [ ] Responsive en móvil

---

**Onboarding + Versión Austera integrados y listos**
