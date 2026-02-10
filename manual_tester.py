import sqlite3
import contract_simulator
import math_engine
import profit_engine

# ==========================================
# ⚙️ CONFIGURACIÓN DEL CONTRATO (INPUTS)
# ==========================================
# Formato: ("Nombre Exacto", Float)

CONTRACT_INPUTS = [
   ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092), 
    ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092),
    ("Five-SeveN | Orange Peel", 0.092),
    ("FAMAS | Grey Ghost", 0.092),
]

# ==========================================

def get_skin_data(cursor, skin_name):
    query = "SELECT collection, rarity, min_float, max_float FROM skins WHERE name = ?"
    cursor.execute(query, (skin_name,))
    return cursor.fetchone()

def run_manual_test():
    print(f"\n{'='*60}")
    print(f"🔬 ANÁLISIS DE CONTRATO ({len(CONTRACT_INPUTS)} inputs)")
    print(f"{'='*60}")

    if len(CONTRACT_INPUTS) != 10:
        print("❌ Error: Debes configurar exactamente 10 inputs.")
        return

    conn = sqlite3.connect("cs2_skins.db")
    cursor = conn.cursor()
    
    prepared_inputs = []
    normalized_sum = 0.0
    total_cost = 0.0
    
    # Diccionario para guardar precios únicos y no repetir en pantalla
    unique_input_prices = {}

    # 1. Procesar Inputs
    print("🔄 Procesando inputs...")
    for i, (name, float_val) in enumerate(CONTRACT_INPUTS):
        data = get_skin_data(cursor, name)
        
        if not data:
            print(f"❌ Error: No encontré '{name}' en la DB.")
            conn.close()
            return

        col, rarity, min_cap, max_cap = data
        
        # Matemáticas Valve
        norm_val = math_engine.normalize_input_float(float_val, min_cap, max_cap)
        normalized_sum += norm_val
        
        # Finanzas
        wear = math_engine.get_wear_name(float_val)
        price = profit_engine.get_real_price(name, wear)
        total_cost += price
        
        # Guardamos el precio unitario si es una skin nueva
        if name not in unique_input_prices:
            unique_input_prices[name] = {'price': price, 'wear': wear}

        prepared_inputs.append({
            'collection': col, 'rarity': rarity, 'float': float_val,
            'min_float': min_cap, 'max_float': max_cap, 'name': name
        })

    conn.close()
    
    # 2. Mostrar Precios Unitarios (Solo distintos)
    print("-" * 60)
    print("💲 PRECIOS DE INPUTS (Unitario)")
    for name, info in unique_input_prices.items():
        print(f"• {name} ({info['wear']}): ${info['price']:.2f}")
    print("-" * 60)

    # 3. Métricas Técnicas
    adj_avg_float = normalized_sum / 10.0
    
    # 4. Simulación
    resultados = contract_simulator.simulate_trade_up(prepared_inputs)
    
    if "error" in resultados:
        print(f"❌ ERROR: {resultados['error']}")
        return

    # 5. Análisis Financiero Detallado
    ev_taxed = 0.0
    ev_raw = 0.0
    winning_chance = 0.0
    
    best_item = {"name": "N/A", "price": 0.0}
    worst_item = {"name": "N/A", "price": 99999.0}
    
    print("\n📊 RESULTADOS POSIBLES")
    print(f"{'PROB%':<8} {'FLOAT':<12} {'DESGASTE':<14} {'PRECIO':<9} {'PROFIT':<10} {'SKIN'}")
    print("-" * 80)
    
    for res in resultados:
        sell_price = profit_engine.get_real_price(res['name'], res['wear_outcome'])
        prob_dec = res['probability'] / 100.0
        
        # Con Impuestos
        val_taxed = sell_price * (1 - profit_engine.STEAM_TAX)
        profit_neto = val_taxed - total_cost
        
        # Acumuladores EV
        ev_taxed += prob_dec * val_taxed
        ev_raw += prob_dec * sell_price
        
        # Best / Worst Tracking
        if sell_price > best_item["price"]:
            best_item = {"name": res['name'], "price": sell_price, "profit": profit_neto}
        
        if sell_price < worst_item["price"]:
            worst_item = {"name": res['name'], "price": sell_price, "profit": profit_neto}

        # Probabilidad de Ganar
        if profit_neto > 0:
            winning_chance += res['probability']

        symbol = "✅" if profit_neto > 0 else "🔻"
        print(f"{res['probability']}%{'':<3} {res['float_outcome']:<12} {res['wear_outcome']:<14} ${sell_price:<8.2f} {symbol} ${profit_neto:<8.2f} {res['name']}")

    print("-" * 80)
    
    # 6. Reporte Final
    if total_cost > 0:
        profitability_fees = (ev_taxed / total_cost) * 100
        profitability_no_fees = (ev_raw / total_cost) * 100
        avg_profit_fees = ev_taxed - total_cost
        avg_profit_no_fees = ev_raw - total_cost
    else:
        profitability_fees = 0; profitability_no_fees = 0
        avg_profit_fees = 0; avg_profit_no_fees = 0

    print(f"\n📈 REPORTE FINANCIERO")
    print(f"COSTO CONTRATO:          ${total_cost:.2f}")
    print(f"ADJ. AVG. FLOAT:         {adj_avg_float:.10f}")
    print("-" * 40)
    print(f"PROFITABILITY (Fees):    {profitability_fees:.2f}%")
    print(f"PROFITABILITY (No Fees): {profitability_no_fees:.2f}%")
    print("-" * 40)
    print(f"PROFIT/TRADEUP (Fees):   ${avg_profit_fees:.2f}")
    print(f"PROFIT/TRADEUP (No Fees):${avg_profit_no_fees:.2f}")
    print("-" * 40)
    print(f"ODDS TO PROFIT:          {winning_chance:.2f}%")
    print(f"BEST ITEM:               ${best_item['price']:.2f} ({best_item['name']})")
    print(f"WORST ITEM:              ${worst_item['price']:.2f} ({worst_item['name']})")
    print("=" * 60)

if __name__ == "__main__":
    run_manual_test()