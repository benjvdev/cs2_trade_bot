import sqlite3
from collections import defaultdict

RARITY_ORDER = [
    "Consumer Grade", "Industrial Grade", "Mil-Spec Grade", 
    "Restricted", "Classified", "Covert"
]

def get_next_rarity(current_rarity):
    """Devuelve la siguiente rareza en la cadena de ascenso."""
    try:
        idx = RARITY_ORDER.index(current_rarity)
        if idx + 1 < len(RARITY_ORDER):
            return RARITY_ORDER[idx + 1]
    except ValueError:
        pass
    return None

def fetch_possible_outcomes(cursor, collection, target_rarity):
    """Busca en la DB los posibles resultados de una colección y rareza."""
    query = "SELECT DISTINCT id, name, min_float, max_float, collection FROM skins WHERE collection = ? AND rarity = ?"
    cursor.execute(query, (collection, target_rarity))
    
    return [
        {"id": r[0], "name": r[1], "min_float": r[2], "max_float": r[3], "collection": r[4]}
        for r in cursor.fetchall()
    ]

def simulate_contract_probabilities(inputs_data):
    """
    Calcula las probabilidades de salida basándose en la cantidad de inputs por colección.
    Fórmula Valve: P = (Inputs_Colección / 10) * (1 / Outputs_Posibles_Colección)
    """
    conn = sqlite3.connect("cs2_skins.db")
    cursor = conn.cursor()
    
    first_rarity = inputs_data[0]['rarity']
    target_rarity = get_next_rarity(first_rarity)
    
    if not target_rarity:
        conn.close()
        raise ValueError(f"No se puede hacer trade-up desde {first_rarity}.")

    # Agrupar inputs por colección
    collection_counts = defaultdict(int)
    for inp in inputs_data:
        collection_counts[inp['collection']] += 1
        
    final_probabilities = []
    
    for collection, input_count in collection_counts.items():
        outcomes = fetch_possible_outcomes(cursor, collection, target_rarity)
        num_outcomes = len(outcomes)
        
        if num_outcomes == 0:
            continue
            
        # Cálculo de probabilidad individual
        chance_per_item = (input_count / 10.0) * (1.0 / num_outcomes)
        
        for outcome in outcomes:
            final_probabilities.append({
                "name": outcome['name'],
                "chance_percent": chance_per_item * 100,
                "min_float": outcome['min_float'],
                "max_float": outcome['max_float'],
                "collection": outcome['collection']
            })

    conn.close()
    return final_probabilities

if __name__ == "__main__":
    print("--- TEST PROBABILIDAD ---")
    try:
        conn = sqlite3.connect("cs2_skins.db")
        # Buscamos cualquier colección válida para testear
        cursor = conn.cursor()
        cursor.execute("SELECT collection FROM skins WHERE rarity='Restricted' LIMIT 1")
        res = cursor.fetchone()
        conn.close()

        if res:
            col = res[0]
            print(f"Probando 10 inputs de: {col}")
            inputs = [{'collection': col, 'rarity': 'Restricted'} for _ in range(10)]
            
            results = simulate_contract_probabilities(inputs)
            total = sum(r['chance_percent'] for r in results)
            
            for r in results:
                print(f"{r['chance_percent']:.2f}% -> {r['name']}")
            print(f"Suma Total: {total:.2f}%")
        else:
            print("No hay datos en la DB para ejecutar el test.")
    except Exception as e:
        print(f"Error: {e}")