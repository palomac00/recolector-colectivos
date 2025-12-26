from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pytz
import re
import time

# URL de la parada LP1912 de la 141
URL = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

def minutos(texto: str):
    """Extrae los minutos de '22 min. aprox.' → 22"""
    m = re.search(r'(\d+)\s*min', texto)
    return int(m.group(1)) if m else None

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(URL)
        time.sleep(5)  # esperar que cargue todo

        # Cada colectivo está en un bloque: <div class="mdl-grid proximo-arribo">
        tarjetas = driver.find_elements(By.CSS_SELECTOR, "div.mdl-grid.proximo-arribo")

        ahora = datetime.now(TZ_AR)
        horarios = []

        for card in tarjetas:
            try:
                nombre_linea = card.find_element(
                    By.CSS_SELECTOR, "div.bandera h5"
                ).text.strip()
                texto_tiempo = card.find_element(
                    By.CSS_SELECTOR, "div.tiempo-arribo div"
                ).text.strip()
            except Exception:
                continue

            mins = minutos(texto_tiempo)
            if mins is None:
                continue

            hora = (ahora + timedelta(minutes=mins)).strftime("%H:%M")
            horarios.append((hora, nombre_linea, mins))

        # Ordenar por hora
        horarios.sort(key=lambda x: x[0])

        # Escribir archivo de salida
        with open("horarios.txt", "w", encoding="utf-8") as f:
            f.write("🚌 LÍNEA 141 - Parada LP1912\n")
            f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"📊 {len(horarios)} horarios válidos\n")
            f.write("=" * 50 + "\n\n")
            for i, (h, linea, mins) in enumerate(horarios, 1):
                f.write(f"{i:2d}. {h} - {linea} ({mins}min)\n")

        print("✅ horarios.txt generado correctamente")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
