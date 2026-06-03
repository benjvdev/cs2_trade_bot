import time
import os
import subprocess
from app.scrapers import daily_dump, steam, csfloat
from app.core import arbitrage
from app.core.contracts import ContractEngine
from app.database.db_manager import DBManager
from app.core.config import Settings
from app.utils.logger import bot_logger

def run_continuous_loop(config: Settings, max_cycles=None):
    bot_logger.info("--- 🔄 STARTING CONTINUOUS INTELLIGENCE LOOP ---")
    
    # 1. Ensure the Daily Dump is fresh
    bot_logger.info("Fetching daily dumps...")
    daily_dump.fetch_daily_dumps()
    
    rmb_to_usd = config.rmb_to_usd
    batch_size = config.batch_size
    sleep_time = config.batch_sleep
    completed_cycles = 0
    
    while True:
        bot_logger.info("--- 🧠 New Intelligence Cycle ---")
        
        # 2. Use the analysis engines to find the top theoretical opportunities
        bot_logger.info("🔍 Analyzing theoretical arbitrage opportunities...")
        arb_opps = arbitrage.find_arbitrage_opportunities(rmb_to_usd=rmb_to_usd)
        
        bot_logger.info("🔍 Analyzing theoretical contract opportunities...")
        db = DBManager()
        engine = ContractEngine(db, rmb_to_usd=rmb_to_usd)
        contracts_results = engine.hunt_contracts(
            min_roi=config.min_roi,
            max_budget=config.max_budget
        )
        
        # Combine opportunities (just take top ones)
        top_arb = arb_opps[:200]
        
        if not top_arb:
            bot_logger.info("No theoretical opportunities found. Sleeping...")
            completed_cycles += 1
            if max_cycles is not None and completed_cycles >= max_cycles:
                return
            time.sleep(sleep_time)
            continue
            
        # 3. Process them in batches
        total_batches = (len(top_arb) + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            batch = top_arb[i*batch_size : (i+1)*batch_size]
            batch_names = [b['name'] for b in batch]
            bot_logger.info(f"📦 Processing batch {i+1}/{total_batches} ({len(batch)} items)")
            
            # 4. For each batch, trigger live scrapers
            steam_limit = config.steam_limit
            csfloat_limit = config.csfloat_limit
            buff_session = config.buff_session
            
            bot_logger.info("🚀 Triggering live scrapers...")
            try:
                steam.fetch_steam_prices(limit=steam_limit)
            except Exception as e:
                bot_logger.error(f"⚠️ Steam scraper failed: {e}")

            try:
                csfloat.fetch_csfloat_prices(
                    limit=csfloat_limit,
                    settings=config,
                    market_hash_names=batch_names,
                )
            except Exception as e:
                bot_logger.error(f"⚠️ CSFloat scraper failed: {e}")
            
            # Try to determine category for Buff verification
            # For now, we still use weapon_ak47 but we could rotate or target
            env = os.environ.copy()
            env["BUFF_SESSION"] = buff_session
            buff_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scrapers", "buff", "index.js")
            
            # Simple rotation or targeting logic could go here
            try:
                subprocess.run(["node", buff_script, "weapon_ak47"], env=env, check=True)
            except Exception as e:
                bot_logger.error(f"⚠️ Buff scraper failed: {e}")
                
            # 5. Log verified results
            try:
                bot_logger.info("✅ Validating results with fresh data...")
                verified_arb_opps = arbitrage.find_arbitrage_opportunities(rmb_to_usd=rmb_to_usd)
                
                verified_in_batch = [opp for opp in verified_arb_opps if opp['name'] in batch_names and opp['profit'] > 0]
                
                if verified_in_batch:
                    bot_logger.info(f"🎯 Found {len(verified_in_batch)} VERIFIED opportunities in this batch!")
                    for opp in verified_in_batch[:5]:
                        bot_logger.info(f"   💰 {opp['name']} | Profit: ${opp['profit']:.2f} | ROI: {opp['roi']:.2f}% | Buy: {opp['buy_source']} -> Sell: {opp['sell_source']}")
                else:
                    bot_logger.warning("No verified opportunities maintained their profit margin in this batch.")
            except Exception as e:
                bot_logger.error(f"⚠️ Validation failed: {e}")
            
            if i == total_batches - 1:
                completed_cycles += 1
                if max_cycles is not None and completed_cycles >= max_cycles:
                    return

            # 6. Sleep between batches
            bot_logger.info(f"⏳ Cooling down for {sleep_time} seconds to avoid bans...")
            try:
                time.sleep(sleep_time)
            except KeyboardInterrupt:
                bot_logger.info("🛑 Loop interrupted by user. Exiting gracefully...")
                return
            
    bot_logger.info("🏁 Cycle complete.")

