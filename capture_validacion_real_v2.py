#!/usr/bin/env python3
"""
Captura REAL de 3 pantallas validando:
1. Home con PWR visible
2. Omni-Input con recomendación inline
3. Layout de proyecto estable

Mejorado: mejor timing, viewport mayor, validación en HTML antes de capturar
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
SCREENSHOT_DIR = Path("/sessions/upbeat-determined-cori/mnt/PWR_repo/screenshots_validation_v2")
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

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 1200)  # Viewport grande
    return driver

def capture_home_with_pwr(driver):
    """Captura 1: Home con PWR visible"""
    print("\n[1/3] Capturando Home con PWR...")

    driver.get(STREAMLIT_URL)
    time.sleep(3)  # Espera a que cargue

    # Scroll al top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Validar que PWR existe en HTML
    try:
        pwr_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'PWR')]"))
        )
        print("  ✅ PWR encontrado en HTML")
    except:
        print("  ⚠️ PWR no encontrado en HTML")

    # Capturar
    screenshot_path = SCREENSHOT_DIR / "1_HOME_PWR_COMPLETO.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"  💾 {screenshot_path}")

    # Validar visibilidad en viewport
    try:
        pwr = driver.find_element(By.XPATH, "//*[contains(text(), 'PWR')]")
        location = pwr.location
        size = pwr.size
        print(f"  📍 PWR ubicación: x={location['x']}, y={location['y']}, width={size['width']}, height={size['height']}")
        if location['y'] > 100:
            print("  ⚠️ PWR está muy abajo en viewport (y > 100)")
        else:
            print("  ✅ PWR está en la región visible")
    except:
        print("  ⚠️ No se pudo verificar ubicación de PWR")

    return screenshot_path

def capture_omni_input_with_recommendation(driver):
    """Captura 2: Omni-Input con recomendación compacta"""
    print("\n[2/3] Capturando Omni-Input con recomendación...")

    # Navegar a proyecto (si es necesario)
    # Streamlit debería estar en Home. Buscamos el botón para ir a Omni-Input
    try:
        # Esperar que cargue la página
        time.sleep(2)

        # Buscar "Nuevo" o "Crear tarea"
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Nuevo') or contains(text(), 'nuevo') or contains(text(), 'Crear')]")
        if buttons:
            print(f"  📌 Encontrados {len(buttons)} botones. Haciendo click en el primero...")
            buttons[0].click()
            time.sleep(2)
        else:
            print("  ⚠️ No se encontró botón Nuevo/Crear, asumiendo que estamos en Omni-Input")
    except Exception as e:
        print(f"  ⚠️ Error al navegar: {e}")

    # Scroll al top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Buscar input de título
    try:
        inputs = driver.find_elements(By.TAG_NAME, "input")
        if inputs:
            print(f"  📌 Encontrados {len(inputs)} inputs. Escribiendo en el primero...")
            input_field = inputs[0]
            input_field.clear()
            input_field.send_keys("Analizar datos de ventas para Q2")
            time.sleep(2)

            # La recomendación debería aparecer al escribir
            # Buscar emoji 🤖 o "ECO" o "RACING"
            try:
                recommendation = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '🤖') or contains(text(), 'ECO') or contains(text(), 'RACING')]"))
                )
                print("  ✅ Recomendación encontrada en HTML")
            except:
                print("  ⚠️ Recomendación NO encontrada en HTML (decision_engine falló)")
        else:
            print("  ⚠️ No se encontraron inputs")
    except Exception as e:
        print(f"  ⚠️ Error al escribir: {e}")

    time.sleep(1)

    # Capturar
    screenshot_path = SCREENSHOT_DIR / "2_RECOMENDACION_COMPACTA.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"  💾 {screenshot_path}")

    return screenshot_path

def capture_proyecto_layout(driver):
    """Captura 3: Layout de proyecto estable"""
    print("\n[3/3] Capturando layout de proyecto...")

    # Si estamos en Omni-Input, esperar a que haya proyecto en sidebar
    time.sleep(1)

    # Buscar elementos del layout 2-columnas (sidebar + main)
    try:
        # Buscar columnas
        layout_elements = driver.find_elements(By.XPATH, "//div[@data-testid='stColumn']")
        print(f"  📌 Encontradas {len(layout_elements)} columnas")

        # Buscar "Proyecto" o proyecto actual
        proyecto_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Proyecto') or contains(text(), 'proyecto')]")
        if proyecto_elements:
            print(f"  ✅ Proyecto encontrado en {len(proyecto_elements)} elementos")
    except:
        pass

    # Scroll para ver el layout completo
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(1)

    # Capturar
    screenshot_path = SCREENSHOT_DIR / "3_LAYOUT_PROYECTO_FLUIDO.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"  💾 {screenshot_path}")

    return screenshot_path

def main():
    if not wait_for_streamlit():
        print("❌ No se pudo conectar a Streamlit")
        return

    driver = None
    try:
        driver = setup_driver()

        print("=" * 60)
        print("CAPTURA DE VALIDACIÓN REAL v2")
        print("=" * 60)

        # Captura 1: Home
        cap1 = capture_home_with_pwr(driver)

        # Captura 2: Omni-Input
        cap2 = capture_omni_input_with_recommendation(driver)

        # Captura 3: Proyecto
        cap3 = capture_proyecto_layout(driver)

        print("\n" + "=" * 60)
        print("✅ CAPTURAS COMPLETADAS")
        print("=" * 60)
        print(f"1. {cap1}")
        print(f"2. {cap2}")
        print(f"3. {cap3}")
        print("\nRevisar imágenes en: " + str(SCREENSHOT_DIR))

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
