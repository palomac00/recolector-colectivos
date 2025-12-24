from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import pytz
import time
import os

# Configurar Chrome headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

# Iniciar driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Ir a la página
    url = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
    print(f"🌐 Cargando {url}")
    driver.get(url)
    time.sleep(3)  # Esperar carga
    
    # Buscar los horarios (ajustá selectores según la página)
    horarios = driver.find_elements(By.CSS_SELECTOR, ".arribo, .schedule-item, [class*='arribo'], [class*='tiempo']")
    
    timestamp = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).strftime('%d/%m/%Y %H:%M:%S')
    
    # Crear TXT
    with open('horarios.txt', 'w', encoding='utf-8') as f:
        f.write(f"Horarios Línea 141 - Parada LP1912\n")
        f.write(f"🕒 {timestamp}\n")
        f.write(f"📊 Encontrados: {len(horarios)} elementos\n")
        f.write("=" * 60 + "\n\n")
        
        if horarios:
            for i, elem in enumerate(horarios[:10], 1):  # Primeros 10
                texto = elem.text.strip()
                f.write(f"{i}. {texto}\n")
        else:
            f.write("No se encontraron horarios\n")
    
    print(f"✅ {len(horarios)} horarios scrapeados y guardados")
    
except Exception as e:
    timestamp = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).strftime('%d/%m/%Y %H:%M:%S')
    with open('horarios.txt', 'w') as f:
        f.write(f"Error: {e}\n{timestamp}\n")
    print(f"❌ Error: {e}")

finally:
    driver.quit()
    print("🏁 Driver cerrado - horarios.txt creado")
