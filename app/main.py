import os
import json
import csv
import argparse
import subprocess
from app.scrapers import steam, csfloat, daily_dump
from app.core import arbitrage
from app.core.contracts import ContractEngine
from app.core import intelligence_loop
from app.database.db_manager import DBManager
from app.core.config import load_settings
from app.utils.logger import bot_logger

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

def run_scrapers(config):
    status = {
        "daily_dump": False,
        "steam": False,
        "csfloat": False,
        "buff": False,
    }
    bot_logger.info("--- 🚀 RUNNING SCRAPERS ---")
    
    # Run Daily Dumps first to have a base
    bot_logger.info("🚀 Fetching daily dumps...")
    try:
        daily_dump_status = daily_dump.fetch_daily_dumps()
        if isinstance(daily_dump_status, dict):
            status["daily_dump"] = any(bool(source_status) for source_status in daily_dump_status.values())
        else:
            status["daily_dump"] = bool(daily_dump_status)
    except Exception as e:
        bot_logger.error(f"❌ Error running daily dump: {e}")

    steam_limit = config.steam_limit
    csfloat_limit = config.csfloat_limit
    buff_session = config.buff_session

    failed_scrapers = []

    # Run Steam
    try:
        status["steam"] = bool(steam.fetch_steam_prices(limit=steam_limit))
    except Exception as e:
        bot_logger.error(f"❌ Error running Steam scraper: {e}")
        status["steam"] = False
    if not status["steam"]:
        failed_scrapers.append("Steam")
    
    # Run CSFloat
    try:
        status["csfloat"] = bool(csfloat.fetch_csfloat_prices(limit=csfloat_limit, settings=config))
    except Exception as e:
        bot_logger.error(f"❌ Error running CSFloat scraper: {e}")
        status["csfloat"] = False
    if not status["csfloat"]:
        failed_scrapers.append("CSFloat")

    if failed_scrapers:
        bot_logger.warning(f"Failed scrapers: {', '.join(failed_scrapers)}")
    
    # Run Buff (Node.js script)
    bot_logger.info("🚀 Fetching items from Buff (Node.js)...")
    env = os.environ.copy()
    env["BUFF_SESSION"] = buff_session
    buff_script = os.path.join(os.path.dirname(__file__), "scrapers", "buff", "index.js")
    try:
        subprocess.run(["node", buff_script, "weapon_ak47"], env=env, check=True)
        status["buff"] = True
        bot_logger.info("✅ Buff scraper finished.")
    except Exception as e:
        bot_logger.error(f"❌ Error running Buff scraper: {e}")

    return status

def run_analysis(config):
    bot_logger.info("--- 📊 RUNNING ANALYSIS ---")
    rmb_to_usd = config.rmb_to_usd
    
    # Arbitrage
    bot_logger.info("🔍 Finding arbitrage opportunities...")
    opps = arbitrage.find_arbitrage_opportunities(
        rmb_to_usd=rmb_to_usd,
        min_roi=config.min_roi,
    )
    
    # Contracts
    bot_logger.info("🔍 Hunting for profitable contracts...")
    db = DBManager()
    engine = ContractEngine(db, rmb_to_usd=rmb_to_usd)
    contracts_results = engine.hunt_contracts(
        min_roi=config.min_roi,
        max_budget=config.max_budget
    )
    
    return opps, contracts_results

def generate_reports(arbitrage_opps, contracts_results):
    bot_logger.info("--- 📑 GENERATING REPORTS ---")
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    # Arbitrage Report
    arb_file = os.path.join(REPORTS_DIR, "arbitrage_report.csv")
    with open(arb_file, "w", newline="", encoding="utf-8") as f:
        if arbitrage_opps:
            writer = csv.DictWriter(f, fieldnames=arbitrage_opps[0].keys())
            writer.writeheader()
            writer.writerows(arbitrage_opps)
            bot_logger.info(f"✅ Saved arbitrage report to {arb_file} ({len(arbitrage_opps)} rows)")
        else:
            f.write("No opportunities found.")
            bot_logger.warning("⚠️ No arbitrage opportunities found.")

    # Contracts Report
    contracts_file = os.path.join(REPORTS_DIR, "contracts_report.csv")
    with open(contracts_file, "w", newline="", encoding="utf-8") as f:
        if contracts_results:
            # Flatten the report for CSV
            fieldnames = ["cost", "revenue", "profit", "roi", "main_outcome"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for res in contracts_results:
                row = {
                    "cost": f"{res['cost']:.2f}",
                    "revenue": f"{res['revenue']:.2f}",
                    "profit": f"{res['profit']:.2f}",
                    "roi": f"{res['roi']:.2f}%",
                    "main_outcome": res["outcomes"][0]["name"] if res["outcomes"] else "N/A"
                }
                writer.writerow(row)
            bot_logger.info(f"✅ Saved contracts report to {contracts_file} ({len(contracts_results)} rows)")
        else:
            f.write("No profitable contracts found.")
            bot_logger.warning("⚠️ No profitable contracts found.")

def main():
    parser = argparse.ArgumentParser(description="CS2 Trade & Arbitrage Bot")
    parser.add_argument("--scrape", action="store_true", help="Run scrapers")
    parser.add_argument("--analyze", action="store_true", help="Run analysis and generate reports")
    parser.add_argument("--all", action="store_true", help="Run everything")
    parser.add_argument("--loop", action="store_true", help="Run the continuous intelligence loop")
    args = parser.parse_args()

    config = load_settings(CONFIG_PATH)

    if args.loop:
        intelligence_loop.run_continuous_loop(config)
        return

    if args.all or (not args.scrape and not args.analyze and not args.loop):
        scrape_status = run_scrapers(config)
        if scrape_status and not any(scrape_status.values()):
            raise RuntimeError("All scrapers failed; refusing to analyze stale data.")
        arb, con = run_analysis(config)
        generate_reports(arb, con)
    else:
        if args.scrape:
            run_scrapers(config)
        if args.analyze:
            arb, con = run_analysis(config)
            generate_reports(arb, con)

    bot_logger.info("🏁 Done!")

if __name__ == "__main__":
    main()
