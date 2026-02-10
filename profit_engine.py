import sqlite3
import contract_simulator
import math_engine

DB_NAME = "cs2_skins.db"
STEAM_TAX = 0.15  # 15% Comisión de Steam (ajustar a 0.02 si usas CSFloat)

def get_real_price(skin_name, wear):
    """Busca el precio de mercado en la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Construimos el nombre exacto: "Skin Name (Condition)"
    full_name = f"{skin_name} ({wear})"
    cursor.execute("SELECT price FROM prices WHERE market_hash_name = ?", (full_name,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else 0.0

def get_avg_price_for_rarity(collection, rarity, wear):
    """Calcula el costo promedio de los inputs de una colección/rareza específica."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM skins WHERE collection=? AND rarity=?", (collection, rarity))
    skins = cursor.fetchall()
    
    total_price = 0
    count = 0
    
    for s in skins:
        price = get_real_price(s[0], wear)
        if price > 0:
            total_price += price
            count += 1
            
    conn.close()
    return (total_price / count) if count > 0 else 0.0

def calculate_profitability(inputs_list):
    """
    Calcula ROI y Beneficio Neto usando precios reales.
    Args: inputs_list (lista de dicts con floats y datos de la skin)
    """
    # 1. Simulación Física (Probabilidades y Floats)
    simulation_results = contract_simulator.simulate_trade_up(inputs_list)
    
    if "error" in simulation_results:
        return simulation_results

    # 2. Calcular Costos (Estimación basada en inputs)
    total_cost = 0
    for inp in inputs_list:
        wear_input = math_engine.get_wear_name(inp['float'])
        # Usamos precio promedio porque en simulaciones no siempre sabemos la skin exacta de input
        avg_price = get_avg_price_for_rarity(inp['collection'], inp['rarity'], wear_input)
        total_cost += avg_price
    
    # 3. Calcular Ingresos (Valor Esperado)
    expected_revenue = 0
    detailed_outcomes = []
    
    for res in simulation_results:
        probability = res['probability'] / 100.0
        sell_price = get_real_price(res['name'], res['wear_outcome'])
        
        post_tax_price = sell_price * (1 - STEAM_TAX)
        revenue_contribution = probability * post_tax_price
        expected_revenue += revenue_contribution
        
        detailed_outcomes.append({
            "name": res['name'],
            "wear": res['wear_outcome'],
            "probability": f"{res['probability']}%",
            "sell_price": f"${sell_price:.2f}",
            "contribution": f"${revenue_contribution:.4f}"
        })

    profit = expected_revenue - total_cost
    roi = (profit / total_cost * 100) if total_cost > 0 else 0.0
    
    return {
        "cost": total_cost,
        "revenue": expected_revenue,
        "profit": profit,
        "roi": roi,
        "outcomes": detailed_outcomes
    }

if __name__ == "__main__":
    print("--- TEST DE PROFIT REAL ---")
    
    # Buscamos una colección válida para probar
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT collection, min_float, max_float FROM skins WHERE rarity='Restricted' LIMIT 1")
    data = cur.fetchone()
    conn.close()
    
    if data:
        col, min_cap, max_cap = data
        print(f"Colección: {col}")
        
        # Simulamos 10 inputs Factory New (0.035)
        inputs = []
        for _ in range(10):
            inputs.append({
                'collection': col, 
                'rarity': 'Restricted', 
                'float': 0.035,
                'min_float': min_cap,
                'max_float': max_cap
            })
            
        report = calculate_profitability(inputs)
        
        print(f"Costo:  ${report['cost']:.2f}")
        print(f"Retorno: ${report['revenue']:.2f}")
        print(f"ROI:     {report['roi']:.2f}%")
    else:
        print("No hay datos suficientes en la DB.")