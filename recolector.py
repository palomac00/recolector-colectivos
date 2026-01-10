#!/usr/bin/env python3
import os
import sys
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytz

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_linea_141():
    driver = setup_driver()
    try:
        # URL específica de línea 141 (ajusta según tu fuente)
        driver.get("https://tu-app-de-colectivos.com/linea-141")
        
        # Espera tabla horarios
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        tabla = driver.find_element(By.TAG_NAME, "table")
        filas = tabla.find_elements(By.TAG_NAME, "tr")
        
        datos = []
        for fila in filas[1:]:  # Salta header
            celdas = fila.find_elements(By.TAG_NAME, "td")
            if len(celdas) >= 4:
                # CAPTURA ID OCULTO (múltiples métodos)
                id_recorrido = (
                    celdas[0].get_attribute('data-id') or
                    celdas[0].get_attribute('data-recorrido') or
                    celdas[0].get_attribute('id') or
                    celdas[0].get_attribute('title') or
                    celdas[0].text.strip() or "SIN-ID"
                )
                
                hora = celdas[1].text.strip()
                minuto = celdas[2].text.strip()
                ramal = celdas[3].text.strip()
                
                if hora and minuto:
                    datos.append({
                        'ID': id_recorrido,
                        'Hora': f"{hora}:{minuto}",
                        'Ramal': ramal,
                        'Fecha': datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).strftime('%Y-%m-%d')
                    })
                    print(f"🚌 ID:{id_recorrido} | {hora}:{minuto} | {ramal}")
        
        return pd.DataFrame(datos)
        
    finally:
        driver.quit()

def main():
    os.makedirs("data", exist_ok=True)
    
    if "--once" in sys.argv:
        print("🔄 Recolectando horarios línea 141...")
        df = scrape_linea_141()
        
        if not df.empty:
            filename = f"data/horarios-141-{datetime.now().strftime('%Y-%m-%d-%H-%M')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"✅ Guardado: {filename}")
        else:
            print("❌ No se encontraron horarios")
    else:
        print("Usa: python recolector.py --once")

if __name__ == "__main__":
    main()
