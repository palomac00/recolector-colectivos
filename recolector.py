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

# Headers que imitan un navegador real
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-AR,es;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://cuandollega.smartmovepro.net/nuevedejulio/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

try:
    response = requests.get(URL, timeout=15, headers=headers, verify=True)
    response.raise_for_status()
    
    data = response.json()
    
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    arribaos = []
    if 'arribos' in data and isinstance(data['arribos'], list):
        for arribo in data['arribos']:
            arribaos.append({
                "tiempo": arribo.get('tiempoRestanteArribo'),
                "bandera": arribo.get('descripcionCartelBandera'),
                "coche": arribo.get('identificadorCoche'),
                "chofer": arribo.get('identificadorChofer'),
                "desvio": arribo.get('desvioHorario'),
                "latitud": arribo.get('latitud'),
                "longitud": arribo.get('longitud')
            })
    
    datos["registros"].append({
        "timestamp": timestamp,
        "cantidad": len(arribaos),
        "arribaos": arribaos
    })
    
    with open(ARCHIVO, 'w') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Guardados {len(arribaos)} colectivos")
    
except requests.exceptions.RequestException as e:
    print(f"Error de red: {e}")
except json.JSONDecodeError as e:
    print(f"Error JSON: {e}")
except Exception as e:
    print(f"Error: {e}")
