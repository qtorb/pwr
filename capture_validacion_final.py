#!/usr/bin/env python3
"""
Captura FINAL: Screenshot de Omni-Input con debug trace visible.

Flujo correcto:
1. Home (PWR visible)
2. Abrire proyecto → sidebar con "➕ Nueva tarea"
3. Click "➕ Nueva tarea" → Omni-Input view
4. Escribir texto en input
5. Capturar con debug expander visible
"""
import time
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

# Configuración
STREAMLIT_URL = "http://localhost:8501"
SCREENSHOT_DIR = Path("/sessions/upbeat-determined-cori/mnt/PWR_repo/screenshots_validation_final")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def wait_for_streamlit(timeout=30):
    """Espera a que Streamlit esté lista"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(STREAMLIT_URL, timeout=2)
            if resp.status_code == 200:
                print("✅ Streamlit lista")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ Streamlit no respondió")
    return False

def setup_driver():
    """Configura Selenium con viewport grande"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-background-networking")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 1200)
    return driver

def capture_1_home_with_pwr(driver):
    """Captura 1: Home con PWR visible"""
    print("\n[1/3] Capturando Home con PWR...")

    driver.get(STREAMLIT_URL)
    time.sleep(3)

    # Scroll al top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Validar que PWR existe
    try:
        pwr_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'PWR')]"))
        )
        print("  ✅ PWR encontrado en HTML")
    except:
        print("  ⚠️ PWR no encontrado en HTML")

    # Capturar
    screenshot_path = SCREENSHOT_DIR / "1_HOME_PWR_VISIBLE.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"  💾 {screenshot_path}")

    return screenshot_path

