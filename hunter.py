import sqlite3
import time
import profit_engine
import math_engine

# ==========================================
# ⚙️ CONFIGURACIÓN DEL CAZADOR V3 (FULL INFO)
# ==========================================
MIN_ROI = 10.0          # Mínimo 10% de retorno para guardarlo
MAX_BUDGET = 25.0       # Presupuesto máximo por contrato
RARITY_TIERS = ['Industrial Grade', 'Mil-Spec Grade', 'Restricted'] 

# Ratios a probar: 9x1 (Riesgo/Video) y 5x5 (Balanceado)
COMBOS_TO_TEST = [(9, 1), (5, 5)] 

# Floats a escanear: MW Bajo (0.08) y FT Bajo (0.20)
TEST_FLOATS = [0.08, 0.20] 
# ==========================================

DB_NAME = "cs2_skins.db"

def get_skins_by_rarity(cursor, rarity):
    """Obtiene skins candidatas ordenadas por precio."""
    query = "SELECT name, collection, min_float, max_float FROM skins WHERE rarity = ?"
    cursor.execute(query, (rarity,))
    raw_skins = cursor.fetchall()
    
    valid_skins = []
    for s in raw_skins:
        name, col, min_f, max_f = s
        # Usamos Field-Tested como referencia de precio base
        price = profit_engine.get_real_price(name, "Field-Tested")
        
        if price > 0:
            valid_skins.append({
                'name': name,
                'collection': col,
                'min': min_f,
                'max': max_f,
                'price': price,
                'rarity': rarity
            })
    
    valid_skins.sort(key=lambda x: x['price'])
    return valid_skins

def generate_mixed_inputs(target_skin, filler_skin, ratio_target, ratio_filler, test_float):
    """Genera la lista de 10 inputs para el simulador."""
    inputs = []
    # Targets
    for _ in range(ratio_target):
        inputs.append({
            'collection': target_skin['collection'], 'rarity': target_skin['rarity'],
            'float': test_float, 'min_float': target_skin['min'], 'max_float': target_skin['max'],
            'name': target_skin['name']
        })
    # Fillers
    for _ in range(ratio_filler):
        inputs.append({
            'collection': filler_skin['collection'], 'rarity': filler_skin['rarity'],
            'float': test_float, 'min_float': filler_skin['min'], 'max_float': filler_skin['max'],
            'name': filler_skin['name']
        })
    return inputs

