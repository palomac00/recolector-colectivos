#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECOLECTOR LÍNEA 141 - HTML + IDENTIFICADOR COCHE
Archivos en /data/ - GitHub Actions OK
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pytz
import re
import time
import pandas as pd
import os
import argparse
from openpyxl.styles import Font

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')
DATA_DIR = "data"

PARADAS_INDIVIDUALES = [
    ("LP1912", "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"),
]

PARADAS_COMBINADAS = [
    ("L6203", "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=L6203"),
    ("L6173", "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=L6173"),
]

def get_fecha_excel():
    return os.path.join(DATA_DIR, f"horarios-141-{datetime.now(TZ_AR).strftime('%Y-%m-%d')}.xlsx")

def minutos(texto):
    m = re.search(r'(\d+)\s*min', texto)
    return int(m.group(1)) if m else None

def extraer_identificador(card):
    """Busca '217', '211' en toda la card"""
    try:
        # DEBUG: Muestra TODO el texto de la card
        texto_completo = card.text
        print(f"     🔍 DEBUG card: {texto_completo[:200]}...")
        
        # Busca identificadorCoche típico: "217", "211" (3 dígitos)
        numeros_3d = re.findall(r'\b\d{3}\b', texto_completo)
        for num in numeros_3d:
            if int(num) > 100:  # No es hora ni minuto
                print(f"     🎯 IDENTIFICADOR ENCONTRADO: {num}")
                return num
                
        # Buscar en atributos data-*
        elementos = card.find_elements(By.CSS_SELECTOR, "[data-*]")
        for elem in elementos:
            for attr in elem.get_property('attributes').keys():
                if 'data' in attr:
                    valor = elem.get_attribute(attr)
                    if re.search(r'\b\d{3}\b', valor):
                        return valor.strip()
                        
    except Exception as e:
        print(f"     ❌ Debug error: {e}")
    
    return ""

def scrape_parada(driver, nombre_parada, url):
    try:
        print(f"     🌐 Cargando {url}")
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        tarjetas = driver.find_elements(By.CSS_SELECTOR, "div.mdl-grid.proximo-arribo")
        ahora = datetime.now(TZ_AR)
        horarios = []

        print(f"     📱 {len(tarjetas)} tarjetas encontradas")

        for i, card in enumerate(tarjetas[:8], 1):
            try:
                nombre_linea = card.find_element(By.CSS_SELECTOR, "div.bandera h5").text.strip()
                texto_tiempo = card.find_element(By.CSS_SELECTOR, "div.tiempo-arribo div").text.strip()
                
                # IDENTIFICADOR
                identificador = extraer_identificador(card)
                
                mins = minutos(texto_tiempo)
                if "Arribando" in texto_tiempo:
                    mins = 0
                    
                if mins is None or mins > 120:
                    continue

                hora = (ahora + timedelta(minutes=mins)).strftime("%H:%M")
                horarios.append({
                    'Hora_Scrap': ahora.strftime('%H:%M:%S'),
                    'Hora_Llegada': hora,
                    'Línea': nombre_linea,
                    'Minutos': mins,
                    'Parada': nombre_parada,
                    'Identificador': identificador
                })
                
                status = f"#{identificador}" if identificador else "(sin ID)"
                print(f"     ✅ {i}. {hora} {nombre_linea} ({mins}m) {status}")
                
            except Exception as e:
                print(f"     ❌ Tarjeta {i}: {e}")

        return horarios
    except Exception as e:
        print(f"   ❌ Error {nombre_parada}: {e}")
        return []

def cargar_excel_dia():
    archivo_hoy = get_fecha_excel()
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(archivo_hoy):
        return {'LP1912': pd.DataFrame(), 'LP1912-215': pd.DataFrame(), '6203-6173': pd.DataFrame()}
    
    try:
        excel_file = pd.ExcelFile(archivo_hoy)
        datos = {}
        for sheet in ['LP1912', 'LP1912-215', '6203-6173']:
            if sheet in excel_file.sheet_names:
                df = pd.read_excel(archivo_hoy, sheet_name=sheet, skiprows=4)
                if 'Identificador' not in df.columns:
                    df['Identificador'] = ''
                datos[sheet] = df
            else:
                datos[sheet] = pd.DataFrame()
        return datos
    except:
        return {'LP1912': pd.DataFrame(), 'LP1912-215': pd.DataFrame(), '6203-6173': pd.DataFrame()}

