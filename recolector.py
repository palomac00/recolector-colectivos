from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pytz
import re
import time

# Configurar Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(options=chrome_options)
tz_ar = pytz.timezone('America/Argentina/Buenos_Aires')

def minutos_a_horario(minutos_str):
    """Convierte '3 min. aprox.' → '10:23'"""
    try:
        mins = int(re.search(r'(\d+)', minutos_str).group(1))
        ahora = datetime.now(tz_ar)
        futuro = ahora + timedelta(minutes=mins)
        return futuro.strftime('%H:%M')
    except:
        return minutos_str  # Si falla, mantener original

try:
    url = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
    driver.get(url)
    time.sleep(5)
    
    # Buscar TODOS los elementos de horarios
    elementos = driver.find_elements(By.CSS_SELECTOR, "div, span, p")
    horarios_raw = []
    
    for elem in elementos:
        texto = elem.text.strip()
        if re.search(r'min\.', texto) and len(texto) < 50:
            horarios_raw.append(texto)
    
    # Filtrar únicos y calcular horarios exactos
    horarios_unicos = []
    vistos = set()
    ahora = datetime.now(tz_ar)
    timestamp = ahora.strftime('%d/%m/%Y %H:%M:%S')
    
    for texto in horarios_raw:
        if texto not in vistos:
            horarios_unicos.append(texto)
            vistos.add(texto)
    
    # Crear TXT con horarios EXACTOS
    with open('horarios.txt', 'w', encoding='utf-8') as f:
        f.write(f"🚌 LÍNEA 141 - Parada LP1912\n")
        f.write(f"📅 {timestamp} (Horarios estimados)\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"{'#':<2} {'Horario':<6} {'Línea':<20} {'Minutos'}\n")
        f.write("-" * 60 + "\n")
        
        for i, linea in enumerate(horarios_unicos[:45], 1):
            horario_exacto = minutos_a_horario(linea)
            minutos = re.search(r'(\d+)', linea).group(1) if re.search(r'(\d+)', linea) else "N/A"
            nombre_linea = linea.split('min')[0].strip()
            
            f.write(f"{i:<2}. {horario_exacto:<6} {nombre_linea:<20} {minutos}min\n")
    
    print(f"✅ {len(horarios_unicos)} horarios EXACTOS guardados")
    
except Exception as e:
    with open('horarios.txt', 'w') as f:
        f.write(f"Error: {e}\n{timestamp}\n")
    print(f"❌ Error: {e}")

finally:
    driver.quit()