def hunter_v3():
    print(f"\n🚀 INICIANDO HUNTER V3 (FULL ANALYTICS)")
    print(f"🎯 Buscando contratos con ROI > {MIN_ROI}%")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    results_found = 0
    start_time = time.time()
    
    # Archivo de salida
    with open("hunter_v3_results.txt", "w", encoding="utf-8") as f:
        f.write("=== REPORTE FINANCIERO DE CONTRATOS (HUNTER V3) ===\n\n")

        for rarity in RARITY_TIERS:
            print(f"\n📦 Escaneando rareza: {rarity}...")
            skins = get_skins_by_rarity(cursor, rarity)
            
            if len(skins) < 2: continue
            
            # Estrategia: Top 5 Fillers vs Resto
            fillers = skins[:5] 
            targets = skins[5:] 
            
            print(f"   🔥 Fillers: {len(fillers)} | 🎯 Targets: {len(targets)}")
            
            for target in targets:
                if target['price'] > MAX_BUDGET: continue

                for filler in fillers:
                    if target['collection'] == filler['collection']: continue
                    
                    for ratio_t, ratio_f in COMBOS_TO_TEST:
                        for float_val in TEST_FLOATS:
                            
                            inputs = generate_mixed_inputs(target, filler, ratio_t, ratio_f, float_val)
                            
                            # 1. Simulación Rápida (Profit Engine)
                            report = profit_engine.calculate_profitability(inputs)
                            
                            if "error" in report: continue
                            
                            # Filtro inicial
                            if report['roi'] >= MIN_ROI and 0 < report['cost'] <= MAX_BUDGET:
                                
                                try:
                                    # 2. CÁLCULOS DETALLADOS (Estilo Manual Tester)
                                    
                                    # A) Adj. Avg. Float
                                    norm_sum = 0.0
                                    for inp in inputs:
                                        norm_sum += math_engine.normalize_input_float(inp['float'], inp['min_float'], inp['max_float'])
                                    adj_avg_float = norm_sum / 10.0
                                    
                                    # B) Métricas "Youtube" (Fees vs No Fees)
                                    # Profit Engine devuelve 'revenue' que es YA con fees (Neto).
                                    ev_taxed = report['revenue']
                                    total_cost = report['cost']
                                    
                                    # Recalcular EV Sin Fees (Raw) y Odds
                                    ev_raw = 0.0
                                    winning_chance = 0.0
                                    best_item = {"name": "N/A", "price": -1.0}
                                    worst_item = {"name": "N/A", "price": 999999.0}
                                    
                                    for out in report['outcomes']:
                                        # Limpieza de strings "$10.50" -> 10.50
                                        price_clean = float(out['sell_price'].replace('$', '').replace(',', ''))
                                        prob_clean = float(out['probability'].replace('%', '')) / 100.0
                                        
                                        # EV Bruto
                                        ev_raw += (price_clean * prob_clean)
                                        
                                        # Best/Worst
                                        if price_clean > best_item["price"]:
                                            best_item = {"name": out['name'], "price": price_clean, "wear": out['wear']}
                                        if price_clean < worst_item["price"]:
                                            worst_item = {"name": out['name'], "price": price_clean, "wear": out['wear']}
                                            
                                        # Odds to Profit (Neto > 0)
                                        net_profit = (price_clean * 0.85) - total_cost
                                        if net_profit > 0:
                                            winning_chance += (prob_clean * 100.0)

                                    # Calcular porcentajes finales
                                    profitability_fees = (ev_taxed / total_cost) * 100
                                    profitability_no_fees = (ev_raw / total_cost) * 100
                                    avg_profit_fees = ev_taxed - total_cost
                                    avg_profit_no_fees = ev_raw - total_cost
                                    
                                    # Filtro de seguridad: Ignorar si la chance de ganar es muy baja
                                    if winning_chance < 15.0: continue

                                    # 3. GENERAR REPORTE
                                    wear_input = math_engine.get_wear_name(float_val)
                                    
                                    block = (
                                        f"✅ [JOYA ENCONTRADA] {ratio_t}x {target['name']} + {ratio_f}x {filler['name']}\n"
                                        f"   💎 Input: {float_val} ({wear_input})\n"
                                        f"   ----------------------------------------\n"
                                        f"   COSTO CONTRATO:          ${total_cost:.2f}\n"
                                        f"   ADJ. AVG. FLOAT:         {adj_avg_float:.9f}\n"
                                        f"   ----------------------------------------\n"
                                        f"   PROFITABILITY (Fees):    {profitability_fees:.2f}%\n"
                                        f"   PROFITABILITY (No Fees): {profitability_no_fees:.2f}%\n"
                                        f"   ----------------------------------------\n"
                                        f"   PROFIT/TRADEUP (Fees):   ${avg_profit_fees:.2f}\n"
                                        f"   PROFIT/TRADEUP (No Fees):${avg_profit_no_fees:.2f}\n"
                                        f"   ----------------------------------------\n"
                                        f"   ODDS TO PROFIT:          {winning_chance:.2f}%\n"
                                        f"   🏆 BEST: ${best_item['price']:.2f} - {best_item['name']} ({best_item['wear']})\n"
                                        f"   💀 WORST: ${worst_item['price']:.2f} - {worst_item['name']} ({worst_item['wear']})\n"
                                        f"   ============================================================\n\n"
                                    )
                                    
                                    print(f"   ✨ {target['name']} (ROI: {report['roi']:.1f}%)")
                                    f.write(block)
                                    results_found += 1
                                    
                                except Exception as e:
                                    print(f"Error calculando detalles: {e}")
                                    continue

    conn.close()
    elapsed = time.time() - start_time
    print(f"\n🏁 FINALIZADO: {results_found} contratos encontrados en {elapsed:.2f}s.")
    print("📂 Revisa 'hunter_v3_results.txt'")

if __name__ == "__main__":
    hunter_v3()