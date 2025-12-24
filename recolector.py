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

try:
    response = requests.get(URL, timeout=10)
    data = response.json()
    
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    arribaos = data.get('arribos', [])
    
    datos["registros"].append({
        "timestamp": timestamp,
        "cantidad": len(arribaos),
        "arribaos": arribaos[:5]
    })
    
    with open(ARCHIVO, 'w') as f:
        json.dump(datos, f, indent=2)
except:
    pass
