# Pruebas de Aceptación: Hito 1 - Provider Real Conectado

Estas pruebas **deben pasar** antes de avanzar a Hito 2 (captura de tokens y costo real).

---

## Precondiciones

- ✅ `google-genai` instalado: `pip install google-genai`
- ✅ `python-dotenv` instalado: `pip install python-dotenv`
- ✅ `.env` con `GEMINI_API_KEY=tu-clave-real`
- ✅ `streamlit` instalado: `pip install streamlit`
- ✅ Proyecto en `/mnt/PWR_repo` con estructura correcta

---

## Test 1: Arranque Limpio con Gemini Configurado

**Descripción**: Verificar que la app inicia sin errores y Gemini se valida correctamente.

**Pasos**:

```bash
# 1. Ejecutar validación
python validate_setup.py
```

**Resultado esperado**:
```
1. Verificando estructura de archivos...
   ✅ router/domain.py
   ✅ router/mode_registry.py
   ✅ router/providers.py
   ✅ router/execution_service.py
   ✅ Todos los archivos presentes

2. Verificando GEMINI_API_KEY...
   ✅ GEMINI_API_KEY configurada: xxxx...xxxx

3. Verificando dependencias Python...
   ✅ google-genai
   ✅ streamlit
   ✅ python-dotenv

4. Verificando importabilidad del Router...
   ✅ Router importable

5. Verificando GeminiProvider...
   ✅ GeminiProvider importable
   ✅ GeminiProvider inicializado (API key válida)
   ✓ Modelo gemini-2.5-flash-lite (eco) disponible
   ✓ Modelo gemini-2.5-pro (racing) disponible
```

**Si falla**: Revisa SETUP_WINDOWS.md para configurar GEMINI_API_KEY

---

## Test 2: Ejecución Real End-to-End de una Tarea

**Descripción**: Ejecutar una tarea completa desde UI hasta resultado persistido.

**Pasos**:

### 2.1 Iniciar la app

```bash
streamlit run app.py
```

**Resultado esperado**: Abre navegador en `http://localhost:8501`

### 2.2 Crear proyecto

1. En sidebar: "Crear Proyecto"
2. Nombre: `Test Hito 1`
3. Descripción: `Validación de Hito 1`
4. Guardar

**Resultado esperado**: Proyecto aparece en lista

### 2.3 Crear tarea ECO

1. Click en proyecto `Test Hito 1`
2. En "Captura rápida":
   - **Título**: `Explicar recursión`
   - **Tipo**: `Pensar` (esto dispara ECO automáticamente)
   - **Descripción**: `¿Qué es recursión en programación?`
   - **Contexto**: `Respuesta corta, máximo 200 palabras`
3. Click "Crear tarea"

**Resultado esperado**: Tarea aparece en lista

### 2.4 Ejecutar tarea con Router (ECO)

1. Click en tarea `Explicar recursión`
2. Click "Ejecutar con Router"

**Esperar**: Spinner "El Router está analizando..."

**Resultado esperado**:
- ✅ **Decisión de modelo** muestra: `eco` (modo)
- ✅ **Resultado** muestra texto real de Gemini (no simulado)
- ✅ **Trazabilidad** expande y muestra:
  - Estado: **COMPLETED**
  - Modo: **eco**
  - Modelo: **gemini-2.5-flash-lite**
  - Proveedor: **gemini**
  - Latencia: **XXX ms** (número real, no simulado)
  - Coste estimado: **$0.05**
  - Motivo: razonamiento de decisión

### 2.5 Crear tarea RACING

1. En "Captura rápida":
   - **Título**: `Estrategia de escalado`
   - **Tipo**: `Decidir` (esto dispara RACING automáticamente)
   - **Descripción**: `Cómo escalar una aplicación de Node.js con microservicios`
   - **Contexto**: `Considera: arquitectura, costos, complejidad operativa`
2. Click "Crear tarea"

**Resultado esperado**: Tarea aparece en lista

### 2.6 Ejecutar tarea con Router (RACING)

1. Click en tarea `Estrategia de escalado`
2. Click "Ejecutar con Router"

**Esperar**: Spinner más largo (racing es más profundo)

**Resultado esperado**:
- ✅ **Decisión de modelo** muestra: `racing` (modo)
- ✅ **Resultado** muestra análisis profundo real (no simulado)
- ✅ **Trazabilidad** expande y muestra:
  - Estado: **COMPLETED**
  - Modo: **racing**
  - Modelo: **gemini-2.5-pro**
  - Proveedor: **gemini**
  - Latencia: **XXX ms** (más que ECO)
  - Coste estimado: **$0.30**
  - Motivo: razonamiento estratégico detectado

---

## Test 3: Error Explícito - API Key o Modelo no disponible

**Descripción**: Verificar que los errores se muestran clara y explícitamente.

### 3.1 Error de API Key inválida

**Pasos**:

1. Editar `.env`: cambiar `GEMINI_API_KEY` a valor inválido (ej: `invalid-key-12345`)
2. Parar app: `Ctrl+C`
3. Ejecutar: `python validate_setup.py`

**Resultado esperado**:
```
5. Verificando GeminiProvider...
   ✅ GeminiProvider importable
   ⚠️ GeminiProvider: No se puede conectar con Gemini API: ...
   → GeminiProvider necesita GEMINI_API_KEY configurada
```

4. Intentar ejecutar app: `streamlit run app.py`
5. Crear tarea y click "Ejecutar con Router"

