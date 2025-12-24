import requests
headers = {'User-Agent': 'Mozilla/5.0'}

print("🔍 Buscando paradas del 324 en Bernal...")

for i in range(1000, 3000):  # Probar 2000 paradas
    try:
        url = f"https://cuandollega.smartmovepro.net/nuevedejulio/arribos/?codLinea=324&idParada=LP{i}"
        r = requests.get(url, headers=headers, timeout=2)
        if "arribos" in r.text and len(r.text) > 100:
            print(f"✅ ¡PARADA 324 ENCONTRADA! LP{i}")
            print(f"URL: {url}")
            break
        if i % 100 == 0:
            print(f"Progreso: {i}/3000")
    except:
        pass

print("🏁 Búsqueda terminada")
