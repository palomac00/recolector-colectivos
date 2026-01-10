#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECOLECTOR LÍNEA 141 - API JSON OFICIAL 
identificadorCoche directo desde cuandollega API
"""

import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import os
import argparse
from openpyxl.styles import Font
import re

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

PARADAS_INDIVIDUALES = [
    ("LP1912", "LP1912"),
]

PARADAS_COMBINADAS = [
    ("L6203", "L6203"),
    ("L6173", "L6173"),
]

def get_fecha_excel():
    return f"data/horarios-141-{datetime.now(TZ_AR).strftime('%Y-%m-%d')}.xlsx"

def minutos_from_api(tiempo_texto):
    """Convierte '9 min. aprox.' → 9"""
    m = re.search(r'(\d+)\s*min', tiempo_texto, re.IGNORECASE)
    return int(m.group(1)) if m else None

def fetch_arribos(id_parada):
    """API request directo a cuandollega"""
    try:
        # Endpoint API desde tu inspección (reconstruido)
        url = f"https://cuandollega.smartmovepro.net/nuevedejulio/arribos/api?codLinea=141&idParada={id_parada}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://cuandollega.smartmovepro.net/nuevedejulio/arribos/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get('arribos', [])
    except Exception as e:
        print(f"❌ API Error {id_parada}: {e}")
        return []

def scrape_parada(id_parada, nombre_parada):
    """API → horarios con identificadorCoche"""
    arribos = fetch_arribos(id_parada)
    ahora = datetime.now(TZ_AR)
    horarios = []
    
    print(f"     📱 API {nombre_parada}: {len(arribos)} arribos")
    
    for arrivo in arribos[:10]:  # Máx 10
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
                'Identificador': ident_coche,      # 🎯 217, 211
                'Chofer': chofer,                  # Valdez, Rivas
                'Desvio': arrivo.get('desvioHorario', ''),
                'UltimoGPS': arrivo.get('ultimaFechaHoraGPS', '')
            })
            
            print(f"     ✅ {hora} {linea} ({mins}min) [# {ident_coche}] {chofer}")
            
        except Exception as e:
            print(f"     ❌ Arribo error: {e}")
    
    return horarios

def cargar_excel_dia():
    archivo_hoy = get_fecha_excel()
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(archivo_hoy):
        return {
            'LP1912': pd.DataFrame(columns=['Hora_Scrap','Hora_Llegada','Línea','Minutos','Parada','Identificador','Chofer','Desvio','UltimoGPS']),
            'LP1912-215': pd.DataFrame(columns=['Hora_Scrap','Hora_Llegada','Línea','Minutos','Parada','Identificador','Chofer','Desvio','UltimoGPS']),
            '6203-6173': pd.DataFrame(columns=['Hora_Scrap','Hora_Llegada','Línea','Minutos','Parada','Identificador','Chofer','Desvio','UltimoGPS'])
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
    except:
        return {
            'LP1912': pd.DataFrame(),
            'LP1912-215': pd.DataFrame(),
            '6203-6173': pd.DataFrame()
        }

def guardar_excel_dia(horarios_lp1912_nuevos, horarios_combinadas_nuevos):
    datos_existentes = cargar_excel_dia()
    ahora = datetime.now(TZ_AR)
    archivo_hoy = get_fecha_excel()
    
    df_lp1912_nuevos = pd.DataFrame(horarios_lp1912_nuevos)
    df_lp1912 = pd.concat([datos_existentes['LP1912'], df_lp1912_nuevos], ignore_index=True)
    df_lp1912 = df_lp1912.drop_duplicates(subset=['Hora_Llegada','Línea','Identificador']).reset_index(drop=True)
    
    nuevos_215 = [h for h in horarios_lp1912_nuevos if '215' in h.get('Línea', '')]
    df_215_nuevos = pd.DataFrame(nuevos_215)
    df_215 = pd.concat([datos_existentes['LP1912-215'], df_215_nuevos], ignore_index=True)
    df_215 = df_215.drop_duplicates(subset=['Hora_Llegada','Línea','Identificador']).reset_index(drop=True)
    
    df_combinadas_nuevos = pd.DataFrame(horarios_combinadas_nuevos)
    df_combinadas = pd.concat([datos_existentes['6203-6173'], df_combinadas_nuevos], ignore_index=True)
    df_combinadas = df_combinadas.drop_duplicates(subset=['Hora_Llegada','Línea','Parada','Identificador']).reset_index(drop=True)
    
    with pd.ExcelWriter(archivo_hoy, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, sheet_name='LP1912', index=False, startrow=4)
        df_215.to_excel(writer, sheet_name='LP1912-215', index=False, startrow=4)
        df_combinadas.to_excel(writer, sheet_name='6203-6173', index=False, startrow=4)
        
        for sheet_name, df in [('LP1912', df_lp1912), ('LP1912-215', df_215), ('6203-6173', df_combinadas)]:
            ws = writer.sheets[sheet_name]
            ws['A1'] = f'LÍNEA 141 - {sheet_name} - {ahora.strftime("%d/%m/%Y")}'
            ws['A2'] = f'Última actualización: {ahora.strftime("%H:%M:%S")}'
            ws['A3'] = f'Total: {len(df)} únicos por Identificador'
            for row in ws['A1:A3']:
                for cell in row:
                    cell.font = Font(bold=True)

    print(f"💾 Excel: {archivo_hoy}")
    print(f"   LP1912: {len(df_lp1912)} | 215: {len(df_215)} | Combinadas: {len(df_combinadas)}")

def guardar_txt(horarios, nombre_archivo, titulo):
    os.makedirs('data', exist_ok=True)
    nombre_archivo = f"data/{nombre_archivo}"
    ahora = datetime.now(TZ_AR)
    
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(f"🚌 {titulo} - API JSON\n")
        f.write(f"📅 {ahora.strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        for i, h in enumerate(sorted(horarios, key=lambda x: x['Hora_Llegada']), 1):
            f.write(f"{i:2d}. {h['Hora_Llegada']} {h['Línea']:>8} ({h['Minutos']:2}min) [# {h['Identificador']}] {h['Chofer']}\n")

def ciclo_completo():
    ahora = datetime.now(TZ_AR)
    print(f"⏰ {ahora.strftime('%H:%M:%S')} - API JSON...")
    
    # LP1912
    print("   🌐 LP1912...")
    horarios_lp1912 = scrape_parada("LP1912", "LP1912")
    guardar_txt(horarios_lp1912, "horarios-LP1912.txt", "LÍNEA 141 - LP1912")
    
    # Combinadas
    print("   🌐 Combinadas...")
    horarios_combinadas = []
    for nombre_id, nombre_view in PARADAS_COMBINADAS:
        horarios = scrape_parada(nombre_id, nombre_view)
        horarios_combinadas.extend(horarios)
    guardar_txt(horarios_combinadas, "horarios-6203-6173.txt", "LÍNEA 141 - L6203+L6173")
    
    if horarios_lp1912 or horarios_combinadas:
        guardar_excel_dia(horarios_lp1912, horarios_combinadas)
    print("✅ Ciclo completado!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    
    os.makedirs('data', exist_ok=True)
    
    print("🚀 LÍNEA 141 - API JSON (identificadorCoche)")
    print(f"📅 {datetime.now(TZ_AR).strftime('%H:%M:%S')}")
    
    if args.once:
        ciclo_completo()
    else:
        while True:
            ciclo_completo()
            print("\n⏳ 15 min...\n")
            time.sleep(900)

if __name__ == "__main__":
    main()
