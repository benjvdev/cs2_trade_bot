import sqlite3
import requests

URL_JSON = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
DB_NAME = "cs2_skins.db"

def setup_database():
    """Configura la estructura completa de la base de datos (Skins + Precios)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabla de Skins (Datos estáticos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skins (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            rarity TEXT,
            collection TEXT,
            min_float REAL,
            max_float REAL,
            image_url TEXT
        )
    ''')

    # 2. Tabla de Precios (Datos dinámicos)
    # Incluimos esto aquí para no depender de scripts externos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            market_hash_name TEXT PRIMARY KEY,
            price REAL,
            source TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def fetch_and_populate(conn):
    print(f"Descargando datos maestros desde {URL_JSON}...")
    try:
        response = requests.get(URL_JSON)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fatal descargando datos: {e}")
        return

    print(f"Procesando {len(data)} items...")
    
    cursor = conn.cursor()
    batch_data = []
    
    for item in data:
        # Ignorar items sin float (Agentes, Graffitis, etc.)
        if 'min_float' not in item or 'max_float' not in item:
            continue
            
        # Extracción segura de datos anidados
        collection = item['collections'][0]['name'] if item.get('collections') else "Unknown"
        rarity = item['rarity']['name'] if item.get('rarity') else "Unknown"

        # Preparamos tupla para inserción masiva
        batch_data.append((
            item['id'],
            item['name'],
            rarity,
            collection,
            item['min_float'],
            item['max_float'],
            item.get('image')
        ))
    
    # Inserción optimizada (Mucho más rápida que loop simple)
    cursor.executemany('''
        INSERT OR IGNORE INTO skins (id, name, rarity, collection, min_float, max_float, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', batch_data)
    
    conn.commit()
    print(f"¡Éxito! Base de datos inicializada con {len(batch_data)} skins listas.")

if __name__ == "__main__":
    db_conn = setup_database()
    fetch_and_populate(db_conn)
    db_conn.close()