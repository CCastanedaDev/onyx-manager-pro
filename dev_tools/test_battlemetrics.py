import requests
import json

def test_battlemetrics(ip):
    print(f"🔍 Buscando servidor con IP: {ip} en BattleMetrics...")
    # Buscamos por nombre exacto
    name_query = "SCUM Server Powered By Onyx Manager"
    url = f"https://api.battlemetrics.com/servers?filter[search]={name_query}&filter[game]=scum"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                server = data["data"][0]
                attr = server["attributes"]
                print("✅ Servidor Encontrado:")
                print(f"   - Nombre: {attr['name']}")
                print(f"   - ID: {server['id']}")
                print(f"   - Puerto: {attr['port']}")
                print(f"   - QueryPort: {attr['queryPort']}")
                print(f"   - Jugadores: {attr['players']}/{attr['maxPlayers']}")
                print(f"   - Estado: {attr['status']}")
                return True
            else:
                print("❌ No se encontraron servidores con esa IP.")
        else:
            print(f"❌ Error API: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Excepción: {e}")
    return False

if __name__ == "__main__":
    test_battlemetrics("201.239.29.194")