def capture_2_omni_input_with_debug(driver):
    """Captura 2: Omni-Input con debug trace visible"""
    print("\n[2/3] Navegando a Omni-Input...")

    # Paso 1: Estamos en home. Buscar un proyecto y hacerle click
    print("  📌 Buscando proyecto en home...")

    try:
        # Scroll down para ver proyectos
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Buscar botones "Abrir" de los proyectos - intentar varias estrategias
        project_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Abrir')]")

        if not project_buttons:
            print("  ⚠️ Primer intento sin botones. Scrolleando y esperando...")
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            project_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Abrir')]")

        if not project_buttons:
            print("  ⚠️ Intento 2 sin botones. Buscando todos los botones...")
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"  DEBUG: Encontrados {len(all_buttons)} botones totales")

            # Mostrar el texto de algunos botones para debugging
            for i, btn in enumerate(all_buttons[:10]):
                btn_text = btn.text.strip()
                print(f"    Botón {i}: {btn_text[:50]}")

            # Buscar buttons que contengan "Abrir"
            project_buttons = [b for b in all_buttons if "Abrir" in b.text]
            print(f"  DEBUG: {len(project_buttons)} botones contienen 'Abrir'")

        if not project_buttons:
            print("  ❌ No hay proyectos disponibles. Creando uno primero...")
            # Intentar click en el botón "+ Nuevo" para crear un proyecto
            new_proj_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Nuevo')]")
            new_proj_btn.click()
            time.sleep(3)
            return None

        # Click en el primer botón "Abrir" (primer proyecto)
        print(f"  📌 Encontrados {len(project_buttons)} proyectos. Abriendo primero...")
        project_buttons[0].click()
        time.sleep(3)

    except Exception as e:
        print(f"  ❌ Error al abrir proyecto: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Paso 2: Ahora estamos en proyecto view. Buscar botón "➕ Nueva tarea"
    print("  📌 Buscando botón 'Nueva tarea' en sidebar...")

    try:
        # Esperar a que la página se cargue completamente
        time.sleep(2)

        # Debug: mostrar todos los botones disponibles
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"  DEBUG: {len(all_buttons)} botones en proyecto view")
        buttons_with_text = [(i, b.text.strip()) for i, b in enumerate(all_buttons) if b.text.strip()]
        for i, text in buttons_with_text[:15]:
            print(f"    Botón {i}: {text[:50]}")

        # Buscar específicamente el botón "Nueva tarea"
        nueva_tarea_buttons = [b for b in all_buttons if "Nueva tarea" in b.text]
        print(f"  DEBUG: {len(nueva_tarea_buttons)} botones contienen 'Nueva tarea'")

        if not nueva_tarea_buttons:
            print("  ⚠️ Botón 'Nueva tarea' no encontrado. Buscando alternativas...")
            # Buscar otros botones que podrían ser el de nueva tarea
            alt_buttons = [b for b in all_buttons if "tarea" in b.text.lower() or "new" in b.text.lower()]
            print(f"  DEBUG: {len(alt_buttons)} botones alternativos")
            for i, b in enumerate(alt_buttons[:5]):
                print(f"    Alt {i}: {b.text.strip()}")

        if nueva_tarea_buttons:
            new_task_btn = nueva_tarea_buttons[0]
            print("  ✅ Botón 'Nueva tarea' encontrado")
            # Scroll para ver el botón
            driver.execute_script("arguments[0].scrollIntoView(true);", new_task_btn)
            time.sleep(1)
            new_task_btn.click()
            time.sleep(3)
        else:
            print("  ❌ No se pudo encontrar botón 'Nueva tarea'")
            return None

    except Exception as e:
        print(f"  ❌ Error al hacer click en 'Nueva tarea': {e}")
        import traceback
        traceback.print_exc()
        return None

    # Paso 3: Estamos en Omni-Input. Escribir en el input principal
    print("  📌 Escribiendo en input principal...")

    try:
        # Scroll al top para ver el input
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # Debug: buscar todos los textareas
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"  DEBUG: {len(textareas)} textareas encontrados")
        for i, ta in enumerate(textareas):
            placeholder = ta.get_attribute("placeholder") or ""
            print(f"    Textarea {i}: placeholder='{placeholder[:60]}'")

        # Buscar textarea con placeholder "¿Qué necesitas que haga PWR?"
        input_field = None
        for ta in textareas:
            placeholder = ta.get_attribute("placeholder") or ""
            if "¿Qué necesitas" in placeholder or "PWR" in placeholder:
                input_field = ta
                break

        if not input_field:
            print("  ⚠️ No encontrado por placeholder exacto. Usando el primer textarea...")
            if textareas:
                input_field = textareas[0]
            else:
                print("  ❌ No hay textareas en la página")
                return None

        print("  ✅ Input encontrado")

        # Scroll para ver el input
        driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
        time.sleep(1)

        # Escribir texto
        input_field.clear()
        input_field.send_keys("Analizar datos de ventas para Q2 2026")
        time.sleep(1)

        # Verificar que el texto se escribió
        input_value = input_field.get_attribute("value")
        print(f"  Verificación: valor actual del input = '{input_value}'")

        if not input_value or len(input_value) < 5:
            print(f"  ⚠️ El input no tiene el texto esperado. Reintentando...")
            # Click en el input para asegurar focus
            input_field.click()
            time.sleep(0.5)
            # Clear y escribir de nuevo
            input_field.clear()
            time.sleep(0.5)
            input_field.send_keys("Analizar datos de ventas para Q2 2026")
            time.sleep(1)
            input_value = input_field.get_attribute("value")
            print(f"  Reintento: valor actual del input = '{input_value}'")

        time.sleep(2)  # Esperar a que se procese la entrada y se genere la recomendación

    except Exception as e:
        print(f"  ❌ Error al escribir en input: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Paso 4: Expandir el debug expander
    print("  📌 Expandiendo debug trace...")

    try:
        # Scroll down mucho más para ver el debug expander
        for scroll_amount in [300, 500, 700, 1000]:
            driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
            time.sleep(0.5)

        time.sleep(1)

        # Estrategia 1: Buscar elementos que contengan "DEBUG"
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'DEBUG')]")
        print(f"  DEBUG: {len(all_elements)} elementos contienen 'DEBUG'")

        if all_elements:
            debug_elem = all_elements[0]
            print(f"    Elemento encontrado: tag={debug_elem.tag_name}")

            # Intentar hacer click en el elemento DEBUG o su parent
            try:
                # Buscar el parent button más cercano
                parent_button = driver.execute_script("""
                    var elem = arguments[0];
                    while (elem && elem.tagName !== 'BUTTON') {
                        elem = elem.parentElement;
                    }
                    return elem;
                """, debug_elem)

                if parent_button:
                    print("  ✅ Parent button encontrado. Clickeando...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", parent_button)
                    time.sleep(0.5)
                    parent_button.click()
                    time.sleep(2)
                    print("  ✅ Debug expander expandido via parent button")
                else:
                    print("  ⚠️ No parent button. Clickeando elemento directo...")
                    driver.execute_script("arguments[0].click();", debug_elem)
                    time.sleep(2)
                    print("  ✅ DEBUG elemento clickeado")
            except Exception as e2:
                print(f"  ⚠️ Error al clickear parent: {e2}")
        else:
            print("  ⚠️ No se encontraron elementos con 'DEBUG'")
    except Exception as e:
        print(f"  ⚠️ Error al expandir debug: {e}")
        import traceback
        traceback.print_exc()

    # Paso 5: Capturar screenshot con debug visible
    print("  📌 Capturando screenshot con debug trace...")

    # Scroll para mostrar el input y el debug expander expandido
    time.sleep(1)

    # Primero screenshot mostrando el input con texto
    driver.execute_script("window.scrollTo(0, 100);")
    time.sleep(0.5)
    screenshot_input = SCREENSHOT_DIR / "2a_OMNI_INPUT_CON_TEXTO.png"
    driver.save_screenshot(str(screenshot_input))
    print(f"  💾 Input visible: {screenshot_input}")

    # Luego screenshot mostrando el debug trace
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(1)
    screenshot_debug = SCREENSHOT_DIR / "2b_OMNI_DEBUG_TRACE_EXPANDED.png"
    driver.save_screenshot(str(screenshot_debug))
    print(f"  💾 Debug trace: {screenshot_debug}")

    return screenshot_debug

def main():
    if not wait_for_streamlit():
        print("❌ No se pudo conectar a Streamlit")
        return

    driver = None
    try:
        driver = setup_driver()

        print("=" * 70)
        print("CAPTURA VALIDACIÓN FINAL: Omni-Input con DEBUG TRACE")
        print("=" * 70)

        # Captura 1: Home
        cap1 = capture_1_home_with_pwr(driver)

        # Captura 2: Omni-Input con debug
        cap2 = capture_2_omni_input_with_debug(driver)

        print("\n" + "=" * 70)
        print("✅ CAPTURAS COMPLETADAS")
        print("=" * 70)
        if cap1:
            print(f"1. Home: {cap1}")
        if cap2:
            print(f"2. Omni-Input: {cap2}")
        print(f"\nRevisar imágenes en: {SCREENSHOT_DIR}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
