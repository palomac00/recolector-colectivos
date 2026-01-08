#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECOLECTOR HORARIOS LÍNEA 141 - VERSIÓN FINAL ACUMULATIVA
Acumula TODOS los horarios del día correctamente
"""

import pandas as pd
import requests
from datetime import datetime
import pytz
import os
import time
from openpyxl.styles import Font

# Zona horaria Argentina
TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

# URLs API (ajusta si cambian)
URL_LP1912 = "https://www.nuevodejulio.com.ar/api/paradas/6203-6173/proximos-arribos"
URL_LP1912_215 = "https://www.nuevodejulio.com.ar/api/paradas/6203-6173/proximos-arribos"

def get_fecha_excel():
    """Nombre archivo Excel HOY"""
    hoy = datetime.now(TZ_AR).strftime("%Y-%m-%d")
    return f"horarios-141-{hoy}.xlsx"

def cargar_excel_dia():
    """🔥 CARGA TODOS los horarios existentes del día"""
    archivo_hoy = get_fecha_excel()
    
    if not os.path.exists(archivo_hoy):
        print(f"📄 Nuevo: {archivo_hoy}")
        empty_df = pd.DataFrame(columns=['Hora_Llegada', 'Línea', 'Minutos', 'Parada', 'Hora_Scrap'])
        return {'LP1912': empty_df, 'LP1912-215': empty_df, '6203-6173': empty_df}
    
    try:
        print(f"📖 Cargando {archivo_hoy}")
        excel_file = pd.ExcelFile(archivo_hoy)
        sheets = {}
        
        for sheet_name in ['LP1912', 'LP1912-215', '6203-6173']:
            if sheet_name in excel_file.sheet_names:
                # Skiprows=3 (títulos) + header=0 (siguiente = columnas)
                df = pd.read_excel(archivo_hoy, sheet_name=sheet_name, skiprows=3, header=0)
                
                # FUERZA columnas correctas
                columnas = ['Hora_Llegada', 'Línea', 'Minutos', 'Parada', 'Hora_Scrap']
                if len(df.columns) >= len(columnas):
                    df.columns = columnas[:len(df.columns)]
                else:
                    df = df.reindex(columns=columnas, fill_value='')
                
                sheets[sheet_name] = df
                print(f"   {sheet_name}: {len(df)} filas ✓")
            else:
                print(f"   ⚠️  {sheet_name} vacío")
                sheets[sheet_name] = pd.DataFrame(columns=['Hora_Llegada', 'Línea', 'Minutos', 'Parada', 'Hora_Scrap'])
        
        # DEBUG
        print(f"📊 TOTAL CARGADO: LP1912={len(sheets['LP1912'])} | 215={len(sheets['LP1912-215'])} | Comb={len(sheets['6203-6173'])}")
        return sheets
        
    except Exception as e:
        print(f"❌ Error Excel: {e}")
        empty_df = pd.DataFrame(columns=['Hora_Llegada', 'Línea', 'Minutos', 'Parada', 'Hora_Scrap'])
        return {'LP1912': empty_df, 'LP1912-215': empty_df, '6203-6173': empty_df}

def scrape_lp1912():
    """Scraping LP1912"""
    try:
        print("🌐 Scraping LP1912...")
        response = requests.get(URL_LP1912, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        horarios = []
        ahora = datetime.now(TZ_AR)
        
        for bus in data.get('arribos', []):
            hora_str = bus.get('hora_llegada', '')
            linea = bus.get('linea', 'DESCONOCIDA')
            minutos = bus.get('minutos', 0)
            
            if ':' in hora_str:
                horarios.append({
                    'Hora_Llegada': hora_str,
                    'Línea': linea,
                    'Minutos': minutos,
                    'Parada': 'LP1912',
                    'Hora_Scrap': ahora.strftime('%H:%M:%S')
                })
        
        print(f"✅ LP1912: {len(horarios)} horarios")
        return horarios
        
    except Exception as e:
        print(f"❌ LP1912: {e}")
        return []

def scrape_combinadas():
    """Scraping 6203-6173"""
    try:
        print("🌐 Scraping Combinadas...")
        response = requests.get(URL_LP1912_215, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        horarios = []
        ahora = datetime.now(TZ_AR)
        
        for bus in data.get('arribos', []):
            hora_str = bus.get('hora_llegada', '')
            linea = bus.get('linea', 'DESCONOCIDA')
            minutos = bus.get('minutos', 0)
            
            if ':' in hora_str:
                horarios.append({
                    'Hora_Llegada': hora_str,
                    'Línea': linea,
                    'Minutos': minutos,
                    'Parada': 'L6203/L6173',
                    'Hora_Scrap': ahora.strftime('%H:%M:%S')
                })
        
        print(f"✅ Combinadas: {len(horarios)} horarios")
        return horarios
        
    except Exception as e:
        print(f"❌ Combinadas: {e}")
        return []

def guardar_excel_dia(horarios_lp1912_nuevos, horarios_combinadas_nuevos):
    """🔥 GUARDA ACUMULANDO TODOS los horarios"""
    datos_existentes = cargar_excel_dia()
    ahora = datetime.now(TZ_AR)
    archivo_hoy = get_fecha_excel()
    
    columnas = ['Hora_Llegada', 'Línea', 'Minutos', 'Parada', 'Hora_Scrap']
    
    # ACUMULAR: existentes + nuevos
    df_lp1912 = pd.concat([
        datos_existentes['LP1912'], 
        pd.DataFrame(horarios_lp1912_nuevos, columns=columnas)
    ], ignore_index=True)
    
    nuevos_215 = [h for h in horarios_lp1912_nuevos if '215' in str(h.get('Línea', ''))]
    df_215 = pd.concat([
        datos_existentes['LP1912-215'], 
        pd.DataFrame(nuevos_215, columns=columnas)
    ], ignore_index=True)
    
    df_combinadas = pd.concat([
        datos_existentes['6203-6173'], 
        pd.DataFrame(horarios_combinadas_nuevos, columns=columnas)
    ], ignore_index=True)
    
    # ESCRIBIR con títulos ARRIBA
    with pd.ExcelWriter(archivo_hoy, engine='openpyxl') as writer:
        df_lp1912.to_excel(writer, sheet_name='LP1912', index=False, startrow=3)
        df_215.to_excel(writer, sheet_name='LP1912-215', index=False, startrow=3)
        df_combinadas.to_excel(writer, sheet_name='6203-6173', index=False, startrow=3)
        
        from openpyxl.styles import Font
        
        sheets_info = {
            'LP1912': df_lp1912,
            'LP1912-215': df_215,
            '6203-6173': df_combinadas
        }
        
        for sheet_name, df in sheets_info.items():
            worksheet = writer.sheets[sheet_name]
            worksheet['A1'] = f'LÍNEA 141 - {sheet_name}'
            worksheet['A2'] = f'Fecha: {ahora.strftime("%d/%m/%Y")}'
            worksheet['A3'] = f'Total: {len(df)} horarios'
            
            # Negrita
            for row in worksheet['A1:A3']:
                for cell in row:
                    cell.font = Font(bold=True)
    
    print(f"💾 {archivo_hoy} GUARDADO:")
    print(f"   LP1912: {len(horarios_lp1912_nuevos)} nuevos → {len(df_lp1912)} TOTAL")
    print(f"   215: {len(nuevos_215)} nuevos → {len(df_215)} TOTAL")
    print(f"   Combinadas: {len(horarios_combinadas_nuevos)} nuevos → {len(df_combinadas)} TOTAL")

def main():
    """Loop infinito - 10 minutos"""
    print("🚀 RECOLECTOR LÍNEA 141 - ACUMULATIVO")
    print(f"📅 {datetime.now(TZ_AR).strftime('%d/%m/%Y %H:%M:%S')}")
    
    while True:
        try:
            print("\n" + "="*60)
            print(f"⏰ {datetime.now(TZ_AR).strftime('%H:%M:%S')} ← NUEVO CICLO")
            
            horarios_lp1912 = scrape_lp1912()
            horarios_combinadas = scrape_combinadas()
            
            if horarios_lp1912 or horarios_combinadas:
                guardar_excel_dia(horarios_lp1912, horarios_combinadas)
            else:
                print("⚠️  Sin datos")
            
            print("💤 Próximo: 10 min...")
            time.sleep(600)  # 10 minutos
            
        except KeyboardInterrupt:
            print("\n🛑 Parado por usuario")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(600)

if __name__ == "__main__":
    main()
