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

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config file not found at {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def run_scrapers(config):
    print("\n--- 🚀 RUNNING SCRAPERS ---")
    
    # Run Daily Dumps first to have a base
    print("🚀 Fetching daily dumps...")
    try:
        daily_dump.fetch_daily_dumps()
    except Exception as e:
        print(f"❌ Error running daily dump: {e}")

    steam_limit = config.get("steam_limit", 50)
    csfloat_limit = config.get("csfloat_limit", 50)
    buff_session = config.get("buff_session", "")

    # Run Steam
    steam.fetch_steam_prices(limit=steam_limit)
    
    # Run CSFloat
    csfloat.fetch_csfloat_prices(limit=csfloat_limit)
    
    # Run Buff (Node.js script)
    print("🚀 Fetching items from Buff (Node.js)...")
    env = os.environ.copy()
    env["BUFF_SESSION"] = buff_session
    buff_script = os.path.join(os.path.dirname(__file__), "scrapers", "buff", "index.js")
    try:
        subprocess.run(["node", buff_script, "weapon_ak47"], env=env, check=True)
        print("✅ Buff scraper finished.")
    except Exception as e:
        print(f"❌ Error running Buff scraper: {e}")

def run_analysis(config):
    print("\n--- 📊 RUNNING ANALYSIS ---")
    rmb_to_usd = config.get("rmb_to_usd", 0.14)
    
    # Arbitrage
    print("🔍 Finding arbitrage opportunities...")
    opps = arbitrage.find_arbitrage_opportunities(rmb_to_usd=rmb_to_usd)
    
    # Contracts
    print("🔍 Hunting for profitable contracts...")
    db = DBManager()
    engine = ContractEngine(db, rmb_to_usd=rmb_to_usd)
    contracts_results = engine.hunt_contracts(
        min_roi=config.get("min_roi", 15.0),
        max_budget=config.get("max_budget", 50.0)
    )
    
    return opps, contracts_results

def generate_reports(arbitrage_opps, contracts_results):
    print("\n--- 📑 GENERATING REPORTS ---")
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    # Arbitrage Report
    arb_file = os.path.join(REPORTS_DIR, "arbitrage_report.csv")
    with open(arb_file, "w", newline="", encoding="utf-8") as f:
        if arbitrage_opps:
            writer = csv.DictWriter(f, fieldnames=arbitrage_opps[0].keys())
            writer.writeheader()
            writer.writerows(arbitrage_opps)
            print(f"✅ Saved arbitrage report to {arb_file} ({len(arbitrage_opps)} rows)")
        else:
            f.write("No opportunities found.")
            print("⚠️ No arbitrage opportunities found.")

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
            print(f"✅ Saved contracts report to {contracts_file} ({len(contracts_results)} rows)")
        else:
            f.write("No profitable contracts found.")
            print("⚠️ No profitable contracts found.")

def main():
    parser = argparse.ArgumentParser(description="CS2 Trade & Arbitrage Bot")
    parser.add_argument("--scrape", action="store_true", help="Run scrapers")
    parser.add_argument("--analyze", action="store_true", help="Run analysis and generate reports")
    parser.add_argument("--all", action="store_true", help="Run everything")
    parser.add_argument("--loop", action="store_true", help="Run the continuous intelligence loop")
    args = parser.parse_args()

    config = load_config()

    if args.loop:
        intelligence_loop.run_continuous_loop(config)
        return

    if args.all or (not args.scrape and not args.analyze and not args.loop):
        run_scrapers(config)
        arb, con = run_analysis(config)
        generate_reports(arb, con)
    else:
        if args.scrape:
            run_scrapers(config)
        if args.analyze:
            arb, con = run_analysis(config)
            generate_reports(arb, con)

    print("\n🏁 Done!")

if __name__ == "__main__":
    main()
