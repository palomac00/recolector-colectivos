import requests
import json
from datetime import datetime
import os

URL = "https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=141&idParada=LP1912"
ARCHIVO = "horarios.json"

if os.path.exists(ARCHIVO):
    with open(ARCHIVO, 'r') as f:
        datos = json.load(f)
else:
    datos = {"registros": []}

headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(URL, timeout=10, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.text)}")
    
    if response.status_code == 200 and len(response.text) > 10:
        data = response.json()
        arribaos = data.get('arribos', [])
        
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        datos["registros"].append({
            "timestamp": timestamp,
            "cantidad": len(arribaos),
            "arribaos": arribaos[:3] if arribaos else []
        })
        
        with open(ARCHIVO, 'w') as f:
            json.dump(datos, f, indent=2)
        
        print(f"Guardados {len(arribaos)} colectivos")
    else:
        print("Respuesta vacía o error")
        
except Exception as e:
    print(f"Error: {e}")
