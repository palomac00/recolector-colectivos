from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pytz
import re
import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(options=chrome_options)
tz_ar = pytz.timezone('America/Argentina/Buenos_Aires')

def parsear_par(linea_texto, tiempo_texto):
    """Combina línea y tiempo correctamente"""
    linea = re.sub(r'\d+.*min', '', linea_texto).strip()
    minutos = int(re.search(r'(\d+)', tiempo_texto).group(1))
    ahora = datetime.now(tz_ar)
    horario = (ahora + timedelta(minutes=minutos)).strftime('%H:%M')
    return f"{horario} - {linea} ({minutos}min)"

try:
    url = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
    driver.get(url)
    time.sleep(6)  # Esperar carga completa
    
    # Buscar TODOS los textos relevantes
    todos_textos = []
    elementos = driver.find_elements(By.XPATH, "//*[contains(text(), 'min. aprox.') or contains(text(), '_') or contains(text(), 'min')]")
    
    for elem in elementos:
        texto = elem.text.strip()
        if texto and ('min' in texto or '_' in texto) and len(texto) < 30:
            todos_textos.append(texto)
    
    # Agrupar por pares: línea + tiempo
    horarios_limpios = []
    i = 0
    while i < len(todos_textos) - 1:
        linea_cand = todos_textos[i]
        tiempo_cand = todos_textos[i + 1]
        
        if re.search(r'\d+_|\d+X', linea_cand) and re.search(r'min\.', tiempo_cand):
            horarios_limpios.append(parsear_par(linea_cand, tiempo_cand))
            i += 2  # Saltar al siguiente par
        else:
            i += 1
    
    timestamp = datetime.now(tz_ar).strftime('%d/%m/%Y %H:%M:%S')
    
    # Guardar LIMPIO
    with open('horarios.txt', 'w', encoding='utf-8') as f:
        f.write(f"🚌 LÍNEA 141 - Parada LP1912\n")
        f.write(f"📅 {timestamp}\n")
        f.write(f"📊 {len(horarios_limpios)} horarios válidos\n")
        f.write("=" * 50 + "\n\n")
        
        for i, horario in enumerate(horarios_limpios, 1):
            f.write(f"{i:2d}. {horario}\n")
    
    print(f"✅ {len(horarios_limpios)} horarios LIMPIOS guardados")
    
except Exception as e:
    with open('horarios.txt', 'w') as f:
        f.write(f"Error: {e}\n")
    print(f"❌ Error: {e}")

finally:
    driver.quit()
