from app.core import math_engine, probability
import sqlite3

class ContractEngine:
    MARKET_FEES = {
        'steam': 0.15,
        'csfloat': 0.02,
        'buff': 0.025,
        'skinport': 0.12,
        'skinbaron': 0.15,
        'csgobackpack': 0.15
    }

    def __init__(self, db_manager, rmb_to_usd=0.14):
        self.db = db_manager
        self.rmb_to_usd = rmb_to_usd

    def get_lowest_price(self, skin_name, wear):
        """Finds the lowest price among available sources including dumps."""
        hash_name = f"{skin_name} ({wear})"
        prices = []
        
        sources = ['steam', 'csfloat', 'buff', 'skinport', 'skinbaron', 'csgobackpack']
        for s in sources:
            # Check live
            p = self.db.get_price(hash_name, s)
            if p is None:
                # Check dump
                p = self.db.get_price(hash_name, f"dump_{s}")
            
            if p is not None:
                if s == 'buff': p *= self.rmb_to_usd
                prices.append(p)
        
        return min(prices) if prices else None

    def calculate_contract_profitability(self, inputs):
        """Calculate ROI and profit based on simulated outcomes and market prices."""
        # 1. Calculate Cost
        total_cost = 0
        for inp in inputs:
            wear = math_engine.get_wear_name(inp['float'])
            p = self.get_lowest_price(inp['name'], wear)
            if p is None:
                return {"error": f"Missing price for {inp['name']} ({wear})"}
            total_cost += p

        # 2. Simulate Outcomes
        try:
            outcomes = probability.simulate_contract_probabilities(inputs)
        except Exception as e:
            return {"error": str(e)}
        
        expected_revenue = 0
        detailed_outcomes = []
        
        for outcome in outcomes:
            prob = outcome['chance_percent'] / 100.0
            out_float = math_engine.calculate_outcome_float(inputs, outcome['min_float'], outcome['max_float'])
            out_wear = math_engine.get_wear_name(out_float)
            
            # Find Highest Net Sell Price across sources
            max_net = 0
            best_source = None
            
            for source, fee in self.MARKET_FEES.items():
                p_sell = self.db.get_price(f"{outcome['name']} ({out_wear})", source)
                if p_sell:
                    if source == 'buff': p_sell *= self.rmb_to_usd
                    net = p_sell * (1 - fee)
                    if net > max_net:
                        max_net = net
                        best_source = source
            
            expected_revenue += prob * max_net
            detailed_outcomes.append({
                "name": outcome['name'],
                "wear": out_wear,
                "float": out_float,
                "probability": outcome['chance_percent'],
                "max_net_revenue": max_net,
                "best_market": best_source
            })

        profit = expected_revenue - total_cost
        roi = (profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "cost": total_cost,
            "revenue": expected_revenue,
            "profit": profit,
            "roi": roi,
            "outcomes": detailed_outcomes
        }

    def hunt_contracts(self, min_roi=10.0, max_budget=25.0):
        """Iterates through tiers to find profitable contract recipes using dump data as filter."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # 1. Load all dump prices for pre-filtering
        cursor.execute("SELECT market_hash_name, price, source FROM prices WHERE source LIKE 'dump_%' OR source = 'csgobackpack'")
        dump_prices = {}
        for name, price, source in cursor.fetchall():
            market_base = source.replace('dump_', '')
            if name not in dump_prices: dump_prices[name] = {}
            dump_prices[name][market_base] = price

        cursor.execute("SELECT name, collection, rarity, min_float, max_float FROM skins")
        all_skins = [
            {'name': r[0], 'collection': r[1], 'rarity': r[2], 'min_float': r[3], 'max_float': r[4]}
            for r in cursor.fetchall()
        ]
        
        # Group by rarity
        by_rarity = {}
        for s in all_skins:
            if s['rarity'] not in by_rarity: by_rarity[s['rarity']] = []
            by_rarity[s['rarity']].append(s)
            
        results = []
        rarity_tiers = ["Industrial Grade", "Mil-Spec Grade", "Restricted", "Classified"]
        
        for rarity in rarity_tiers:
            skins = by_rarity.get(rarity, [])
            if len(skins) < 2: continue
            
            # Pre-filter skins using dump data to save time
            valid_skins = []
            for s in skins:
                # Try to get lowest dump price
                hash_name = f"{s['name']} (Field-Tested)"
                p_list = []
                if hash_name in dump_prices:
                    for m, p in dump_prices[hash_name].items():
                        if m == 'buff': p *= self.rmb_to_usd
                        p_list.append(p)
                
                if p_list:
                    p = min(p_list)
                    if p <= max_budget:
                        s['price'] = p
                        valid_skins.append(s)
            
            valid_skins.sort(key=lambda x: x['price'])
            if len(valid_skins) < 2: continue

            # Optimization: only check cheapest skins as inputs
            inputs_pool = valid_skins[:20]
            fillers = inputs_pool[:5] 
            targets = inputs_pool

            for target in targets:
                for filler in fillers:
                    if target['collection'] == filler['collection']: continue
                    
                    # Test common ratios
                    combos = [(10, 0), (9, 1), (5, 5)]
                    for n_t, n_f in combos:
                        inputs = []
                        for _ in range(n_t): 
                            t_copy = target.copy()
                            t_copy['float'] = 0.08 # Default test float
                            inputs.append(t_copy)
                        for _ in range(n_f):
                            f_copy = filler.copy()
                            f_copy['float'] = 0.08
                            inputs.append(f_copy)
                            
                        report = self.calculate_contract_profitability(inputs)
                        if "error" not in report and report['roi'] >= min_roi:
                            results.append(report)
        
        conn.close()
        return results
