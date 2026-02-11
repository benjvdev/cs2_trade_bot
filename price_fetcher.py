import sqlite3
import time
import json
import os

# Intenta importar cloudscraper, si no está, avisa
try:
    import cloudscraper
except ImportError:
    print("❌ ERROR: Necesitas instalar cloudscraper.")
    print("   Ejecuta: pip install cloudscraper")
    exit()

# Configuración
DB_NAME = "cs2_skins.db"
URL_API = "http://csgobackpack.net/api/GetItemsList/v2/"
LOCAL_FILE = "prices.json"

def get_json_data():
    """Intenta descargar de internet, si falla, busca archivo local."""
    
    # 1. Intentar descarga con Cloudscraper (Anti-Cloudflare)
    print(f"\n🌍 Intentando conectar con CSGO Backpack (Modo Evasión Cloudflare)...")
    scraper = cloudscraper.create_scraper() # Crea un navegador falso
    
    try:
        response = scraper.get(URL_API, params={'currency': 'USD'}, timeout=60)
        
        if response.status_code == 200:
            print("✅ ¡Bypass Exitoso! Descargando datos...")
            return response.json()
        else:
            print(f"⚠️ El servidor respondió con código {response.status_code}.")
            
    except Exception as e:
        print(f"⚠️ Error de conexión automática: {e}")

    # 2. Si falla lo anterior, buscar archivo local
    print(f"\n⚠️ No se pudo descargar automáticamente.")
    print(f"📂 Buscando archivo local '{LOCAL_FILE}' como respaldo...")
    
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                print("✅ Archivo local encontrado. Leyendo...")
                return json.load(f)
        except Exception as e:
            print(f"❌ Error leyendo archivo local: {e}")
            return None
    else:
        print(f"❌ ERROR FATAL: No se pudo conectar y no existe '{LOCAL_FILE}'.")
        print("💡 SOLUCIÓN MANUAL:")
        print("   1. Ve a: http://csgobackpack.net/api/GetItemsList/v2/")
        print("   2. Espera que cargue el texto.")
        print("   3. Dale click derecho -> 'Guardar como' -> nómbralo 'prices.json'")
        print("   4. Ponlo en esta misma carpeta y vuelve a ejecutar este script.")
        return None

def update_prices():
    data = get_json_data()
    
    if not data or not data.get('success'):
        print("❌ No hay datos válidos para procesar.")
        return

    items = data.get('items_list', {})
    print(f"⚙️ Procesando {len(items)} items para la base de datos...")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla de precios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            market_hash_name TEXT PRIMARY KEY,
            price REAL,
            source TEXT,
            updated_at TEXT
        )
    ''')
    
    updates = []
    
    for name, details in items.items():
        price = 0.0
        p_data = details.get("price", {})
        
        try:
            # Prioridad: 7 días -> 30 días -> 24 horas -> Histórico
            if "7_days" in p_data and p_data["7_days"].get("average", 0):
                price = float(p_data["7_days"]["average"])
            elif "30_days" in p_data and p_data["30_days"].get("average", 0):
                price = float(p_data["30_days"]["average"])
            elif "24_hours" in p_data and p_data["24_hours"].get("average", 0):
                price = float(p_data["24_hours"]["average"])
            
            if price == 0 and "all_time" in p_data:
                 price = float(p_data["all_time"].get("average", 0))

        except (ValueError, TypeError):
            continue

        if price > 0:
            updates.append((name, price, "csgobackpack", time.strftime('%Y-%m-%d %H:%M:%S')))

    if updates:
        print(f"📥 Insertando {len(updates)} precios...")
        cursor.execute("BEGIN TRANSACTION;")
        cursor.executemany('''
            INSERT OR REPLACE INTO prices (market_hash_name, price, source, updated_at)
            VALUES (?, ?, ?, ?)
        ''', updates)
        conn.commit()
        print(f"✅ ¡LISTO! Base de datos actualizada con éxito.")
    else:
        print("⚠️ No se encontraron precios válidos.")

    conn.close()

if __name__ == "__main__":
    update_prices()