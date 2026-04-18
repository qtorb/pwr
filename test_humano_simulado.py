#!/usr/bin/env python3
"""
Prueba Selenium MEJORADA simulando interacción humana realista.

Flujo:
1. Focus en el input
2. Write con delays (simulan typing humano)
3. Blur (simula click fuera del input)
4. Wait para que Streamlit complete rerun
5. Expandir DEBUG expander
6. Capturar screenshot
"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

STREAMLIT_URL = "http://localhost:8501"
SCREENSHOT_DIR = Path("/sessions/upbeat-determined-cori/mnt/PWR_repo/screenshots_prueba_humana")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def wait_for_streamlit(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            if requests.get(STREAMLIT_URL, timeout=2).status_code == 200:
                print("✅ Streamlit lista")
                return True
        except:
            pass
        time.sleep(1)
    return False

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 1200)
    return driver

def type_with_delays(element, text, delay_per_char=0.05):
    """Escribe texto con delays para simular typing humano"""
    element.click()
    time.sleep(0.2)

    for char in text:
        element.send_keys(char)
        time.sleep(delay_per_char)

def main():
    if not wait_for_streamlit():
        print("❌ Streamlit no disponible")
        return

    driver = None
    try:
        driver = setup_driver()

        print("\n" + "="*70)
        print("PRUEBA HUMANA SIMULADA — Interacción Realista")
        print("="*70)

        # Paso 1: Ir a home
        print("\n[1] Navegando a home...")
        driver.get(STREAMLIT_URL)
        time.sleep(3)

        # Paso 2: Abrir proyecto
        print("[2] Abriendo primer proyecto...")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        abrir_buttons = [b for b in all_buttons if "Abrir" in b.text]
        if abrir_buttons:
            abrir_buttons[0].click()
            time.sleep(3)

        # Paso 3: Click en "Nueva tarea"
        print("[3] Clickeando 'Nueva tarea'...")
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        nueva_tarea_buttons = [b for b in all_buttons if "Nueva tarea" in b.text]
        if nueva_tarea_buttons:
            driver.execute_script("arguments[0].scrollIntoView(true);", nueva_tarea_buttons[0])
            time.sleep(0.5)
            nueva_tarea_buttons[0].click()
            time.sleep(3)

        # Paso 4: INTERACCIÓN HUMANA REALISTA
        print("[4] Interacción humana en el input...")

        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        input_field = textareas[0] if textareas else None

        if input_field:
            print("   • Focus en input...")
            input_field.click()
            time.sleep(0.3)

            print("   • Escribiendo texto (con delays para simular typing)...")
            text_to_type = "Analizar datos de ventas para Q2 2026"
            type_with_delays(input_field, text_to_type, delay_per_char=0.08)

            input_value = input_field.get_attribute("value")
            print(f"   • Valor en textarea: '{input_value}'")
            print(f"   • Length: {len(input_value)}")

            # Esperar un poco (simula usuario pensando)
            print("   • Esperando 1s (usuario pensando)...")
            time.sleep(1)

            # Blur: simular user saliendo del field (Tab)
            print("   • Blur: Presionando Tab para salir del input...")
            input_field.send_keys(Keys.TAB)
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)

            # Esperar a que Streamlit complete el rerun
            print("   • Esperando a que Streamlit se re-renderice...")
            time.sleep(3)

            # Verificar valor de nuevo
            input_value_after = input_field.get_attribute("value")
            print(f"   • Valor después de blur: '{input_value_after}'")
            print(f"   • ¿Se mantuvo el valor? {'✅ Sí' if input_value_after else '❌ No'}")

        # Paso 5: Expandir DEBUG
        print("\n[5] Expandiendo DEBUG trace...")
        driver.execute_script("window.scrollTo(0, 700);")
        time.sleep(1)

        # Buscar todos los botones y luego el que tenga DEBUG
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"   Botones totales encontrados: {len(all_buttons)}")

        debug_button = None
        for btn in all_buttons:
            btn_text = btn.text.strip() if btn.text else ""
            if "DEBUG" in btn_text:
                debug_button = btn
                print(f"   ✅ Button con DEBUG encontrado: '{btn_text[:50]}'")
                break

        if debug_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", debug_button)
            time.sleep(0.5)
            try:
                debug_button.click()
                print("   ✅ Click en DEBUG button realizado")
            except:
                print("   ⚠️ Click falló, intentando con JavaScript...")
                driver.execute_script("arguments[0].click();", debug_button)
            time.sleep(3)
            print("   ✅ DEBUG trace expandido")
        else:
            print("   ⚠️ Button DEBUG no encontrado. Caputrando igual...")

        # Paso 6: Captura final
        print("\n[6] Capturando screenshot...")
        driver.execute_script("window.scrollTo(0, 400);")
        time.sleep(1)

        screenshot_path = SCREENSHOT_DIR / "prueba_humana_debug_trace.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"   💾 {screenshot_path}")

        print("\n" + "="*70)
        print("✅ PRUEBA COMPLETADA")
        print("="*70)
        print(f"\nRevisa: {screenshot_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
