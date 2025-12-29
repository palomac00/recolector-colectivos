from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pytz
import re
import time
import pandas as pd
import os

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
        horarios.append({
            'Fecha': ahora.strftime('%d/%m/%Y'),
            'Hora_Scrap': ahora.strftime('%H:%M:%S'),
            'Hora_Llegada': hora,
            'Línea': nombre_linea,
            'Minutos': mins,
            'Parada': nombre_parada
        })

    return horarios

def cargar_excel_existente():
    """Carga datos existentes del Excel o crea vacío"""
    if os.path.exists('horarios-141-completo.xlsx'):
        try:
            excel_existente = pd.ExcelFile('horarios-141-completo.xlsx')
            # Cargar todas las hojas
            datos = {}
            for sheet in excel_existente.sheet_names:
                if sheet in ['LP1912', 'LP1912-215', '6203-6173']:
                    df = pd.read_excel(excel_existente, sheet_name=sheet)
                    datos[sheet] = df
            return datos
        except:
            print("⚠️ Excel corrupto, creo nuevo")
    
    # Si no existe o está corrupto
    return {
        'LP1912': pd.DataFrame(),
        'LP1912-215': pd.DataFrame(),
        '6203-6173': pd.DataFrame()
    }

def guardar_excel_completo(horarios_lp1912_nuevos, horarios_combinadas_nuevos):
    """Agrega NUEVOS horarios al Excel existente"""
    datos_existentes = cargar_excel_existente()
    ahora = datetime.now(TZ_AR)
    
    # LP1912 - TODOS (agregar nuevos)
    df_lp1912 = pd.concat([datos_existentes['LP1912'], pd.DataFrame(horarios_lp1912_nuevos)], ignore_index=True)
    
    # LP1912 - SOLO 215 (agregar solo nuevos 215)
    nuevos_215 = [h for h in horarios_lp1912_nuevos if '215' in h['Línea']]
    df_215 = pd.concat([datos_existentes['LP1912-215'], pd.DataFrame(nuevos_215)], ignore_index=True)
    
    # Combinadas (agregar nuevos)
    df_combinadas = pd.concat([datos_existentes['6203-6173'], pd.DataFrame(horarios_combinadas_nuevos)], ignore_index=True)
    
    with pd.ExcelWriter('horarios-141-completo.xlsx', engine='openpyxl') as writer:
        # Escribir hojas actualizadas
        df_lp1912.to_excel(writer, sheet_name='LP1912', index=False)
        df_215.to_excel(writer, sheet_name='LP1912-215', index=False)
        df_combinadas.to_excel(writer, sheet_name='6203-6173', index=False)
        
        # Formato títulos
        workbook = writer.book
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet['A1'] = f'LÍNEA 141 - {sheet_name}'
            worksheet['A2'] = f'Última actualización: {ahora.strftime("%d/%m/%Y %H:%M:%S")}'
            worksheet['A3'] = f'Total filas: {len(writer.sheets[sheet_name])}'

    print(f"✅ Excel actualizado: {len(horarios_lp1912_nuevos)} nuevos LP1912, {len(nuevos_215)} nuevos 215, {len(horarios_combinadas_nuevos)} combinadas")

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Scrapear LP1912
        horarios_lp1912 = scrape_parada(driver, "LP1912", PARADAS_INDIVIDUALES[0][1])
        guardar_lp1912_txt(horarios_lp1912)

        # Scrapear combinadas
        horarios_combinadas = []
        for nombre, url in PARADAS_COMBINADAS:
            horarios = scrape_parada(driver, nombre, url)
            horarios_combinadas.extend(horarios)
        guardar_combinadas_txt(horarios_combinadas)

        # ACTUALIZAR Excel consolidado (agrega sin borrar)
        guardar_excel_completo(horarios_lp1912, horarios_combinadas)

    finally:
        driver.quit()

def guardar_lp1912_txt(horarios):
    ahora = datetime.now(TZ_AR)
    horarios.sort(key=lambda x: x['Hora_Llegada'])

    with open("horarios-LP1912.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - Parada LP1912 (HOY)\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"📊 {len(horarios)} horarios\n\n")
        for i, h in enumerate(horarios, 1):
            f.write(f"{i:2d}. {h['Hora_Llegada']} - {h['Línea']} ({h['Minutos']}min)\n")

    horarios_215 = [h for h in horarios if '215' in h['Línea']]
    with open("horarios-215-LP1912.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - Parada LP1912 (solo 215 - HOY)\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"📊 {len(horarios_215)} horarios 215\n\n")
        for i, h in enumerate(horarios_215, 1):
            f.write(f"{i:2d}. {h['Hora_Llegada']} - {h['Línea']} ({h['Minutos']}min)\n")

def guardar_combinadas_txt(horarios):
    ahora = datetime.now(TZ_AR)
    horarios.sort(key=lambda x: x['Hora_Llegada'])

    with open("horarios-6203-6173.txt", "w", encoding="utf-8") as f:
        f.write(f"🚌 LÍNEA 141 - L6203 + L6173 (HOY)\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"📊 {len(horarios)} horarios\n\n")
        for i, h in enumerate(horarios, 1):
            f.write(f"{i:2d}. {h['Hora_Llegada']} - {h['Línea']} ({h['Minutos']}min) @ {h['Parada']}\n")

if __name__ == "__main__":
    main()
