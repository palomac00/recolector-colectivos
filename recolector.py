import requests
import json
from datetime import datetime
import os
import re

URL = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
ARCHIVO = "horarios.json"

if os.path.exists(ARCHIVO):
    with open(ARCHIVO, 'r') as f:
        datos = json.load(f)
else:
    datos = {"registros": []}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
}

try:
    response = requests.get(URL, timeout=10, headers=headers)
    
    # Intenta extraer JSON del HTML si está embebido
    text = response.text
    
    # Busca JSON en el HTML
    json_match = re.search(r'\{.*"arribos".*\}', text, re.DOTALL)
    
    if json_match:
        data = json.loads(json_match.group())
        arribaos = data.get('arribos', [])
        
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Limpia los datos
        arribaos_limpios = []
        for arribo in arribaos[:10]:  # Solo los primeros 10
            arribaos_limpios.append({
                "tiempo": arribo.get('tiempoRestanteArribo'),
                "bandera": arribo.get('descripcionCartelBandera'),
                "coche": arribo.get('identificadorCoche'),
                "chofer": arribo.get('identificadorChofer')
            })
        
        datos["registros"].append({
            "timestamp": timestamp,
            "cantidad": len(arribaos_limpios),
            "arribaos": arribaos_limpios
        })
        
        with open(ARCHIVO, 'w') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        print(f"OK: {len(arribaos_limpios)} colectivos")
    else:
        print("No se encontró JSON en la respuesta")
        
except Exception as e:
    print(f"Error: {e}")
