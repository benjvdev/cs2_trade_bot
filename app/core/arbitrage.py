from collections.abc import Mapping

from app.database.db_manager import DBManager
from app.utils.logger import bot_logger

DEFAULT_TRUSTED_SOURCES = {
    'buff',
    'dump_buff',
    'steam',
    'dump_steam',
    'csfloat',
    'skinport',
    'dump_skinport',
    'skinbaron',
    'dump_skinbaron',
}

FEES = {
    'buff': 0.025,
    'dump_buff': 0.025,
    'steam': 0.15,
    'dump_steam': 0.15,
    'csfloat': 0.02,
    'skinport': 0.12,
    'dump_skinport': 0.12,
    'skinbaron': 0.15,
    'dump_skinbaron': 0.15,
    'csgobackpack': 0.15,
}


def _fetch_price_rows(db_manager):
    get_records = getattr(db_manager, 'get_all_price_records', None)
    if callable(get_records):
        rows = get_records()
        if isinstance(rows, (list, tuple)):
            return rows

    return db_manager.get_all_prices()


def _price_row_fields(row):
    if isinstance(row, Mapping):
        return row['market_hash_name'], row['price'], row['source']

    return row[0], row[1], row[2]


def find_arbitrage_opportunities(rmb_to_usd=0.14, db_manager=None, min_roi=0.0, trusted_sources=None):
    """
    Identifies arbitrage opportunities where an item can be bought low on one market 
    and sold for a net profit on another.
    """
    if db_manager is None:
        db_manager = DBManager()
    if trusted_sources is None:
        trusted_sources = DEFAULT_TRUSTED_SOURCES
    else:
        trusted_sources = set(trusted_sources)
        
    try:
        # Fetch all available price data via DBManager
        rows = _fetch_price_rows(db_manager)
    except Exception as e:
        bot_logger.error(f"Database error in arbitrage engine: {e}")
        return []

    # Group prices by item and market (consolidating dump/live)
    items = {}
    for row in rows:
        name, price, source = _price_row_fields(row)
        if source not in trusted_sources:
            continue

        if name not in items:
            items[name] = {}
        
        # Determine base market name (e.g., 'dump_steam' -> 'steam')
        market_base = source.replace('dump_', '')
        
        # Prioritize live over dump: 
        # If we don't have this market yet, OR if this is a live source (doesn't start with dump_)
        if market_base not in items[name] or not source.startswith('dump_'):
            items[name][market_base] = (price, source)
        
    opportunities = []
    for name, markets in items.items():
        if len(markets) < 2:
            continue
            
        # Net Sale Calculation (after fees)
        net_sales = {}
        # Buy Cost Calculation (actual USD cost)
        buy_costs = {}

        for market_base, (price, source) in markets.items():
            fee = FEES.get(source, 0)
            
            # Convert to USD
            usd_price = price
            if market_base == 'buff':
                usd_price = price * rmb_to_usd
            
            buy_costs[source] = usd_price
            net_sales[source] = usd_price * (1 - fee)

        # Find best buy source and best sell source
        for b_source, b_price in buy_costs.items():
            for s_source, s_net in net_sales.items():
                if b_source == s_source:
                    continue
                
                if b_price < s_net:
                    profit = s_net - b_price
                    roi = (profit / b_price) * 100
                    if roi >= min_roi:
                        opportunities.append({
                            'name': name,
                            'buy_source': b_source,
                            'sell_source': s_source,
                            'buy_price': b_price,
                            'sell_price_net': s_net,
                            'profit': profit,
                            'roi': roi
                        })
            
    return sorted(opportunities, key=lambda x: x['profit'], reverse=True)
