#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECOLECTOR LÍNEA 141 - API JSON OFICIAL 
TODOS los archivos en carpeta /data/
"""

import requests
import os
from datetime import datetime, timedelta
import pytz
import pandas as pd
import argparse
from openpyxl.styles import Font
import re

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

# ¡TODOS los paths en /data/ !
DATA_DIR = "data"

PARADAS_INDIVIDUALES = [
    ("LP1912", "LP1912"),
]

PARADAS_COMBINADAS = [
    ("L6203", "L6203"),
    ("L6173", "L6173"),
]

def get_fecha_excel():
    return os.path.join(DATA_DIR, f"horarios-141-{datetime.now(TZ_AR).strftime('%Y-%m-%d')}.xlsx")

def minutos_from_api(tiempo_texto):
    m = re.search(r'(\d+)\s*min', tiempo_texto, re.IGNORECASE)
    return int(m.group(1)) if m else None

def fetch_arribos(id_parada):
    """API request directo"""
    try:
        url = f"https://cuandollega.smartmovepro.net/nuevedejulio/arribos/api?codLinea=141&idParada={id_parada}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://cuandollega.smartmovepro.net/nuevedejulio/'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get('arribos', [])
    except Exception as e:
        print(f"❌ API {id_parada}: {e}")
        return []

def scrape_parada(id_parada, nombre_parada):
    arribos = fetch_arribos(id_parada)
    ahora = datetime.now(TZ_AR)
    horarios = []
    
    print(f"     📱 {nombre_parada}: {len(arribos)} arribos")
    
    for arrivo in arribos[:10]:
        try:
            linea = arrivo.get('descripcionCortaBandera', '141')
            tiempo_texto = arrivo.get('tiempoRestanteArribo', '')
            ident_coche = arrivo.get('identificadorCoche', '')
            chofer = arrivo.get('identificadorChofer', '')
            
            mins = minutos_from_api(tiempo_texto)
            if mins is None:
                continue
                
            hora = (ahora + timedelta(minutes=mins)).strftime("%H:%M")
            
            horarios.append({
                'Hora_Scrap': ahora.strftime('%H:%M:%S'),
                'Hora_Llegada': hora,
                'Línea': linea,
                'Minutos': mins,
                'Parada': nombre_parada,
                'Identificador': ident_coche,
                'Chofer': chofer,
                'Desvio': arrivo.get('desvioHorario', ''),
                'UltimoGPS': arrivo.get('ultimaFechaHoraGPS', '')
            })
            
            print(f"     ✅ {hora} {linea} ({mins}m) [# {ident_coche}] {chofer[:20]}...")
            
        except Exception as e:
            print(f"     ❌ {e}")
    
    return horarios

def cargar_excel_dia():
    archivo_hoy = get_fecha_excel()
    
    if not os.path.exists(archivo_hoy):
        return {
            'LP1912': pd.DataFrame(),
            'LP1912-215': pd.DataFrame(),
            '6203-6173': pd.DataFrame()
        }
    
    try:
        excel_file = pd.ExcelFile(archivo_hoy)
        datos = {}
        for sheet in ['LP1912', 'LP1912-215', '6203-6173']:
            if sheet in excel_file.sheet_names:
                df = pd.read_excel(archivo_hoy, sheet_name=sheet, skiprows=4)
                datos[sheet] = df
            else:
                datos[sheet] = pd.DataFrame()
        return datos
    except Exception as e:
        print(f"⚠️ {archivo_hoy}: {e}")
        return {
            'LP1912': pd.DataFrame(),
            'LP1912-215': pd.DataFrame(),
            '6203-6173': pd.DataFrame()
        }

def guardar_excel_dia(horarios_lp1912_nuevos, horarios_combinadas_nuevos):
    datos_existentes = cargar_excel_dia()
    ahora = datetime.now(TZ_AR)
    archivo_hoy = get_fecha_excel()
    
    # Crear data/ siempre
    os.makedirs(DATA_DIR, exist_ok=True)
    
    df_lp1912_nuevos = pd.DataFrame(horarios_lp1912_nuevos)
    df_lp1912 = pd.concat([datos_existentes['LP1912'], df_lp1912_nuevos]).drop_duplicates(subset=['Hora_Llegada','Línea','Identificador']).reset_index(drop=True)
    
    nuevos_215 = [h for h in horarios_lp1912_nuevos if '215' in str(h.get('Línea', ''))]
    df_215_nuevos = pd.DataFrame(nuevos_215)
    df_215 = pd.concat([datos_existentes['LP1912-215'], df_215_nuevos]).drop_duplicates(subset=['Hora_Llegada','Línea','Identificador']).reset_index(drop=True)
    
    df_combinadas_nuevos = pd.DataFrame(horarios_combinadas_nuevos)
    df_combinadas = pd.concat([datos_existentes['6203-6173'], df_combinadas_nuevos]).drop_duplicates(subset=['Hora_Llegada','Línea','Parada','Identificador']).reset_index(drop=True)
    
    with pd.ExcelWriter(archivo_hoy, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, 'LP1912', index=False, startrow=4)
        df_215.to_excel(writer, 'LP1912-215', index=False, startrow=4)
        df_combinadas.to_excel(writer, '6203-6173', index=False, startrow=4)
        
        for sheet_name, df in [('LP1912', df_lp1912), ('LP1912-215', df_215), ('6203-6173', df_combinadas)]:
            ws = writer.sheets[sheet_name]
            ws['A1'] = f'LÍNEA 141 API - {sheet_name}'
            ws['A2'] = f'{ahora.strftime("%d/%m/%Y %H:%M:%S")}'
            ws['A3'] = f'{len(df)} únicos (Identificador)'
            for row in ws['A1:A3']:
                for cell in row:
                    cell.font = Font(bold=True)

    print(f"💾 data/horarios-141-{ahora.strftime('%Y-%m-%d')}.xlsx")
    print(f"   LP1912: {len(df_lp1912)} | 215: {len(df_215)} | Combinadas: {len(df_combinadas)}")

def guardar_txt(horarios, nombre_txt, titulo):
    archivo_txt = os.path.join(DATA_DIR, nombre_txt)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    ahora = datetime.now(TZ_AR)
    horarios_sorted = sorted(horarios, key=lambda x: x['Hora_Llegada'])
    
    with open(archivo_txt, "w", encoding="utf-8") as f:
        f.write(f"🚌 {titulo} - API JSON\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        for i, h in enumerate(horarios_sorted, 1):
            f.write(f"{i:2d}. {h['Hora_Llegada']:>5} {h['Línea']:>8} ({h['Minutos']:2}m) [# {h['Identificador']}] {h['Chofer']}\n")

def ciclo_completo():
    ahora = datetime.now(TZ_AR)
    print(f"\n⏰ {ahora.strftime('%H:%M:%S')} - Línea 141 API")
    
    # LP1912
    print("🌐 LP1912...")
    horarios_lp1912 = scrape_parada("LP1912", "LP1912")
    guardar_txt(horarios_lp1912, "horarios-LP1912.txt", "141 - LP1912")
    
    # Combinadas
    print("🌐 L6203 + L6173...")
    horarios_combinadas = []
    for id_parada, nombre in PARADAS_COMBINADAS:
        horarios = scrape_parada(id_parada, nombre)
        horarios_combinadas.extend(horarios)
    guardar_txt(horarios_combinadas, "horarios-6203-6173.txt", "141 - L6203+L6173")
    
    if horarios_lp1912 or horarios_combinadas:
        guardar_excel_dia(horarios_lp1912, horarios_combinadas)
    print("✅ Listo!")

def main():
    parser = argparse.ArgumentParser(description="Recolector 141 API")
    parser.add_argument('--once', action='store_true', help='GitHub Actions')
    args = parser.parse_args()
    
    print("🚀 Línea 141 - API JSON (identificadorCoche)")
    print(f"📁 Todos archivos → /{DATA_DIR}/")
    
    if args.once:
        ciclo_completo()
    else:
        while True:
            ciclo_completo()
            print("⏳ 15 minutos...\n")
            time.sleep(900)

if __name__ == "__main__":
    main()
