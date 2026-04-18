# RELEASE CHECKLIST — PWR Estabilización Interna
**Fecha: 2026-04-18 | Versión: Stabilization v1 | Objetivo: Test Real 3-5 días**

---

## GATE: Antes de Test Real

### 1. CÓDIGO COMPILABLE ✅
```
[✅] app.py compila sin errores (4205 líneas)
[✅] router/ módulos cargan correctamente
[✅] imports resueltos
[✅] normalize_row() implementado y funcionando
```

### 2. DATABASE FUNCIONAL ✅
```
[✅] Schema: 7 tablas
[✅] Datos: 17 proyectos, 19 tareas
[✅] Migrations: Automatizadas en startup
[✅] Persistencia local: ✅ Funciona
[✅] Persistencia Railway: ⚠️ Efímera (OK para test corto)
```

### 3. CORE COMPONENTS ✅
```
[✅] ExecutionService: Se inicializa correctamente
[✅] ModelCatalog: Carga BD + fallback a registry
[✅] TaskInput: Se crea sin errors
[✅] DecisionEngine: Integrado en ExecutionService
[✅] Providers: Mock disponible (Gemini requiere API key)
```

### 4. FLUJO PRINCIPAL VALIDADO
```
Home → [buscar/crear proyecto]
    ↓
Proyecto → [crear tarea]
    ↓
Tarea → [escribir intención → ver recomendación inline]
    ↓
Ejecutar → [LLM execution con MockEcoProvider]
    ↓
Resultado → [mostrar output]
    ↓
Guardar (opcional) → [assets table]
    ↓
Volver a Home → [lista actualizada]
```

### 5. DEPLOYMENT READY ✅
```
[✅] Procfile: Creado
[✅] requirements.txt: Completo (streamlit, google-genai)
[✅] .streamlit/config.toml: Creado
[✅] railway.json: Creado
[✅] .env.example: Documentado
```

### 6. CONFIGURACIÓN NECESARIA (antes de Railway deploy)
```
[ ] Preparar GEMINI_API_KEY (o usar mocks)
[ ] Confirmar variables de entorno en Railway
[ ] Tener git repo listo para conectar a Railway
```

### 7. ERRORES CONOCIDOS: NINGUNO BLOQUEADOR
```
[✅] Assets=0: Normal (usuarios no guardaron aún)
[✅] Execution_history=0: Feature no implementada (v2)
[✅] Dual status fields: Sincronizados, no es bug
[✅] Omni-Input timing: Validado en Phase 3 (88ms)
[✅] GeminiProvider: Requiere API key (fallback a mock)
```

---

## RIESGOS CONOCIDOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Railway dyno restart → data loss | Media | Alto | Aceptado para test corto (3-5 días típicamente sin restart) |
| GeminiProvider falla → mock fallback | Baja | Bajo | Mock providers funcionan perfectamente |
| Omni-Input timing varía en Railway | Media | Bajo | Phase 3 validó timing, imperceptible para usuario |
| Session state no persiste reinicio | Normal | Aceptado | Streamlit behavior, no es bug |

---

## CRITERIOS DE ACEPTACIÓN — TEST REAL

### ✅ Éxito = Todos estos funcionan 3-5 días sin crashes

1. **Home carga sin errores**
   - PWR visible
   - Proyectos listados
   - Botones funcionales

2. **Crear proyecto funciona**
   - Nombre guardado en DB
   - Aparece en Home
   - Se puede abrir sin crashes

3. **Crear tarea funciona**
   - Intención se tipea
   - Recomendación inline aparece
   - No hay crashes en input

4. **Ejecutar tarea funciona**
   - Mock LLM ejecuta
   - Output aparece
   - DB se actualiza

5. **Navegar funciona**
   - Home ← → Proyecto ← → Tarea funcionan
   - No hay pantallas muertas
   - Botones responden

6. **Sin crashes silenciosos**
   - Errores visibles en UI si pasan
   - Fallbacks funcionan
   - No hay "tarea no encontrada" silenciosa

7. **Persistencia funciona**
   - Cerrar y reabrir: datos intactos
   - Recargar página: datos intactos
   - (Dyno restart: datos se pierden - aceptado)

---

## CONFIGURACIÓN RAILWAY (Paso a Paso)

### Crear Deploy
1. En railway.app: New Project → GitHub repo
2. Seleccionar PWR_repo
3. Railway auto-detecta Procfile
4. Deploy automático

### Variables de Entorno (Railway Dashboard)
```
GEMINI_API_KEY=<your_key>           # O dejar vacío para usar mocks
STREAMLIT_SERVER_HEADLESS=true      # Requerido
STREAMLIT_SERVER_PORT=8501          # Usar default
```

### Verificar Deploy
1. Esperar Railway Build → Deployment
2. Copiar URL pública
3. Abrir en browser
4. Debe cargar Home

---

## ENTREGABLES OBLIGATORIOS

### 1. STATUS_TECH_REAL.md ✅
- Checklist completo
- Riesgos documentados
- Componentes validados

### 2. DEPLOYMENT_NOTES.md ✅
- Instrucciones Railway
- Limitaciones documentadas
- Persistencia explicada

### 3. Configuración Files ✅
- Procfile
- requirements.txt
- .streamlit/config.toml
- railway.json
- .env.example

### 4. Evidencia Real (POST-DEPLOY)
- URL pública funcional
- Captura Home cargando
- Captura creando tarea
- Captura viendo recomendación
- Captura resultado
- Confirmación: datos persisten tras reinicio

---

## GO / NO-GO DECISION

### GO CRITERIOS
```
[✅] Código compila
[✅] DB funciona
[✅] Flujo principal testeable
[✅] Deployment configurado
[✅] Riesgos conocidos y aceptados
```

### Decisión: ✅ GO PARA TEST REAL

**Estado**: Listo para Railway deployment
**Próximo paso**: Configurar GEMINI_API_KEY y deployar a Railway
**Validación**: 3-5 días de uso real sin redeploy

---

## POST-TEST (No Hacer Ahora)

Cosas que surgirán tras 3-5 días de test real:
- Bugs específicos de Railway (si los hay)
- UX patterns que faltan
- Performance insights
- Data persistence needs

**NO HACER AHORA**: No proponer features, no refactor, no creatividad.
**SI HACER**: Documentar bugs, validar estabilidad, aceptar limitaciones.

