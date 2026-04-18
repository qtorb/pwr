# Configuración PWR Router v1 + Gemini 2.5 para Windows

**Guía completa paso a paso para Windows (sin asumir experiencia con terminal)**

---

## Índice

1. [Requisitos previos](#requisitos-previos)
2. [Paso 1: Obtener API Key de Gemini](#paso-1-obtener-api-key-de-gemini)
3. [Paso 2: Descargar y preparar PWR](#paso-2-descargar-y-preparar-pwr)
4. [Paso 3: Instalar Python (si no lo tienes)](#paso-3-instalar-python-si-no-lo-tienes)
5. [Paso 4: Instalar dependencias Python](#paso-4-instalar-dependencias-python)
6. [Paso 5: Configurar variable de entorno GEMINI_API_KEY](#paso-5-configurar-variable-de-entorno-gemini_api_key)
7. [Paso 6: Validar configuración](#paso-6-validar-configuración)
8. [Paso 7: Ejecutar la app](#paso-7-ejecutar-la-app)
9. [Troubleshooting](#troubleshooting)

---

## Requisitos previos

- **Windows 10 o superior** (cualquier versión)
- **Conexión a internet** (para Gemini API)
- **Bloc de notas o editor de texto** (para editar .env)
- **Navegador web** (Chrome, Firefox, Edge, etc.)

---

## Paso 1: Obtener API Key de Gemini

### 1.1 Abrir navegador

1. Abre tu navegador favorito
2. Ve a: https://aistudio.google.com/app/apikey

### 1.2 Crear API Key

1. Si te pide login, usa tu cuenta Google (o crea una)
2. Click en botón azul **"Create API Key"**
3. Selecciona el proyecto (usa el que sugiera)
4. Click en **"Create API key in new project"**

### 1.3 Copiar la clave

1. Verás una clave larga en la pantalla (ej: `AIzaSy...`)
2. **IMPORTANTE**: Copia esa clave exactamente como aparece
3. Guárdala en un archivo de texto temporal (la usarás en próximos pasos)

⚠️ **No compartas esta clave con nadie**

---

## Paso 2: Descargar y preparar PWR

### 2.1 Abrir carpeta del proyecto

1. Abre **Explorador de archivos** (presiona `Windows + E`)
2. Navega a dónde está el proyecto PWR (ej: `C:\Users\tuusuario\Documentos\PWR_repo`)
3. Mantén esta ventana abierta

### 2.2 Preparar archivo .env

1. En la carpeta PWR, verás un archivo `.env.example`
2. **Click derecho** en `.env.example`
3. Selecciona **"Copiar"**
4. **Click derecho** en la carpeta vacía
5. Selecciona **"Pegar"**
6. Aparecerá una copia llamada `.env.example - copia`
7. **Click derecho** en esa copia
8. Selecciona **"Cambiar nombre"**
9. Cambia el nombre a: `.env` (solo eso, sin `.example`)

**Resultado**: Ahora tienes un archivo `.env` en la carpeta PWR.

### 2.3 Editar .env con tu clave

1. **Click derecho** en el archivo `.env`
2. Selecciona **"Abrir con..."** → **"Bloc de notas"** (o tu editor favorito)
3. Verás algo como:
   ```
   GEMINI_API_KEY=your-key-here
   ```
4. **Borra** `your-key-here`
5. **Pega** tu clave de Gemini que copiaste antes
6. Resultado final:
   ```
   GEMINI_API_KEY=AIzaSy_xxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
7. **Ctrl+S** para guardar
8. Cierra el editor

✅ **Listo**: Tu .env está configurado

---

## Paso 3: Instalar Python (si no lo tienes)

### 3.1 Verificar si tienes Python

1. Presiona **Windows + R**
2. Escribe: `cmd`
3. Presiona **Enter** (se abrirá terminal negra)
4. Escribe: `python --version`
5. Presiona **Enter**

**Si ves algo como** `Python 3.10.5`: **Saltar a [Paso 4](#paso-4-instalar-dependencias-python)**

**Si ves error**: Necesitas instalar Python. Continúa abajo.

### 3.2 Descargar Python

1. Abre navegador y ve a: https://www.python.org/downloads/
2. Click en botón **"Download Python 3.11"** (o la versión más nueva)
3. Espera a que descargue el archivo `.exe`

### 3.3 Instalar Python

1. Abre la carpeta de Descargas
2. Doble click en el archivo `python-3.xx.exe`
3. **IMPORTANTE**: Marca la casilla **"Add python.exe to PATH"** (abajo a la izquierda)
4. Click en **"Install Now"**
5. Espera a que termine
6. Click en **"Close"**

### 3.4 Verificar instalación

1. Presiona **Windows + R**
2. Escribe: `cmd`
3. Presiona **Enter**
4. Escribe: `python --version`
5. Presiona **Enter**

**Resultado esperado**: `Python 3.11.x` o similar ✅

---

## Paso 4: Instalar dependencias Python

### 4.1 Abrir terminal en la carpeta PWR

1. Abre la carpeta PWR en Explorador de archivos
2. En la barra de dirección (arriba), haz **click derecho**
3. Selecciona **"Copiar dirección como texto"**
4. Presiona **Windows + R**
5. Escribe: `cmd`
6. Presiona **Enter**
7. En la terminal, escribe: `cd ` (con espacio al final)
8. **Click derecho** y **"Pegar"** (se pega la ruta)
9. Presiona **Enter**

**Deberías ver**:
```
C:\Users\tuusuario\ruta\a\PWR_repo>
```

### 4.2 Instalar paquetes

En la terminal, escribe estos comandos uno por uno, presionando **Enter** después de cada uno:

```cmd
pip install google-genai
```

**Espera a que termine**, luego:

```cmd
pip install python-dotenv
```

**Espera a que termine**, luego:

```cmd
pip install streamlit
```

**Espera a que termine**

**Resultado esperado**: Sin errores en rojo, solo mensajes de instalación.

---

## Paso 5: Configurar variable de entorno GEMINI_API_KEY

**Opción A: Usar .env (Recomendado - ya está hecho en Paso 2)**

Si completaste el Paso 2.3 correctamente, ya está configurado.

**Opción B: Variable de entorno del sistema (más permanente)**

### 5.1 Abrir variables de entorno

1. Presiona **Windows + R**
2. Escribe: `sysdm.cpl`
3. Presiona **Enter**
4. Click en pestaña **"Opciones avanzadas"**
5. Click en botón **"Variables de entorno"** (abajo a la derecha)

### 5.2 Crear variable

1. En la ventana que se abre, click en **"Nueva..."** (en la sección inferior "Variables de usuario")
2. **Nombre de la variable**: `GEMINI_API_KEY`
3. **Valor de la variable**: pega tu clave de Gemini
4. Click **"Aceptar"**
5. Click **"Aceptar"** de nuevo
6. Click **"Aceptar"** una última vez

### 5.3 Reiniciar para aplicar cambios

1. **Reinicia tu computadora** (los cambios de variables de entorno requieren reinicio)

O alternativa: Cierra y reabre todas las ventanas de terminal.

---

## Paso 6: Validar configuración

### 6.1 Abrir terminal en PWR

1. Presiona **Windows + R**
2. Escribe: `cmd`
3. Presiona **Enter**
4. Navega a carpeta PWR (como en Paso 4.1)

### 6.2 Ejecutar validación

Escribe:

```cmd
python validate_setup.py
```

Presiona **Enter**

### 6.3 Leer resultado

**Si todo está bien, verás**:
```
✅ GeminiProvider importable
✅ GeminiProvider inicializado (API key válida)
✓ Modelo gemini-2.5-flash-lite (eco) disponible
✓ Modelo gemini-2.5-pro (racing) disponible
```

**Si ves error**:
- "GEMINI_API_KEY no configurada" → Revisa Paso 5
- "google-genai no está instalado" → Revisa Paso 4.2
- Otros errores → Ve a [Troubleshooting](#troubleshooting)

---

## Paso 7: Ejecutar la app

### 7.1 Desde terminal

1. En terminal (en carpeta PWR), escribe:

```cmd
streamlit run app.py
```

Presiona **Enter**

### 7.2 Esperar

La terminal mostrará:
```
Collecting usage statistics...
You can disable this...
You can now view your app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://XXX.XXX.X.XXX:8501
```

### 7.3 Abrir navegador

1. Se abrirá automáticamente en tu navegador
2. Si no, abre tu navegador y ve a: `http://localhost:8501`

### 7.4 Usar la app

1. Click en **"Crear Proyecto"** o usa uno existente
2. Crea una tarea (ej: "¿Qué es Python?")
3. Click en **"Ejecutar con Router"**
4. Espera unos segundos (Gemini responde en tiempo real)
5. ¡Verás la respuesta real de Gemini!

---

## Troubleshooting

### Problema: "GEMINI_API_KEY no configurada"

**Solución**:

1. Verifica que `.env` existe en la carpeta PWR
2. Abre `.env` con bloc de notas
3. Verifica que la clave está ahí: `GEMINI_API_KEY=AIzaSy...`
4. Guarda el archivo
5. Cierra y reabre la terminal
6. Intenta de nuevo

### Problema: "google-genai no está instalado"

**Solución**:

```cmd
pip install google-genai
```

Espera a que termine e intenta de nuevo.

### Problema: "Python no reconocido"

**Solución**:

1. Presiona **Windows + R**
2. Escribe: `sysdm.cpl`
3. Click en **"Variables de entorno"**
4. En **"Variables de usuario"**, click **"Nueva..."**
5. Nombre: `Path`
6. Valor: `C:\Users\TUUSUARIO\AppData\Local\Programs\Python\Python311\Scripts` (reemplaza TUUSUARIO)
7. Click **"Aceptar"**
8. Reinicia terminal

### Problema: "No se puede conectar con Gemini API"

**Soluciones en orden**:

1. Verifica tu conexión a internet
2. Verifica que la API key es correcta (sin espacios extra)
3. Regenera la clave en https://aistudio.google.com/app/apikey
4. Reemplaza en `.env` y guarda
5. Cierra y reabre terminal

### Problema: Streamlit abre pero la app carga lentamente

**Normal**: La primera ejecución puede tomar 30 segundos. Espera.

### Problema: "Modelo no disponible"

**Solución**:

La clave está bien pero el modelo `gemini-2.5-pro` o `gemini-2.5-flash-lite` no está disponible en tu región. Esto es raro pero puede pasar.

1. Intenta primero una tarea simple (ECO)
2. Si ECO funciona pero RACING no: contáctanos

### Problema: Quiero parar la app

**Solución**:

En la terminal donde corre streamlit, presiona: **Ctrl+C**

---

## Checklist Final

- ✅ Python 3.10+ instalado
- ✅ google-genai, python-dotenv, streamlit instalados
- ✅ .env existe en carpeta PWR
- ✅ .env contiene GEMINI_API_KEY=tu-clave-real
- ✅ validate_setup.py muestra todo ✅
- ✅ `streamlit run app.py` abre la app
- ✅ Puedo crear proyectos y tareas
- ✅ Puedo ejecutar tareas con Gemini real

**Si todo está ✅**: ¡Listo para Pruebas de Aceptación!

---

## Próximos pasos

1. Ejecutar [ACCEPTANCE_TESTS_HITO1.md](ACCEPTANCE_TESTS_HITO1.md)
2. Validar que todos los tests pasen
3. Pasar a **Hito 2: Captura de Tokens y Costo Real**

---

**¿Necesitas ayuda?** Revisa SETUP_GEMINI.md para más detalles técnicos.
