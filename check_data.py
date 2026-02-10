import sqlite3

DB_NAME = "cs2_skins.db"

def search_skin(query):
    """Busca y muestra detalles técnicos de una skin en la DB."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"\n--- Resultados para '{query}' ---")
    
    cursor.execute("SELECT name, min_float, max_float, rarity, collection FROM skins WHERE name LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()

    if not results:
        print("❌ No se encontraron coincidencias.")
    
    for row in results:
        print(f"Skin:      {row[0]}")
        print(f"Floats:    {row[1]} - {row[2]}")
        print(f"Rareza:    {row[3]}")
        print(f"Colección: {row[4]}")
        print("-" * 40)

    conn.close()

if __name__ == "__main__":
    term = input("Ingresa el nombre (o parte) de la skin a buscar: ")
    search_skin(term)