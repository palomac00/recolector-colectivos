import requests
import json
from datetime import datetime
import os

# Usamos la parada LP1912 (Diagonal 80 y 1) sin filtrar por codLinea
# Esto asegura que veamos TODOS los colectivos que el sistema detecta ahí
URL = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?idParada=LP1912"
ARCHIVO = "horarios.json"

# Identidad de navegador para evitar bloqueos del servidor
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

datos = {"registros": []}

# Cargar datos previos (maneja archivos vacíos o corruptos)
if os.path.exists(ARCHIVO):
    try:
        with open(ARCHIVO, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                datos = json.loads(content)
    except Exception:
        datos = {"registros": []}

try:
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    
    try:
        data = response.json()
    except Exception:
        print("La respuesta de la web no es un JSON válido.")
        data = {"arribos": []}

    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    arribaos = []
    
    # Extraer información de todos los ramales detectados
    if 'arribos' in data and data['arribos']:
        for arribo in data['arribos']:
            arribaos.append({
                "linea": arribo.get('codigoLinea', 'N/A'),
                "ramal": arribo.get('descripcionCartelBandera', 'N/A'),
                "tiempo": arribo.get('tiempoRestanteArribo', 'N/A'),
                "coche": arribo.get('identificadorCoche', 'N/A')
            })
    
    # Guardar el registro. Incluir el timestamp siempre obliga a GitHub a ver un cambio
    datos["registros"].append({
        "timestamp": timestamp,
        "cantidad": len(arribaos),
        "detalles": arribaos
    })
    
    # Limitar el historial a los últimos 500 registros para que el archivo no sea gigante
    if len(datos["registros"]) > 500:
        datos["registros"] = datos["registros"][-500:]

    with open(ARCHIVO, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
        
    print(f"✓ {timestamp}: Guardados {len(arribaos)} colectivos.")

except Exception as e:
    print(f"Error en la recolección: {e}")
