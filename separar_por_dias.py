import pandas as pd
import os
from datetime import datetime
import pytz

TZ_AR = pytz.timezone('America/Argentina/Buenos_Aires')

def separar_excel_por_dias(archivo_origen):
    """Separa el Excel grande por días en archivos individuales"""
    
    # Leer todas las hojas
    excel = pd.ExcelFile(archivo_origen)
    hojas = ['LP1912', 'LP1912-215', '6203-6173']
    
    datos_por_dia = {}
    
    print("🔍 Analizando datos por fecha...")
    
    for hoja in hojas:
        if hoja in excel.sheet_names:
            df = pd.read_excel(excel, sheet_name=hoja)
            
            # Buscar columna de fecha (puede estar desordenada)
            col_fecha = None
            for col in df.columns:
                if 'fecha' in col.lower() or 'date' in col.lower():
                    col_fecha = col
                    break
            
            if col_fecha is None:
                # Si no hay columna fecha, usar Hora_Scrap
                df['Fecha_Scrap'] = pd.to_datetime(df['Hora_Scrap'], format='%H:%M:%S').dt.date
                col_fecha = 'Fecha_Scrap'
            else:
                # Parsear fechas desordenadas del Excel
                df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce', dayfirst=True)
                df['Fecha_Scrap'] = df[col_fecha].dt.date
            
            # Agrupar por día
            for fecha, grupo in df.groupby('Fecha_Scrap'):
                fecha_str = fecha.strftime('%Y-%m-%d')
                if fecha_str not in datos_por_dia:
                    datos_por_dia[fecha_str] = {hoja: grupo}
                else:
                    datos_por_dia[fecha_str][hoja] = grupo
                print(f"  📅 {fecha_str}: {len(grupo)} filas en {hoja}")
    
    # Crear Excel por día
    print("\n📊 Creando Excels por día...")
    for fecha_str, datos_dia in datos_por_dia.items():
        archivo_dia = f"horarios-141-{fecha_str}.xlsx"
        
        with pd.ExcelWriter(archivo_dia, engine='openpyxl') as writer:
            for hoja, df_dia in datos_dia.items():
                # Limpiar columnas extrañas
                columnas_limpias = ['Hora_Scrap', 'Hora_Llegada', 'Línea', 'Minutos', 'Parada']
                df_limpio = df_dia[[col for col in columnas_limpias if col in df_dia.columns]]
                df_limpio.to_excel(writer, sheet_name=hoja, index=False)
                
                # Títulos
                worksheet = writer.sheets[hoja]
                worksheet['A1'] = f'LÍNEA 141 - {hoja}'
                worksheet['A2'] = f'Fecha: {fecha_str}'
                worksheet['A3'] = f'Total: {len(df_limpio)} horarios'
        
        print(f"✅ Creado: {archivo_dia}")
    
    print(f"\n🎉 SEPARADO! {len(datos_por_dia)} días procesados")
    print("Archivos generados:")
    for f in sorted(datos_por_dia.keys()):
        print(f"   📄 horarios-141-{f}.xlsx")

if __name__ == "__main__":
    archivo = "horarios-141-completo.xlsx"  # Tu archivo actual
    
    if os.path.exists(archivo):
        separar_excel_por_dias(archivo)
        print("\n¡Listo! Eliminá el Excel grande y quedate con los diarios.")
    else:
        print(f"❌ No encuentro {archivo}")