**Resultado esperado**:
- ❌ Mensaje de error en rojo: `Error: No se puede conectar con Gemini API: ...`
- ✅ Trazabilidad muestra: error_code = `invalid_key`, error_message visible
- ✅ Router summary se guarda en BD igual (para auditoría)

**Solución**: Restaurar API key válida en `.env`

### 3.2 Error de modelo no disponible

**Pasos**:

1. En `router/mode_registry.py`, cambiar modelo ECO a inválido:
   ```python
   "eco": ModeConfig(
       mode="eco",
       provider="gemini",
       model="gemini-invalid-model",  # Inválido propósito
       estimated_cost=0.05,
   )
   ```

2. Parar app y validar: `python validate_setup.py`

**Resultado esperado**:
```
⚠️ Modelo gemini-invalid-model (eco) no disponible: ...
```

3. Ejecutar app: `streamlit run app.py`
4. Crear tarea tipo "Pensar" y click "Ejecutar con Router"

**Resultado esperado**:
- ❌ Mensaje de error: `Error: Modelo 'gemini-invalid-model' no encontrado...`
- ✅ error_code = `model_not_found`
- ✅ Trazabilidad muestra el error explícitamente

**Solución**: Restaurar `mode_registry.py` a valores correctos

---

## Test 4: Upgrade ECO → RACING

**Descripción**: Una tarea ECO puede reevaluarse como RACING si se actualiza contexto.

**Pasos**:

### 4.1 Crear tarea que comienza ECO

1. Crear tarea:
   - **Título**: `Revisar código`
   - **Tipo**: `Revisar`
   - **Descripción**: `¿Está bien este código?`
   - **Contexto**: `(vacío)`
2. Ejecutar: automáticamente decide **ECO** (tarea simple)
3. Ver resultado ECO

### 4.2 Actualizar a RACING

1. Editar tarea (click en botón de edición si existe, o copiar/nueva):
   - Mismo título
   - **Tipo**: `Decidir` (esto requiere más análisis)
   - **Descripción**: `¿Debería refactorizar este código? Considerar tiempo, riesgo, beneficio`
   - **Contexto**: `Arquitectura del proyecto: microservicios. Equipo: 3 personas. Deadline: 2 meses.`
2. Crear nueva tarea con estos datos
3. Ejecutar

**Resultado esperado**:
- ✅ Automáticamente decide **RACING** (contexto + complejidad mayor)
- ✅ Modelo: `gemini-2.5-pro` (no flash-lite)
- ✅ Latencia más alta que ECO
- ✅ Coste estimado: $0.30

**Conclusión**: La heurística eco/racing funciona correctamente

---

## Test 5: Persistencia Correcta - Resultado, Trazabilidad y Activo

**Descripción**: Verificar que todo se guarda correctamente en BD.

**Pasos**:

### 5.1 Verificar persistencia de resultado

1. Ejecutar una tarea (ECO o RACING)
2. En DB, verificar que se guardó:
   - `task.llm_output` = salida real de Gemini
   - `task.useful_extract` = primeros 700 chars
   - `task.router_summary` = contiene modo, modelo, latencia, razonamiento

**Para verificar** (si tienes acceso a DB):
```bash
sqlite3 pwr_data/pwr.db "SELECT router_summary FROM tasks WHERE id = 1;"
```

**Resultado esperado**: router_summary contiene toda la info:
```
Modelo recomendado: gemini-2.5-flash-lite
Modo: eco
Proveedor: gemini
Nivel de complejidad: 0.25
Latencia: XXX ms
Coste estimado: $0.05

Motivo:
- Tarea acotada de baja complejidad
```

### 5.2 Verificar trazabilidad en session_state

1. Ejecutar tarea
2. Click "Ver trazabilidad"

**Resultado esperado**: Expander muestra:
- ✅ Estado: COMPLETED
- ✅ Modo: eco/racing
- ✅ Modelo: nombre real
- ✅ Proveedor: gemini
- ✅ Latencia: número en ms
- ✅ Coste estimado: $X.XX
- ✅ Motivo: razonamiento
- ✅ (Si error): error_code y error_message

### 5.3 Crear activo desde resultado

1. Ejecutar tarea
2. En "Resultado", click "Crear activo"

**Resultado esperado**:
- ✅ Nuevo activo aparece en lista "Activos"
- ✅ Contiene el extracto útil (o salida completa)
- ✅ Título: "Activo · [nombre tarea]"
- ✅ En BD: asset está ligado a task y project

**Para verificar**:
```bash
sqlite3 pwr_data/pwr.db "SELECT COUNT(*) FROM assets;"
```

---

## Resumen de Validación

| Test | Descripción | Estado | Notas |
|------|-------------|--------|-------|
| 1 | Arranque limpio + Gemini | ✅ | Validar con `validate_setup.py` |
| 2 | Ejecución E2E (ECO + RACING) | ✅ | Real API, latencia real, output real |
| 3 | Errores explícitos | ✅ | API key inválida, modelo no encontrado |
| 4 | Upgrade ECO → RACING | ✅ | Heurística funciona |
| 5 | Persistencia (resultado, trazabilidad, activo) | ✅ | Todo en BD, todo accesible |

**Cuando todos los tests pasen**: ✅ **Hito 1 VALIDADO**

---

## Siguientes Pasos

Una vez validado Hito 1:
- [ ] Pasar a **Hito 2: Captura de Tokens y Costo Real**
  - Extraer tokens reales de respuesta Gemini
  - Calcular costo real (tokens × precio)
  - Mostrar en white box
  - Persistir en BD

