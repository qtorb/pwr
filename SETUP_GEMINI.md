# Configuración de Gemini Provider (google-genai)

El Router v1 usa **Google Gemini** como provider real con el SDK oficial `google-genai`. Aquí cómo configurarlo en **Linux, macOS y Windows**.

## 1. Obtener API Key de Gemini

1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click en "Create API Key"
3. Copia la clave generada (guárdala en un lugar seguro)

---

## 2. Configurar variable de entorno

### Opción A: .env local (recomendado para desarrollo)

**Todos los sistemas:**

```bash
cp .env.example .env
# Edita .env con tu editor favorito y pega tu clave
```

Contenido del archivo `.env`:
```
GEMINI_API_KEY=your-api-key-here
```

**⚠️ Importante**: El archivo `.env` ya está en `.gitignore`, así que no se subirá a git.

### Opción B: Variable de entorno del sistema

#### Linux / macOS

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Para hacerlo permanente, añade la línea anterior a `~/.bashrc` o `~/.zshrc`:

```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.bashrc
# Luego:
source ~/.bashrc
```

#### Windows (CMD)

```cmd
setx GEMINI_API_KEY "your-api-key-here"
```

**Nota**: Debes **reiniciar el símbolo del sistema** después de ejecutar `setx`.

#### Windows (PowerShell)

```powershell
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-api-key-here", "User")
```

**Nota**: Debes **reiniciar PowerShell** después.

#### Windows (Anaconda Prompt / Miniconda)

Si usas Anaconda:

```bash
# Opción 1: Usar .env (recomendado)
cp .env.example .env
# Edita .env

# Opción 2: Variable de entorno en el environment
conda activate pwr
conda env config vars set GEMINI_API_KEY=your-api-key-here
conda deactivate
conda activate pwr  # Reactivar environment
```

---

## 3. Instalar dependencias

### Linux / macOS

```bash
pip install google-genai python-dotenv streamlit
```

### Windows (CMD)

```cmd
pip install google-genai python-dotenv streamlit
```

### Windows (PowerShell)

```powershell
pip install google-genai python-dotenv streamlit
```

### Windows (Anaconda Prompt)

```bash
conda activate pwr
conda install -c conda-forge google-genai python-dotenv
pip install streamlit
```

---

## 4. Verificar configuración

Ejecuta el script de validación:

### Linux / macOS

```bash
python validate_setup.py
```

### Windows (cualquier terminal)

```
python validate_setup.py
```

Este script verifica:
- ✅ Archivos presentes
- ✅ GEMINI_API_KEY configurada
- ✅ Dependencias instaladas
- ✅ Router importable
- ✅ GeminiProvider funcional

---

## 5. Ejecutar la app

### Linux / macOS

```bash
streamlit run app.py
```

### Windows (CMD)

```cmd
streamlit run app.py
```

### Windows (PowerShell)

```powershell
streamlit run app.py
```

### Windows (Anaconda Prompt)

```bash
conda activate pwr
streamlit run app.py
```

La app abrirá en tu navegador en `http://localhost:8501`.

---

## Modelos Disponibles (Gemini 2.5)

| Modo | Modelo | Caso de uso | Costo estimado |
|------|--------|------------|-----------------|
| **eco** | `gemini-2.5-flash-lite` | Tareas rápidas, respuestas cortas | $0.05 por ejecución |
| **racing** | `gemini-2.5-pro` | Análisis profundo, razonamiento complejo | $0.30 por ejecución |

Ambos modelos son **estables en producción** y soportados a largo plazo por Google.

---

## Flujo de Validación (Startup Only)

Cuando inicias la app, el Router realiza estas validaciones **una sola vez**:

1. **API Key**: Verifica que GEMINI_API_KEY está configurada ✓
2. **Conexión API**: Intenta comunicarse con Gemini ✓
3. **Modelos disponibles**: Valida que eco y racing existen ✓

Si algo falla, ves un aviso:
```
⚠️ GeminiProvider no disponible: [error]
```

Luego, cada ejecución NO valida de nuevo (para evitar latencia innecesaria).

---

## Troubleshooting

### Error: "GEMINI_API_KEY no configurada"

**Linux / macOS:**
```bash
# Verificar que está en .env
cat .env | grep GEMINI_API_KEY

# Si usas variable de entorno:
echo $GEMINI_API_KEY
```

**Windows (CMD):**
```cmd
REM Verificar .env
type .env

REM Si usas variable de entorno:
echo %GEMINI_API_KEY%
```

**Windows (PowerShell):**
```powershell
# Verificar .env
Get-Content .env

# Si usas variable de entorno:
$env:GEMINI_API_KEY
```

**Solución:**
- Asegúrate que `.env` existe en la carpeta del proyecto
- Asegúrate que no hay espacios al principio o final de la clave
- Reinicia la app: `streamlit run app.py`

### Error: "google-genai no está instalado"

```bash
pip install google-genai python-dotenv
```

Si estás en Windows con Anaconda:
```bash
conda install -c conda-forge google-genai python-dotenv
```

### Error: "Clave API inválida"

- Regenera una nueva clave en [Google AI Studio](https://aistudio.google.com/app/apikey)
- Reemplaza en `.env` o en tu variable de entorno
- Reinicia la app

### Error: "Modelo no disponible"

Vés esto en startup si algún modelo no está disponible:
```
⚠️ Modelo gemini-2.5-pro (racing) no disponible: ...
```

**Causas:**
- API key sin acceso a ese modelo
- Modelos no disponibles en tu región
- Límites de cuenta alcanzados

**Soluciones:**
- Verifica que tu API key es correcta
- Intenta con otra clave
- Revisa [Google AI Studio](https://aistudio.google.com/app/apikey)

### Error: "Rate limit"

- Gemini tiene límites de llamadas por minuto (QPM)
- Tier gratuito: ~15 QPM
- Espera 1-2 minutos e intenta de nuevo
- La app mostrará el error explícitamente

---

## Costos y Límites

**Tier Gratuito:**
- Primeros 15 solicitudes por minuto (QPM)
- Muy bajo costo

**Tier de Pago:**
- Mayor número de solicitudes
- Costos según [pricing de Google AI](https://ai.google.dev/pricing)

La app muestra el costo estimado en la trazabilidad.

---

## Persistencia de Trazabilidad

Cuando ejecutas una tarea:
- **Éxito**: router_summary, llm_output, extract se guardan en BD ✓
- **Error**: router_summary con error_code y mensaje se guarda en BD ✓
- **Session**: trace en session_state tiene info para UI ✓

Puedes auditar todas las ejecuciones viendo el historial de tareas.

---

## Testing sin Credenciales

Si quieres testear sin Gemini:

1. Comenta la línea de GeminiProvider en `router/execution_service.py`:
   ```python
   # self.providers["gemini"] = GeminiProvider()
   ```

2. Descomentar después de agregar credenciales

El sistema te avisará si Gemini no está disponible pero seguirá funcionando con MockProviders.

---

## Próximos Pasos

- [x] Configurar google-genai
- [x] Validar API key y modelos (startup only)
- [x] Usar Gemini 2.5 (flash-lite + pro)
- [ ] Capturar tokens reales (siguiente hito)
- [ ] Calcular costo real (siguiente hito)
- [ ] Soportar múltiples proveedores (futuro)

---

**¿Problemas?** Revisa `validate_setup.py` para un diagnóstico rápido.
