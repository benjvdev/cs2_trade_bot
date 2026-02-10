import json
import sqlite3
import os

# Configuración
JSON_FILE = "prices.json"
DB_NAME = "cs2_skins.db"

def update_prices_from_local():
    """Importa precios desde un archivo local prices.json (CSGO Backpack)"""
    
    print(f"📂 Buscando archivo: {JSON_FILE}...")
    
    if not os.path.exists(JSON_FILE):
        print(f"❌ ERROR: Falta '{JSON_FILE}'.")
        print("Descárgalo de: http://csgobackpack.net/api/GetItemsList/v2/")
        return

    print("📖 Leyendo y procesando JSON...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data.get('success'):
            print("❌ JSON inválido (success != true).")
            return

        items = data.get('items_list', {})
        print(f"✅ JSON cargado. Procesando {len(items)} items...")

    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    updates = []
    
    for name, details in items.items():
        price = 0.0
        p_data = details.get("price", {})
        
        # Estrategia de cascada: Priorizamos estabilidad (7 días) sobre inmediatez
        try:
            if "7_days" in p_data:
                price = float(p_data["7_days"].get("average", 0))
            elif "30_days" in p_data:
                price = float(p_data["30_days"].get("average", 0))
            elif "24_hours" in p_data:
                price = float(p_data["24_hours"].get("average", 0))
        except (ValueError, TypeError):
            continue

        if price > 0:
            updates.append((name, price, "steam_backpack"))

    if updates:
        print(f"📥 Insertando {len(updates)} precios en la base de datos...")
        # Borramos precios antiguos para evitar mezclar datos obsoletos
        cursor.execute("DELETE FROM prices")
        
        cursor.executemany('''
            INSERT OR REPLACE INTO prices (market_hash_name, price, source, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', updates)
        
        conn.commit()
        print(f"✅ ¡ÉXITO! Base de datos actualizada con {len(updates)} precios.")
    else:
        print("⚠️ No se extrajeron precios válidos del archivo.")

    conn.close()

if __name__ == "__main__":
    update_prices_from_local()