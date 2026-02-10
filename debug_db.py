import sqlite3

def check_database_health():
    conn = sqlite3.connect("cs2_skins.db")
    cursor = conn.cursor()
    
    print("🏥 DIAGNÓSTICO DE BASE DE DATOS")
    print("=" * 40)
    
    # 1. ¿Hay skins?
    cursor.execute("SELECT count(*) FROM skins")
    total_skins = cursor.fetchone()[0]
    print(f"📦 Total Skins en DB:      {total_skins}")
    
    # 2. ¿Hay precios?
    cursor.execute("SELECT count(*) FROM prices")
    total_prices = cursor.fetchone()[0]
    print(f"💰 Total Precios en DB:    {total_prices}")
    
    # 3. ¿Hay precios válidos (> 0)?
    cursor.execute("SELECT count(*) FROM prices WHERE price > 0")
    valid_prices = cursor.fetchone()[0]
    print(f"✅ Precios Válidos (> $0): {valid_prices}")
    
    print("-" * 40)
    
    # 4. Prueba Específica (Lo que usa el Hunter)
    # Buscamos una skin común para ver si tiene precio en Field-Tested
    test_skin = "AK-47 | Safari Mesh"
    wear = "Field-Tested"
    full_name = f"{test_skin} ({wear})"
    
    print(f"🔎 Buscando: '{full_name}'")
    
    cursor.execute("SELECT price FROM prices WHERE market_hash_name = ?", (full_name,))
    res = cursor.fetchone()
    
    if res:
        print(f"   💲 Precio encontrado: ${res[0]}")
    else:
        print(f"   ❌ NO TIENE PRECIO. El Hunter la ignorará.")
        
        # Intento de ver qué hay parecido
        print(f"   Revisando si existe con otro nombre...")
        cursor.execute("SELECT market_hash_name, price FROM prices WHERE market_hash_name LIKE '%Safari Mesh%' LIMIT 3")
        similares = cursor.fetchall()
        for s in similares:
            print(f"   -> Encontré: {s[0]} = ${s[1]}")

    conn.close()

if __name__ == "__main__":
    check_database_health()