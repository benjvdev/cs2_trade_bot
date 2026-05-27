import time
import os
import subprocess
import logging
from app.scrapers import daily_dump, steam, csfloat
from app.core import arbitrage
from app.core.contracts import ContractEngine
from app.database.db_manager import DBManager

logger = logging.getLogger(__name__)

def run_continuous_loop(config):
    print("--- 🔄 STARTING CONTINUOUS INTELLIGENCE LOOP ---")
    
    # 1. Ensure the Daily Dump is fresh
    print("Fetching daily dumps...")
    daily_dump.fetch_daily_dumps()
    
    rmb_to_usd = config.get("rmb_to_usd", 0.14)
    batch_size = config.get("batch_size", 50)
    sleep_time = config.get("batch_sleep", 60)
    
    while True:
        print("\n--- 🧠 New Intelligence Cycle ---")
        
        # 2. Use the analysis engines to find the top theoretical opportunities
        print("🔍 Analyzing theoretical arbitrage opportunities...")
        arb_opps = arbitrage.find_arbitrage_opportunities(rmb_to_usd=rmb_to_usd)
        
        print("🔍 Analyzing theoretical contract opportunities...")
        db = DBManager()
        engine = ContractEngine(db, rmb_to_usd=rmb_to_usd)
        contracts_results = engine.hunt_contracts(
            min_roi=config.get("min_roi", 15.0),
            max_budget=config.get("max_budget", 50.0)
        )
        
        # Combine opportunities (just take top ones)
        top_arb = arb_opps[:200]
        
        if not top_arb:
            print("No theoretical opportunities found. Sleeping...")
            time.sleep(sleep_time)
            continue
            
        # 3. Process them in batches
        total_batches = (len(top_arb) + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            batch = top_arb[i*batch_size : (i+1)*batch_size]
            print(f"\n📦 Processing batch {i+1}/{total_batches} ({len(batch)} items)")
            
            # 4. For each batch, trigger live scrapers
            steam_limit = config.get("steam_limit", 100)
            csfloat_limit = config.get("csfloat_limit", 100)
            buff_session = config.get("buff_session", "")
            
            print("🚀 Triggering live scrapers...")
            try:
                steam.fetch_steam_prices(limit=steam_limit)
            except Exception as e:
                print(f"⚠️ Steam scraper failed: {e}")

            try:
                csfloat.fetch_csfloat_prices(limit=csfloat_limit)
            except Exception as e:
                print(f"⚠️ CSFloat scraper failed: {e}")
            
            # Try to determine category for Buff verification
            # For now, we still use weapon_ak47 but we could rotate or target
            env = os.environ.copy()
            env["BUFF_SESSION"] = buff_session
            buff_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scrapers", "buff", "index.js")
            
            # Simple rotation or targeting logic could go here
            try:
                subprocess.run(["node", buff_script, "weapon_ak47"], env=env, check=True)
            except Exception as e:
                print(f"⚠️ Buff scraper failed: {e}")
                
            # 5. Log verified results
            try:
                print("✅ Validating results with fresh data...")
                verified_arb_opps = arbitrage.find_arbitrage_opportunities(rmb_to_usd=rmb_to_usd)
                
                batch_names = [b['name'] for b in batch]
                verified_in_batch = [opp for opp in verified_arb_opps if opp['name'] in batch_names and opp['profit'] > 0]
                
                if verified_in_batch:
                    print(f"🎯 Found {len(verified_in_batch)} VERIFIED opportunities in this batch!")
                    for opp in verified_in_batch[:5]:
                        print(f"   💰 {opp['name']} | Profit: ${opp['profit']:.2f} | ROI: {opp['roi']:.2f}% | Buy: {opp['buy_source']} -> Sell: {opp['sell_source']}")
                else:
                    print("⚠️ No verified opportunities maintained their profit margin in this batch.")
            except Exception as e:
                print(f"⚠️ Validation failed: {e}")
            
            # 6. Sleep between batches
            print(f"⏳ Cooling down for {sleep_time} seconds to avoid bans...")
            try:
                time.sleep(sleep_time)
            except KeyboardInterrupt:
                print("\n🛑 Loop interrupted by user. Exiting gracefully...")
                return
            
        print("🏁 Cycle complete.")
