from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pytz
import re
import time

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

PARADAS_INDIVIDUALES = [
    ("LP1912", "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"),
]

PARADAS_COMBINADAS = [
    ("L6203", "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=L6203"),
    ("L6173", "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=L6173"),
]

def minutos(texto: str):
    m = re.search(r'(\d+)\s*min', texto)
    return int(m.group(1)) if m else None

def scrape_parada(driver, nombre_parada, url):
    driver.get(url)
    time.sleep(5)

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
        horarios.append((hora, nombre_linea, mins, nombre_parada))

    return horarios

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
        # 1. LP1912 - genera 2 archivos (general + solo 215)
        horarios_lp1912 = scrape_parada(driver, "LP1912", PARADAS_INDIVIDUALES[0][1])
        guardar_lp1912(horarios_lp1912)

        # 2. 6203 + 6173 - SOLO 1 archivo combinado
        todos_horarios = []
        for nombre, url in PARADAS_COMBINADAS:
            horarios = scrape_parada(driver, nombre, url)
            todos_horarios.extend(horarios)
        
        guardar_combinadas(todos_horarios)

    finally:
        driver.quit()

def guardar_lp1912(horarios):
    ahora = datetime.now(TZ_AR)
    horarios.sort(key=lambda x: x[0])

    # General LP1912
    with open("horarios-LP1912.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - Parada LP1912\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"📊 {len(horarios)} horarios válidos\n")
        f.write("=" * 50 + "\n\n")
        for i, (h, linea, mins, parada) in enumerate(horarios, 1):
            f.write(f"{i:2d}. {h} - {linea} ({mins}min)\n")

    # Solo 215 LP1912
    horarios_215 = [(h, linea, mins, parada) for (h, linea, mins, parada) in horarios if "215" in linea]
    with open("horarios-215-LP1912.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - Parada LP1912 (solo 215)\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"📊 {len(horarios_215)} horarios de la 215\n")
        f.write("=" * 50 + "\n\n")
        for i, (h, linea, mins, parada) in enumerate(horarios_215, 1):
            f.write(f"{i:2d}. {h} - {linea} ({mins}min)\n")

    print("✅ LP1912: horarios-LP1912.txt + horarios-215-LP1912.txt")

def guardar_combinadas(horarios):
    ahora = datetime.now(TZ_AR)
    horarios.sort(key=lambda x: x[0])

    with open("horarios-6203-6173.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - Paradas L6203 + L6173 (COMBINADO)\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"📊 {len(horarios)} horarios válidos\n")
        f.write("=" * 50 + "\n\n")
        for i, (h, linea, mins, parada) in enumerate(horarios, 1):
            f.write(f"{i:2d}. {h} - {linea} ({mins}min) @ {parada}\n")

    print("✅ Combinadas: horarios-6203-6173.txt")

if __name__ == "__main__":
    main()
