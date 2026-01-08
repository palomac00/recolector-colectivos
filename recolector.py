#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECOLECTOR LÍNEA 141 - VERSIÓN FINAL CORREGIDA
URLs DIFERENTES + Acumulación perfecta
"""

import pandas as pd
import requests
from datetime import datetime
import pytz
import os
import time
from openpyxl.styles import Font

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

# ✅ URLs CORRECTAS Y DIFERENTES
URL_LP1912 = "https://www.nuevodejulio.com.ar/api/paradas/LP1912/proximos-arribos"
URL_COMBINADAS = "https://www.nuevodejulio.com.ar/api/paradas/6203-6173/proximos-arribos"

def get_fecha_excel():
    hoy = datetime.now(TZ_AR).strftime("%Y-%m-%d")
    return f"horarios-141-{hoy}.xlsx"

def cargar_excel_dia():
    archivo_hoy = get_fecha_excel()
    
    if not os.path.exists(archivo_hoy):
        print(f"📄 Nuevo: {archivo_hoy}")
        empty_df = pd.DataFrame(columns=['Hora_Llegada', 'Línea', 'Minutos', 'Parada'])
        return {'LP1912': empty_df, 'LP1912-215': empty_df, '6203-6173': empty_df}
    
    try:
        print(f"📖 Cargando {archivo_hoy}")
        excel_file = pd.ExcelFile(archivo_hoy)
        sheets = {}
        
        for sheet_name in ['LP1912', 'LP1912-215', '6203-6173']:
            if sheet_name in excel_file.sheet_names:
                df = pd.read_excel(archivo_hoy, sheet_name=sheet_name, skiprows=3, header=0)
                columnas = ['Hora_Llegada', 'Línea', 'Minutos', 'Parada']
                df.columns = columnas[:len(df.columns)]
                sheets[sheet_name] = df
                print(f"   {sheet_name}: {len(df)} filas")
            else:
                sheets[sheet_name] = pd.DataFrame(columns=['Hora_Llegada', 'Línea', 'Minutos', 'Parada'])
        
        return sheets
    except Exception as e:
        print(f"❌ Error Excel: {e}")
        empty_df = pd.DataFrame(columns=['Hora_Llegada', 'Línea', 'Minutos', 'Parada'])
        return {'LP1912': empty_df, 'LP1912-215': empty_df, '6203-6173': empty_df}

def scrape_lp1912():
    """Scraping LP1912 - MÁS RÁPIDO"""
    try:
        print("🌐 LP1912...", end=" ")
        response = requests.get(URL_LP1912, timeout=8)
        data = response.json()
        
        horarios = []
        for bus in data.get('arribos', []):
            hora_str = bus.get('hora_llegada', '')
            if ':' in hora_str:
                horarios.append({
                    'Hora_Llegada': hora_str,
                    'Línea': bus.get('linea', 'N/A'),
                    'Minutos': bus.get('minutos', 0),
                    'Parada': 'LP1912'
                })
        
        print(f"{len(horarios)} ok")
        return horarios
    except:
        print("❌")
        return []

def scrape_combinadas():
    """Scraping 6203-6173"""
    try:
        print("🌐 Combinadas...", end=" ")
        response = requests.get(URL_COMBINADAS, timeout=8)
        data = response.json()
        
        horarios = []
        for bus in data.get('arribos', []):
            hora_str = bus.get('hora_llegada', '')
            if ':' in hora_str:
                horarios.append({
                    'Hora_Llegada': hora_str,
                    'Línea': bus.get('linea', 'N/A'),
                    'Minutos': bus.get('minutos', 0),
                    'Parada': '6203-6173'
                })
        
        print(f"{len(horarios)} ok")
        return horarios
    except:
        print("❌")
        return []

def guardar_excel_dia(horarios_lp1912, horarios_combinadas):
    datos_existentes = cargar_excel_dia()
    ahora = datetime.now(TZ_AR)
    archivo = get_fecha_excel()
    
    columnas = ['Hora_Llegada', 'Línea', 'Minutos', 'Parada']
    
    # ACUMULAR
    df_lp1912 = pd.concat([datos_existentes['LP1912'], pd.DataFrame(horarios_lp1912, columns=columnas)], ignore_index=True)
    nuevos_215 = [h for h in horarios_lp1912 if '215' in str(h.get('Línea', ''))]
    df_215 = pd.concat([datos_existentes['LP1912-215'], pd.DataFrame(nuevos_215, columns=columnas)], ignore_index=True)
    df_combinadas = pd.concat([datos_existentes['6203-6173'], pd.DataFrame(horarios_combinadas, columns=columnas)], ignore_index=True)
    
    with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, 'LP1912', index=False, startrow=3)
        df_215.to_excel(writer, 'LP1912-215', index=False, startrow=3)
        df_combinadas.to_excel(writer, '6203-6173', index=False, startrow=3)
        
        from openpyxl.styles import Font
        sheets_info = {'LP1912': df_lp1912, 'LP1912-215': df_215, '6203-6173': df_combinadas}
        
        for sheet_name, df in sheets_info.items():
            ws = writer.sheets[sheet_name]
            ws['A1'] = f'LÍNEA 141 - {sheet_name}'
            ws['A2'] = f'Fecha: {ahora.strftime("%d/%m/%Y")}'
            ws['A3'] = f'Total: {len(df)}'
            for row in ws['A1:A3']:
                for cell in row:
                    cell.font = Font(bold=True)
    
    print(f"💾 {archivo}: LP1912={len(df_lp1912)} 215={len(df_215)} Comb={len(df_combinadas)}")

def main():
    print("🚀 LÍNEA 141 - INICIADO")
    print(f"📅 {datetime.now(TZ_AR).strftime('%H:%M:%S')}")
    
    while True:
        try:
            print(f"\n⏰ {datetime.now(TZ_AR).strftime('%H:%M:%S')}")
            t1 = time.time()
            
            horarios_lp1912 = scrape_lp1912()
            horarios_combinadas = scrape_combinadas()
            
            if horarios_lp1912 or horarios_combinadas:
                guardar_excel_dia(horarios_lp1912, horarios_combinadas)
            else:
                print("⚠️ Sin datos")
            
            t2 = time.time()
            print(f"✅ Ciclo: {t2-t1:.1f}s | Espera: 4 min")
            time.sleep(240)  # ← 4 MINUTOS
            
        except KeyboardInterrupt:
            print("\n🛑 Parado")
            break
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
