#!/usr/bin/env python3
import os
import glob
import pandas as pd
from datetime import datetime

def separar_xlsx():
    data_dir = "data"
    xlsx_files = glob.glob(f"{data_dir}/horarios-141-*.xlsx")
    
    for file in xlsx_files:
        df = pd.read_excel(file)
        fecha = os.path.basename(file).split('-')[2:4]
        fecha_str = f"{fecha[0]}-{fecha[1]}-??"
        
        # Filtra por fecha si existe columna
        if 'Fecha' in df.columns:
            hoy = df['Fecha'].iloc[0]
            df['Fecha'] = hoy
        
        # Guarda por día
        dia_file = file.replace('.xlsx', f'-{fecha_str}.xlsx')
        df.to_excel(dia_file, index=False)
        print(f"📅 Separado: {dia_file}")

if __name__ == "__main__":
    separar_xlsx()
