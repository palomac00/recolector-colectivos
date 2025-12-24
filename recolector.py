import requests
import json
from datetime import datetime
import os

URL = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
ARCHIVO = "horarios.json"
DEBUG = "debug.txt"

if os.path.exists(ARCHIVO):
    with open(ARCHIVO, 'r') as f:
        datos = json.load(f)
else:
    datos = {"registros": []}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json'
}

try:
    response = requests.get(URL, timeout=10, headers=headers)
    
    # Guarda respuesta para debug
    with open(DEBUG, 'w') as f:
        f.write(f"Status: {response.status_code}\n")
        f.write(f"Content-Type: {response.headers.get('content-type')}\n")
        f.write(f"Length: {len(response.text)}\n")
        f.write("---CONTENIDO---\n")
        f.write(response.text[:2000])
    
    # Intenta parsear como JSON
    try:
        data = response.json()
        arribaos = data.get('arribos', [])
        
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        arribaos_limpios = []
        for arribo in arribaos[:10]:
            arribaos_limpios.append({
                "tiempo": arribo.get('tiempoRestanteArribo'),
                "bandera": arribo.get('descripcionCartelBandera'),
                "coche": arribo.get('identificadorCoche')
            })
        
        datos["registros"].append({
            "timestamp": timestamp,
            "cantidad": len(arribaos_limpios),
            "arribaos": arribaos_limpios
        })
        
        with open(ARCHIVO, 'w') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        print(f"OK: {len(arribaos_limpios)} colectivos")
    except json.JSONDecodeError:
        print("JSON inválido - respuesta guardada en debug.txt")
        
except Exception as e:
    print(f"Error: {e}")