def guardar_excel_dia(horarios_lp1912, horarios_combinadas):
    datos = cargar_excel_dia()
    ahora = datetime.now(TZ_AR)
    archivo = get_fecha_excel()
    
    # LP1912 (no 215)
    df_lp1912_nuevos = pd.DataFrame(horarios_lp1912)
    df_lp1912 = pd.concat([datos['LP1912'], df_lp1912_nuevos])
    df_lp1912 = df_lp1912.drop_duplicates(subset=['Hora_Llegada','Línea','Identificador']).reset_index(drop=True)
    
    # 215 separada
    nuevos_215 = [h for h in horarios_lp1912 if '215' in str(h.get('Línea',''))]
    df_215_nuevos = pd.DataFrame(nuevos_215)
    df_215 = pd.concat([datos['LP1912-215'], df_215_nuevos]).drop_duplicates(subset=['Hora_Llegada','Línea','Identificador']).reset_index(drop=True)
    
    # Combinadas
    df_combinadas_nuevos = pd.DataFrame(horarios_combinadas)
    df_combinadas = pd.concat([datos['6203-6173'], df_combinadas_nuevos]).drop_duplicates(subset=['Hora_Llegada','Línea','Parada','Identificador']).reset_index(drop=True)
    
    with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, 'LP1912', index=False, startrow=4)
        df_215.to_excel(writer, 'LP1912-215', index=False, startrow=4)
        df_combinadas.to_excel(writer, '6203-6173', index=False, startrow=4)
        
        for sheet, df in [('LP1912', df_lp1912), ('LP1912-215', df_215), ('6203-6173', df_combinadas)]:
            ws = writer.sheets[sheet]
            ws['A1'] = f'LÍNEA 141 - {sheet} - {ahora.strftime("%d/%m/%Y")}'
            ws['A2'] = f'Actualizado: {ahora.strftime("%H:%M:%S")}'
            ws['A3'] = f'{len(df)} únicos (por Identificador)'
            for row in ws['A1:A3']:
                for cell in row:
                    cell.font = Font(bold=True)

    print(f"💾 {archivo}")
    print(f"   LP1912: {len(df_lp1912)} | 215: {len(df_215)} | Combinadas: {len(df_combinadas)}")

def guardar_txt(horarios, nombre_txt, titulo):
    archivo = os.path.join(DATA_DIR, nombre_txt)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    ahora = datetime.now(TZ_AR)
    horarios_sorted = sorted(horarios, key=lambda x: x['Hora_Llegada'])
    
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(f"🚌 {titulo}\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        for i, h in enumerate(horarios_sorted, 1):
            ident = h.get('Identificador', '')
            f.write(f"{i:2d}. {h['Hora_Llegada']} {h['Línea']:>8} ({h['Minutos']:2}m)")
            if ident: f.write(f" [# {ident}]")
            f.write(f" @ {h['Parada']}\n")

def ciclo_completo(driver):
    ahora = datetime.now(TZ_AR)
    print(f"⏰ {ahora.strftime('%H:%M:%S')} - Recolectando...")
    
    # LP1912
    print("🌐 LP1912...")
    horarios_lp1912 = scrape_parada(driver, "LP1912", PARADAS_INDIVIDUALES[0][1])
    guardar_txt(horarios_lp1912, "horarios-LP1912.txt", "LÍNEA 141 - LP1912")
    
    # Combinadas
    print("🌐 L6203 + L6173...")
    horarios_combinadas = []
    for nombre, url in PARADAS_COMBINADAS:
        horarios = scrape_parada(driver, nombre, url)
        horarios_combinadas.extend(horarios)
    guardar_txt(horarios_combinadas, "horarios-6203-6173.txt", "LÍNEA 141 - L6203+L6173")
    
    if horarios_lp1912 or horarios_combinadas:
        guardar_excel_dia(horarios_lp1912, horarios_combinadas)
    print("✅ Ciclo completo!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(25)
    
    try:
        print("🚀 LÍNEA 141 - HTML + IDENTIFICADOR")
        print(f"📁 Todos los archivos → /{DATA_DIR}/")
        
        if args.once:
            ciclo_completo(driver)
        else:
            while True:
                ciclo_completo(driver)
                print("\n⏳ 15 minutos...\n")
                time.sleep(900)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
