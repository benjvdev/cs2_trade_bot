# Design Spec: Database Manager (Multi-source)

## 1. Overview
The `DBManager` provides a centralized interface for interacting with the SQLite database used by the CS2 Trade & Arbitrage Bot. It handles both static skin data and dynamic price data from multiple sources (Buff, Steam, CSFloat).

## 2. Goals
- Centralize database operations.
- Support multiple price sources for the same item.
- Ensure database integrity and schema consistency.
- Provide simple methods for fetching and updating prices.

## 3. Architecture
The manager uses `sqlite3` and targets `data/cs2_skins.db`.

### 3.1. Schema
#### Table: `skins` (Static Data)
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Unique identifier for the skin. |
| name | TEXT | Market hash name. |
| rarity | TEXT | Item rarity. |
| collection | TEXT | Collection name. |
| min_float | REAL | Minimum wear value. |
| max_float | REAL | Maximum wear value. |
| image_url | TEXT | URL to the item image. |

#### Table: `prices` (Dynamic Data)
| Column | Type | Description |
|--------|------|-------------|
| market_hash_name | TEXT | Market hash name. |
| price | REAL | Current price in USD. |
| source | TEXT | Source of the price (e.g., 'buff', 'steam'). |
| updated_at | TIMESTAMP | Automatic timestamp. |
| **PK** | (name, source) | Composite key to allow multiple sources per item. |

## 4. Implementation Details
### 4.1. Initialization
- Ensure `data/` directory exists.
- Create tables if they do not exist.
- **Migration Logic:** If the `prices` table exists but lacks the composite primary key, it will be recreated or altered to match the new schema.

### 4.2. Key Methods
- `update_price(name, price, source)`: `INSERT OR REPLACE` into `prices`.
- `get_price(name, source)`: `SELECT price` from `prices`.

## 5. Testing Strategy
- A temporary test script `test_db.py` will verify:
    - Database creation.
    - Table creation.
    - Upserting prices from different sources for the same item.
    - Correct retrieval of prices.
