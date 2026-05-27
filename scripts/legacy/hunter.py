import sqlite3
import time
import profit_engine
from app.core import math_engine

# CONFIGURACIÓN
MIN_ROI = 10.0
MAX_BUDGET = 25.0
RARITY_TIERS = ['Industrial Grade', 'Mil-Spec Grade', 'Restricted']
COMBOS_TO_TEST = [(9, 1), (5, 5)]
TEST_FLOATS = [0.08, 0.20]
DB_NAME = "cs2_skins.db"

def get_skins_by_rarity(cursor, rarity):
    cursor.execute("SELECT name, collection, min_float, max_float FROM skins WHERE rarity = ?", (rarity,))
    raw_skins = cursor.fetchall()
    valid_skins = []
    for s in raw_skins:
        name, col, min_f, max_f = s
        price = profit_engine.get_real_price(name, "Field-Tested")
        if price > 0:
            valid_skins.append({
                'name': name, 'collection': col, 'min': min_f, 'max': max_f,
                'price': price, 'rarity': rarity
            })
    valid_skins.sort(key=lambda x: x['price'])
    return valid_skins

def generate_mixed_inputs(target_skin, filler_skin, ratio_target, ratio_filler, test_float):
    inputs = []
    for _ in range(ratio_target):
        inputs.append({
            'collection': target_skin['collection'], 'rarity': target_skin['rarity'],
            'float': test_float, 'min_float': target_skin['min'], 'max_float': target_skin['max'],
            'name': target_skin['name']
        })
    for _ in range(ratio_filler):
        inputs.append({
            'collection': filler_skin['collection'], 'rarity': filler_skin['rarity'],
            'float': test_float, 'min_float': filler_skin['min'], 'max_float': filler_skin['max'],
            'name': filler_skin['name']
        })
    return inputs

def get_wear_threshold(wear_name):
    if wear_name == "Factory New": return 0.07
    if wear_name == "Minimal Wear": return 0.15
    if wear_name == "Field-Tested": return 0.38
    if wear_name == "Well-Worn": return 0.45
    return 1.00

def calculate_safety_limit(cursor, best_outcome_skin, target_wear):
    cursor.execute("SELECT min_float, max_float FROM skins WHERE name = ?", (best_outcome_skin,))
    caps = cursor.fetchone()
    if not caps: return 1.0
    min_cap, max_cap = caps
    threshold = get_wear_threshold(target_wear)
    float_range = max_cap - min_cap
    if float_range == 0: return 1.0
    max_avg_required = (threshold - min_cap) / float_range
    return min(max_avg_required, 1.0)

def generate_buying_recipe(max_avg_float):
    total_budget = max_avg_float * 10.0
    cost_9_mw = 9 * 0.08
    remainder_mw = total_budget - cost_9_mw
    
    if 0.0 < remainder_mw < 0.07:
        return f"      • ESTRATEGIA:         9x Float ~0.08 + 1x Float < {remainder_mw:.4f}"

    if max_avg_float < 0.07:
        cost_9_fn = 9 * 0.05
        remainder_fn = total_budget - cost_9_fn
        if remainder_fn > 0.0:
            return f"      • ESTRATEGIA:         9x Float ~0.05 + 1x Float < {remainder_fn:.4f}"
            
    return f"      • ESTRATEGIA:         Buscar 10x skins con float aprox {max_avg_float:.4f}"

