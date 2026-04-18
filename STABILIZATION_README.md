# PWR — Estabilización Interna
**Estado: Ready for Internal Test | Fecha: 2026-04-18**

---

## ¿Qué es esto?

PWR (Portable Work Router) en fase de **estabilización**. El objetivo es una app fiable para test de 3-5 días sin crashes, con persistencia clara y sin features nuevas.

---

## Quick Start (Local)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configura GEMINI_API_KEY (opcional, sin ella usa mocks)
export GEMINI_API_KEY="tu_clave_aqui"

# 3. Ejecutar la app
streamlit run app.py

# 4. Abre en browser
# http://localhost:8501
```

---

## Quick Start (Railway)

```bash
# 1. Push a GitHub
git push

# 2. En railway.app:
#    - New Project → Connect GitHub repo
#    - Railway detecta Procfile automáticamente
#    - Deploy

# 3. Configurar env vars en Railway Dashboard:
#    GEMINI_API_KEY=<tu_clave>
#    STREAMLIT_SERVER_HEADLESS=true

# 4. Acceder a URL pública
# https://pwr-xxxx.railway.app
```

---

## Estado Actual ✅

| Componente | Estado | Detalles |
|-----------|--------|---------|
| Código | ✅ Compilable | 4205 líneas, sin errores |
| Database | ✅ Funcional | 7 tablas, 17 proyectos, 19 tareas |
| Router | ✅ Integrado | ExecutionService + DecisionEngine |
| Omni-Input | ✅ Validado | 88ms latencia (imperceptible) |
| Home | ✅ Estable | PWR visible, sin regressions |
| Deployment | ✅ Configurado | Procfile + requirements.txt + Railway setup |
| Persistencia | ✅ Local | ⚠️ Efímera en Railway (OK para test corto) |

---

## Flujo Principal (Testeado)

```
1. Home
   ↓ [Crear proyecto o abrir existente]
2. Proyecto
   ↓ [Crear tarea]
3. Nueva Tarea
   ↓ [Tipear intención]
   ↓ [Ver recomendación inline]
   ↓ [Clickear Ejecutar]
4. Ejecutando...
   ↓ [LLM execution con mock o real]
5. Resultado
   ↓ [Mostrar output]
   ↓ [Opción: Guardar como activo]
6. Volver a Home
   ↓ [Datos intactos en DB]
```

---

## Documentación de Estabilización

- **STATUS_TECH_REAL.md** — Estado técnico completo, checklist validación, riesgos
- **DEPLOYMENT_NOTES.md** — Cómo deployar a Railway, limitaciones de persistencia
- **RELEASE_CHECKLIST.md** — Go/no-go criteria, pasos antes de test real
- **STABILIZATION_README.md** — Este archivo

---

## Limitaciones Conocidas (Aceptadas)

### SQLite en Railway
- ✅ Data persiste entre app restarts (en el mismo dyno)
- ❌ Data se pierde si Railway reinicia dyno (típicamente no pasa en 3-5 días)
- **Mitigación**: Aceptado para test corto. Para producción, migrar a PostgreSQL

### GeminiProvider
- ✅ Funciona si GEMINI_API_KEY está configurada
- ✅ MockEcoProvider funciona sin key (para testing)
- **Si no hay key**: App usa mocks, recomendaciones funcionales pero no reales

### Omni-Input
- ✅ Validado a 88ms promedio (imperceptible)
- ⚠️ Widget sync timing puede variar en Railway
- **Riesgo**: Bajo, pero monitorear en test real

---

## Cómo Validar Estabilidad (Test Real)

### Día 1-2: Smoke Tests
```
[ ] Home carga sin crashes
[ ] Crear proyecto sin crashes
[ ] Crear tarea sin crashes
[ ] Ver recomendación inline
[ ] Ejecutar tarea sin crashes
[ ] Ver resultado sin crashes
[ ] Navegar sin pantallas muertas
```

### Día 3-5: Flujo Real
```
[ ] Trabajo continuo en 1-2 proyectos
[ ] Múltiples tareas ejecutadas
[ ] Sin crashes silenciosos
[ ] Datos persisten (cerrar/abrir browser)
[ ] No hay memory leaks visibles
[ ] Omni-Input se siente responsivo
```

### Éxito = Cero crashes + datos intactos

---

## Si Algo Falla

### App crashes en startup
```
1. Ver logs de Railway (o console local)
2. Verificar: GEMINI_API_KEY configurada o usar mocks
3. Comprobar: requirements.txt instalado
```

### Datos desaparecen
```
1. Revisar: Railway dyno restarted?
   - Timestamp de pwr.db en Railway
2. Si YES: Dyno restart normal, data lost. Aceptado.
3. Si NO: Bug en persistencia, reportar.
```

### Recomendación inline no aparece
```
1. Verificar: Omni-Input en Phase 3 validado
2. Esperar: 2-3s después de escribir
3. Si aún no aparece: Revisar debug_info en código
```

### Crashes silenciosos
```
1. Verificar: st.error() visible en UI
2. Si no: Revisar app.py error handlers (líneas 2303+)
3. Reportar: Error message exacto
```

---

## Roadmap Post-Estabilización (NO HACER AHORA)

- [ ] PostgreSQL para persistencia real
- [ ] Execution history logging
- [ ] Assets persistence testing
- [ ] Multi-user support
- [ ] Authentication
- [ ] Monitoring / alerting
- [ ] Performance profiling

**REGLA**: Si no está en este plan, no se hace hasta test real completado.

---

## Contactos

- **Status**: Ready for internal test
- **Next Step**: Deploy to Railway + validate 3-5 días
- **Bloqueador**: Ninguno conocido
- **Riesgo Principal**: Railway dyno restart (aceptado para test corto)

---

## Checklist Final (ANTES DE TEST REAL)

```
Código
[✅] app.py compila
[✅] router/ carga
[✅] imports resueltos

Database
[✅] Schema válido
[✅] Datos cargan
[✅] Migrations ok

Deployment
[✅] Procfile creado
[✅] requirements.txt completo
[✅] .streamlit/config.toml creado
[✅] railway.json creado
[ ] GEMINI_API_KEY preparada (o confirmado mock)

Before Pushing
[ ] git status limpio
[ ] No secrets en código
[ ] .env.example documentado
[ ] Railway var.env configuradas
```

---

**Estado Final**: ✅ LISTO PARA TEST REAL EN RAILWAY

