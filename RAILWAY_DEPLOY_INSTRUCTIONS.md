# RAILWAY DEPLOY — Instrucciones Paso-a-Paso
**Para generar URL pública y validar 5 evidencias**

---

## PREREQUISITOS

✅ Tienes acceso a railway.app
✅ GitHub account conectado a Railway
✅ Git client local
✅ Código PWR en el folder /sessions/upbeat-determined-cori/mnt/PWR_repo

---

## PASO 1: Git Setup Local

```bash
cd /sessions/upbeat-determined-cori/mnt/PWR_repo

# Verificar estado
git status

# Si no es un repo, inicializar
git init
git add .
git commit -m "PWR stabilization: Railway deployment ready"

# Conectar a GitHub remote (si no existe)
# git remote add origin https://github.com/tu-usuario/pwr.git
```

**Qué verificar**:
- [ ] Git repo inicializado
- [ ] Todos los archivos de deployment presentes (Procfile, requirements.txt, etc.)
- [ ] Último commit tiene Procfile + requirements.txt

---

## PASO 2: Push a GitHub

```bash
git push -u origin main
# O la rama que uses
```

**Qué verificar**:
- [ ] Push exitoso
- [ ] GitHub muestra los archivos (especialmente Procfile)

---

## PASO 3: Railway Dashboard Setup

1. Abre https://railway.app/dashboard
2. Click en **New Project**
3. Selecciona **GitHub** → conecta tu repo PWR_repo
4. Railway auto-detecta Procfile
5. Espera a que se configure el servicio

**Qué esperar**:
- Railway dice "Procfile detected"
- Muestra streamlit como servicio

---

## PASO 4: Variables de Entorno

En Railway Dashboard → Variables:

```
GEMINI_API_KEY=tu_clave_aqui
```

**Opciones**:
- ✅ Configura GEMINI_API_KEY real → LLM funciona
- ✅ Deja vacío → MockEcoProvider funciona (para testing)
- ❌ No configurar nada → GeminiProvider falla, pero mock fallback activo

---

## PASO 5: Deploy

1. En Railway: Click **Deploy**
2. Espera logs de build
3. Espera "Build successful"
4. Espera "Deployment successful"

**Logs esperados**:
```
Installing dependencies...
Installing streamlit==1.28.1
Installing google-genai>=0.1.0
Starting Streamlit...
Streamlit app running at...
```

**Tiempo**: 2-3 minutos típicamente

---

## PASO 6: Obtener URL Pública

En Railway Dashboard:
- Copia la **Public URL** (algo como `https://pwr-xxxxx.railway.app`)

**Verificar**:
- [ ] URL es única
- [ ] Empieza con https://
- [ ] Contiene "railway.app"

---

## PASO 7: Validar Deploy (Primeras Evidencias)

### Evidencia 1: URL Pública Funcional
```
URL: https://pwr-xxxxx.railway.app
Status: Abre sin errores de conexión
Captura: Screenshot de URL en browser
```

### Evidencia 2: Home Carga
```
Qué ver:
- Logo/heading "PWR" visible
- Lista de proyectos (17 proyectos cargados)
- Botones: "Nuevo Proyecto", "Abrir", etc.
- NO hay errores rojos en pantalla

Captura: Home screenshot
```

### Evidencia 3: Omni-Input Funciona
```
Pasos:
1. Entra a un proyecto existente
2. Clickea "Nueva tarea"
3. Tipea en input: "Qué es PWR?"
4. Espera 2-3 segundos
5. Ver recomendación inline aparecer (ej: "💭 PWR está analizando...")

Captura: Input con recomendación visible
```

### Evidencia 4: Ejecutar Produce Resultado
```
Pasos:
1. Desde la recomendación, clickea "Ejecutar"
2. Espera spinner "⏳ Ejecutando..."
3. Ver resultado LLM (mock o real)
4. Ver output en pantalla

Captura: Resultado visible (sin errores)
```

### Evidencia 5: Persistencia + Limitación
```
Persistencia TEST:
1. Crea un nuevo proyecto en Railway: "Test XYZ"
2. Recarga la página (F5)
3. ¿El proyecto sigue ahí?
   → SI: ✅ Persistencia funciona (al menos para esta sesión)
   → NO: ❌ Bug crítico

SQLite Ephemeral Clarification:
- En Railway, SQLite persiste entre app restarts EN EL MISMO DYNO
- SI Railway reinicia dyno (redeploy, scaling, etc):
  → Data se pierde completamente
  → Esto es NORMAL en Railway con SQLite
  → Para producción: necesita PostgreSQL

Captura: Proyecto "Test XYZ" visible post-reload

Documento: Etiqueta claramente:
"✅ Persistencia: VÁLIDA PARA TEST CORTO (3-5 días sin dyno restart)
⚠️ Persistencia: NO VÁLIDA para validación de continuidad/recuperación
→ Motivo: SQLite en Railway es efímero
→ Fix real: PostgreSQL (post-test)"
```

---

## SI ALGO FALLA

### "Build failed"
```
1. Ver logs en Railway
2. Buscar error específico
3. Problemas comunes:
   - requirements.txt malformado → revisar
   - Falta Procfile → verificar existe
   - Python version → Railway usa 3.11 por defecto (OK)
```

### "App crashes on startup"
```
1. Ver logs en Railway
2. Si dice "GEMINI_API_KEY": No es crítico, MockEcoProvider activo
3. Si dice "ModuleNotFoundError": requirements.txt incompleto
4. Si dice "Syntax Error": app.py tiene problemas (pero no debería)
```

### "Home no carga / error 500"
```
1. Espera 30s (Railway puede estar iniciando)
2. Recarga página
3. Si persiste: Ver logs en Railway
4. Si ve "StreamlitAppException": Bug en código (reportar)
```

### "Omni-Input no muestra recomendación"
```
1. Espera 3-5 segundos después de escribir
2. Verifica: ¿Escribiste al menos 5 caracteres?
3. Si nada: revisar logs, probablemente MockProvider ejecutando
```

---

## RESULTADO ESPERADO

Después de estos pasos, deberías tener:

✅ URL pública funcional (https://pwr-xxxxx.railway.app)
✅ Home cargando correctamente
✅ Omni-Input mostrando recomendación inline
✅ Ejecutar generando resultado
✅ Persistencia funcionando (con caveats documentados)

**Una vez confirmes estas 5 cosas, toma capturas y pasamos a validar.**

---

## SIGUIENTE PASO

1. Ejecuta este deploy
2. Confirma la URL pública
3. Toma capturas de las 5 evidencias
4. Documenta: "Persistencia válida para test corto (XYZ dyno status)"
5. Comunica: ✅ LISTO PARA TEST REAL

**Tiempo total**: ~10 minutos deploy + 5 minutos validación = 15 minutos