def hunter_v5():
    print(f"\n🚀 INICIANDO HUNTER V5 (ULTIMATE REPORT)")
    print(f"🎯 ROI > {MIN_ROI}% | Win Chance > 15% | Full Financial Details")
    print("=" * 60)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    results_found = 0
    start_time = time.time()

    with open("hunter_results.txt", "w", encoding="utf-8") as f:
        f.write("=== REPORTE DE CAZA ULTIMATE ===\n\n")

        for rarity in RARITY_TIERS:
            print(f"\n📦 Rareza: {rarity}...")
            skins = get_skins_by_rarity(cursor, rarity)
            if len(skins) < 2: continue

            fillers = skins[:5]
            targets = skins[5:]

            for target in targets:
                if target['price'] > MAX_BUDGET: continue

                for filler in fillers:
                    if target['collection'] == filler['collection']: continue

                    for ratio_t, ratio_f in COMBOS_TO_TEST:
                        for float_val in TEST_FLOATS:
                            wear_name = math_engine.get_wear_name(float_val)
                            p_target = profit_engine.get_real_price(target['name'], wear_name)
                            p_filler = profit_engine.get_real_price(filler['name'], wear_name)

                            if p_target == 0 or p_filler == 0: continue

                            real_cost = (p_target * ratio_t) + (p_filler * ratio_f)
                            if real_cost > MAX_BUDGET: continue

                            inputs = generate_mixed_inputs(target, filler, ratio_t, ratio_f, float_val)
                            report = profit_engine.calculate_profitability(inputs)

                            if "error" in report: continue

                            report['cost'] = real_cost
                            report['profit'] = report['revenue'] - real_cost
                            report['roi'] = (report['profit'] / real_cost * 100) if real_cost > 0 else 0

                            if report['roi'] >= MIN_ROI:
                                try:
                                    win_prob = sum(
                                        float(p['probability'].replace('%', ''))
                                        for p in report['outcomes']
                                        if (float(p['sell_price'].replace('$', '').replace(',', '')) * 0.85) > report['cost']
                                    )

                                    if win_prob < 15.0: continue

                                    norm_sum = 0
                                    for inp in inputs:
                                        norm_sum += math_engine.normalize_input_float(inp['float'], inp['min_float'], inp['max_float'])
                                    current_adj_float = norm_sum / 10.0

                                    sorted_outcomes = sorted(
                                        report['outcomes'],
                                        key=lambda x: float(x['sell_price'].replace('$', '').replace(',', ''))
                                    )
                                    best = sorted_outcomes[-1]
                                    worst = sorted_outcomes[0]

                                    max_avg_float = calculate_safety_limit(cursor, best['name'], best['wear'])
                                    total_float_points = max_avg_float * 10.0
                                    safety_buffer = max_avg_float - current_adj_float
                                    safety_icon = "🟢" if safety_buffer > 0.02 else "⚠️" if safety_buffer > 0 else "🛑"
                                    
                                    recipe_str = generate_buying_recipe(max_avg_float)

                                    ev_taxed = report['revenue']
                                    ev_raw = 0.0
                                    for o in report['outcomes']:
                                        p_sell = float(o['sell_price'].replace('$', '').replace(',', ''))
                                        p_prob = float(o['probability'].replace('%', '')) / 100.0
                                        ev_raw += p_sell * p_prob

                                    profitability_fees = (ev_taxed / real_cost) * 100
                                    profitability_no_fees = (ev_raw / real_cost) * 100
                                    avg_profit_fees = ev_taxed - real_cost
                                    avg_profit_no_fees = ev_raw - real_cost

                                    best_float_val = float(best['float'])
                                    worst_float_val = float(worst['float'])

                                    result_str = (
                                        f"✅ [JOYA] {ratio_t}x {target['name']} + {ratio_f}x {filler['name']}\n"
                                        f"   🛒 GUÍA DE COMPRA DETALLADA:\n"
                                        f"      💲 PRECIOS DE COMPRA (POR UNIDAD):\n"
                                        f"         • {target['name']}: ${p_target:.2f}\n"
                                        f"         • {filler['name']}: ${p_filler:.2f}\n"
                                        f"      ---------------------------------------------------\n"
                                        f"{recipe_str}\n"
                                        f"      • FILTRO FLOAT:       < {max_avg_float:.5f} (Promedio Máximo)\n"
                                        f"      • PUNTOS TOTALES:     {total_float_points:.4f} (Suma de los 10 floats)\n"
                                        f"      • MARGEN SEGURIDAD:   {safety_icon} ({safety_buffer:.4f})\n"
                                        f"   ----------------------------------------\n"
                                        f"   📈 REPORTE FINANCIERO\n"
                                        f"   COSTO CONTRATO:          ${real_cost:.2f}\n"
                                        f"   ADJ. AVG. FLOAT:         {current_adj_float:.10f}\n"
                                        f"   ----------------------------------------\n"
                                        f"   PROFITABILITY (Fees):    {profitability_fees:.2f}%\n"
                                        f"   PROFITABILITY (No Fees): {profitability_no_fees:.2f}%\n"
                                        f"   ----------------------------------------\n"
                                        f"   PROFIT/TRADEUP (Fees):   ${avg_profit_fees:.2f}\n"
                                        f"   PROFIT/TRADEUP (No Fees):${avg_profit_no_fees:.2f}\n"
                                        f"   ----------------------------------------\n"
                                        f"   ODDS TO PROFIT:          {win_prob:.2f}%\n"
                                        f"   BEST ITEM:               {best['sell_price']} ({best['name']} - {best['wear']})\n"
                                        f"      -> Output Float: {best_float_val:.9f}\n"
                                        f"   WORST ITEM:              {worst['sell_price']} ({worst['name']} - {worst['wear']})\n"
                                        f"      -> Output Float: {worst_float_val:.9f}\n"
                                        f"   ============================================================\n\n"
                                    )

                                    print(f"   ✨ {target['name']} (ROI: {report['roi']:.0f}%)")
                                    f.write(result_str)
                                    results_found += 1

                                except Exception as e:
                                    continue

    conn.close()
    elapsed = time.time() - start_time
    print(f"\n🏁 FINALIZADO: {results_found} contratos rentables encontrados en {elapsed:.2f}s.")
    print("📂 Revisa 'hunter_results.txt'")

if __name__ == "__main__":
    hunter_v5()