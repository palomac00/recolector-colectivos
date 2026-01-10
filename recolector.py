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
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_linea_141():
    driver = setup_driver()
    try:
        # ✅ URL REAL línea 141 Rosario
        driver.get("https://www.colectivosderosario.com.ar/recorrido-linea-141/")
        
        # Espera que cargue la página
        time.sleep(3)
        
        # Busca cualquier tabla de horarios
        tablas = driver.find_elements(By.TAG_NAME, "table")
        print(f"🔍 Encontradas {len(tablas)} tablas")
        
        datos = []
        for tabla in tablas:
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            print(f"Tabla con {len(filas)} filas")
            
            for fila in filas[1:10]:  # Primeras 10 filas para debug
                celdas = fila.find_elements(By.TAG_NAME, "td")
                if len(celdas) >= 3:
                    # ID oculto + datos visibles
                    id_recorrido = celdas[0].get_attribute('data-id') or celdas[0].text.strip() or "ID-UNK"
                    hora_min = celdas[1].text.strip() if len(celdas) > 1 else ""
                    ramal = celdas[2].text.strip() if len(celdas) > 2 else ""
                    
                    if hora_min:
                        datos.append({
                            'ID': id_recorrido,
                            'Hora': hora_min,
                            'Ramal': ramal,
                            'Fecha': datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).strftime('%Y-%m-%d')
                        })
                        print(f"🚌 {id_recorrido} | {hora_min} | {ramal}")
        
        return pd.DataFrame(datos)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return pd.DataFrame()
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
            print(f"✅ Guardado: {filename} ({len(df)} horarios)")
        else:
            print("❌ No se encontraron horarios")
    else:
        print("Usa: python recolector.py --once")

if __name__ == "__main__":
    main()
