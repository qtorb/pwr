#!/usr/bin/env python3
"""
Mide el tiempo real entre blur del input y aparición de la recomendación inline.

Metodología:
1. T0: User escribe y hace Tab (blur)
2. Medir cada 100ms: ¿aparece recomendación?
3. T1: Primera aparición de recomendación
4. Latencia = T1 - T0
"""
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pathlib import Path

STREAMLIT_URL = "http://localhost:8501"
RESULTS_DIR = Path("/sessions/upbeat-determined-cori/mnt/PWR_repo/timing_results")
RESULTS_DIR.mkdir(exist_ok=True)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 1200)
    return driver

def has_recommendation(driver):
    """Verifica si la recomendación inline está visible"""
    try:
        # Buscar el patrón "🤖 ECO" o "🤖" seguido de modelo
        recs = driver.find_elements(By.XPATH, "//span[contains(text(), 'ECO')] | //strong[contains(text(), 'ECO')]")
        return len(recs) > 0
    except:
        return False

def measure_latency():
    """Mide la latencia entre blur y recomendación visible"""
    driver = None
    measurements = []

    try:
        driver = setup_driver()
        print("\n" + "="*70)
        print("MEDICIÓN DE LATENCIA — Recomendación Inline")
        print("="*70)

        # Navegar a Omni-Input
        print("\n[Setup] Navegando a Omni-Input...")
        driver.get(STREAMLIT_URL)
        time.sleep(3)

        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        abrir = [b for b in all_buttons if "Abrir" in b.text]
        if abrir:
            abrir[0].click()
            time.sleep(3)

        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        nueva = [b for b in all_buttons if "Nueva tarea" in b.text]
        if nueva:
            driver.execute_script("arguments[0].scrollIntoView(true);", nueva[0])
            time.sleep(0.5)
            nueva[0].click()
            time.sleep(3)

        # Test 1: Input pequeño (< 5 chars) - No debe mostrar recomendación
        print("\n[Test 1] Input pequeño (< 5 chars)...")
        ta = driver.find_elements(By.TAG_NAME, "textarea")[0]
        ta.click()
        time.sleep(0.2)
        ta.send_keys("abc")
        time.sleep(0.5)
        ta.send_keys(Keys.TAB)
        time.sleep(3)

        has_rec = has_recommendation(driver)
        print(f"  ¿Recomendación visible? {has_rec}")
        print(f"  ✓ Esperado: NO (menos de 5 chars)")

        # Limpiar para siguiente test
        ta.clear()
        time.sleep(0.5)

        # Test 2: Medir latencia real con input válido
        print("\n[Test 2] Midiendo latencia con input válido...")

        ta.click()
        time.sleep(0.2)

        # Escribir el texto lentamente (simula usuario)
        test_text = "Analizar datos de ventas para Q2 2026"
        print(f"  Escribiendo: '{test_text}'")

        for char in test_text:
            ta.send_keys(char)
            time.sleep(0.08)

        print(f"  Esperando antes de blur: 1s...")
        time.sleep(1)

        # T0: Momento exacto del blur
        print(f"  Haciendo Tab (blur)...")
        t0 = time.time()
        ta.send_keys(Keys.TAB)
        print(f"  T0 (Tab ejecutado): {datetime.fromtimestamp(t0).strftime('%H:%M:%S.%f')[:-3]}")

        # Medir cada 100ms hasta que aparezca la recomendación
        max_wait = 5.0  # 5 segundos máximo
        poll_interval = 0.1  # 100ms entre checks
        checks = []

        while (time.time() - t0) < max_wait:
            elapsed = time.time() - t0

            has_rec = has_recommendation(driver)
            checks.append({
                "elapsed_ms": round(elapsed * 1000),
                "has_recommendation": has_rec
            })

            if has_rec:
                t1 = time.time()
                latency_ms = round((t1 - t0) * 1000)
                print(f"\n  ✓ RECOMENDACIÓN APARECE en T+{latency_ms}ms")

                measurements.append({
                    "test": "input_valido_37chars",
                    "input_length": len(test_text),
                    "latency_ms": latency_ms,
                    "timestamp_start": datetime.fromtimestamp(t0),
                    "timestamp_end": datetime.fromtimestamp(t1),
                    "perceptible": "sí" if latency_ms > 1000 else "no"
                })
                break

            time.sleep(poll_interval)

        if not any(c["has_recommendation"] for c in checks):
            print(f"\n  ✗ TIMEOUT: No aparece recomendación después de {max_wait}s")

        # Captura del estado final
        print(f"\n[Captura] Tomando screenshot...")
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(0.5)
        driver.save_screenshot(str(RESULTS_DIR / "latencia_visual.png"))
        print(f"  💾 Screenshot guardado")

        # Test 3: Medir con input muy largo
        print("\n[Test 3] Midiendo con input largo (100+ chars)...")
        ta.clear()
        time.sleep(0.5)
        ta.click()
        time.sleep(0.2)

        long_text = "Necesito analizar en profundidad los datos de ventas para Q2 2026 incluyendo tendencias mensuales y proyecciones futuras"
        for char in long_text:
            ta.send_keys(char)
            time.sleep(0.05)

        time.sleep(1)
        t0 = time.time()
        ta.send_keys(Keys.TAB)

        while (time.time() - t0) < max_wait:
            if has_recommendation(driver):
                t1 = time.time()
                latency_ms = round((t1 - t0) * 1000)
                print(f"  ✓ Aparece en T+{latency_ms}ms")

                measurements.append({
                    "test": "input_largo_100chars",
                    "input_length": len(long_text),
                    "latency_ms": latency_ms,
                    "timestamp_start": datetime.fromtimestamp(t0),
                    "timestamp_end": datetime.fromtimestamp(t1),
                    "perceptible": "sí" if latency_ms > 1000 else "no"
                })
                break
            time.sleep(0.1)

    finally:
        if driver:
            driver.quit()

    # Reporte
    print("\n" + "="*70)
    print("RESULTADOS DE LATENCIA")
    print("="*70)

    for m in measurements:
        print(f"\n📊 Test: {m['test']}")
        print(f"   Input length: {m['input_length']} chars")
        print(f"   Latencia: {m['latency_ms']}ms")
        print(f"   ¿Perceptible (>1s)? {m['perceptible'].upper()}")
        print(f"   Timestamp: {m['timestamp_start'].strftime('%H:%M:%S.%f')[:-3]} → {m['timestamp_end'].strftime('%H:%M:%S.%f')[:-3]}")

    # Análisis
    if measurements:
        avg_latency = sum(m["latency_ms"] for m in measurements) / len(measurements)
        max_latency = max(m["latency_ms"] for m in measurements)
        min_latency = min(m["latency_ms"] for m in measurements)

        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   Latencia mínima: {min_latency}ms")
        print(f"   Latencia máxima: {max_latency}ms")
        print(f"   Latencia promedio: {round(avg_latency)}ms")

        if max_latency > 2000:
            print(f"\n⚠️ CONCLUSIÓN: Latencia PERCEPTIBLE (>{2000}ms)")
            print(f"   Usuario esperará más de 2s entre blur y recomendación")
            print(f"   → NECESITA feedback visual intermedio")
        elif max_latency > 1000:
            print(f"\n⚡ CONCLUSIÓN: Latencia NOTABLE (~1-2s)")
            print(f"   Recomendado: feedback visual sutil")
        else:
            print(f"\n✅ CONCLUSIÓN: Latencia ACEPTABLE (<1s)")
            print(f"   Feedback visual opcional")

    print("\n" + "="*70)

if __name__ == "__main__":
    measure_latency()
