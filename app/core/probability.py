import sqlite3
import os
from collections import defaultdict
from app.utils.logger import bot_logger

# Define DB path relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "cs2_skins.db")

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

def simulate_contract_probabilities(inputs_data, db_path=None):
    """
    Calcula las probabilidades de salida basándose en la cantidad de inputs por colección.
    Fórmula Valve: P = (Inputs_Colección / 10) * (1 / Outputs_Posibles_Colección)
    """
    if len(inputs_data) != 10:
        raise ValueError("A trade-up contract requires exactly 10 inputs.")

    first_rarity = inputs_data[0]['rarity']
    if any(inp['rarity'] != first_rarity for inp in inputs_data):
        raise ValueError("All contract inputs must have the same rarity.")

    conn = sqlite3.connect(db_path or DB_PATH)
    try:
        cursor = conn.cursor()

        target_rarity = get_next_rarity(first_rarity)

        if not target_rarity:
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

        return final_probabilities
    finally:
        conn.close()

if __name__ == "__main__":
    bot_logger.info("--- TEST PROBABILIDAD ---")
    try:
        conn = sqlite3.connect(DB_PATH)
        # Buscamos cualquier colección válida para testear
        cursor = conn.cursor()
        cursor.execute("SELECT collection FROM skins WHERE rarity='Restricted' LIMIT 1")
        res = cursor.fetchone()
        conn.close()

        if res:
            col = res[0]
            bot_logger.info(f"Probando 10 inputs de: {col}")
            inputs = [{'collection': col, 'rarity': 'Restricted'} for _ in range(10)]

            results = simulate_contract_probabilities(inputs)
            total = sum(r['chance_percent'] for r in results)

            for r in results:
                bot_logger.info(f"{r['chance_percent']:.2f}% -> {r['name']}")
            bot_logger.info(f"Suma Total: {total:.2f}%")
        else:
            bot_logger.warning("No hay datos en la DB para ejecutar el test.")
    except Exception as e:
        bot_logger.error(f"Error: {e}")
