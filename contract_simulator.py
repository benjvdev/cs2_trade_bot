import math_engine
import probability_engine

def simulate_trade_up(input_skins):
    """
    Simula un contrato completo combinando probabilidad y matemáticas de float.
    input_skins: Lista de 10 dicts con keys: collection, rarity, float, min_float, max_float.
    """
    
    if len(input_skins) != 10:
        return {"error": "Se requieren exactamente 10 skins."}
    
    # 1. Calcular Probabilidades
    try:
        possible_outcomes = probability_engine.simulate_contract_probabilities(input_skins)
    except Exception as e:
        return {"error": f"Error en probabilidades: {str(e)}"}
    
    final_results = []
    
    # 2. Calcular Floats y Desgaste
    for outcome in possible_outcomes:
        # La nueva lógica requiere pasar la lista completa de inputs (con sus caps)
        predicted_float = math_engine.calculate_outcome_float(
            input_skins, 
            outcome['min_float'], 
            outcome['max_float']
        )
        predicted_wear = math_engine.get_wear_name(predicted_float)
        
        final_results.append({
            "name": outcome['name'],
            "collection": outcome['collection'],
            "probability": round(outcome['chance_percent'], 2),
            "float_outcome": f"{predicted_float:.9f}",
            "wear_outcome": predicted_wear
        })
        
    final_results.sort(key=lambda x: x['probability'], reverse=True)
    return final_results

# --- ZONA DE PRUEBAS ---
if __name__ == "__main__":
    import sqlite3
    print("--- TEST DE SIMULACIÓN ---")
    
    # Obtenemos una skin real de la DB para usar sus caps correctos en el test
    conn = sqlite3.connect("cs2_skins.db")
    cursor = conn.cursor()
    cursor.execute("SELECT collection, min_float, max_float FROM skins WHERE rarity='Industrial Grade' LIMIT 1")
    ref_skin = cursor.fetchone()
    conn.close()
    
    if ref_skin:
        col, min_cap, max_cap = ref_skin
        print(f"Usando datos reales de: {col} (Caps: {min_cap}-{max_cap})")
        
        test_inputs = []
        for _ in range(10):
            test_inputs.append({
                'collection': col,
                'rarity': 'Industrial Grade',
                'float': 0.012345,
                'min_float': min_cap, # Necesario para math_engine actualizado
                'max_float': max_cap  # Necesario para math_engine actualizado
            })
            
        results = simulate_trade_up(test_inputs)
        
        if "error" in results:
            print(results['error'])
        else:
            print(f"{'PROBABILIDAD':<15} {'FLOAT':<15} {'SKIN'}")
            print("-" * 50)
            for res in results:
                print(f"{res['probability']}%{'':<9} {res['float_outcome']:<15} {res['name']}")
    else:
        print("Error: No hay datos suficientes en la DB para el test.")