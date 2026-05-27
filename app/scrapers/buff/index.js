const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Absolute path to the SQLite database - Adjusted to match the project root
const DB_PATH = path.resolve(__dirname, '../../../cs2_skins.db');

/**
 * Fetches prices from Buff163 for a specific category and saves them to the database.
 * @param {string} category - The item category (e.g., 'knife_butterfly', 'weapon_ak47')
 * @param {string} sessionCookie - The 'session' cookie value for authentication
 */
async function fetchBuffPrices(category, sessionCookie) {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();

    // Set the session cookie for buff.163.com to bypass login
    await context.addCookies([
        {
            name: 'session',
            value: sessionCookie,
            domain: 'buff.163.com',
            path: '/'
        }
    ]);

    const page = await context.newPage();
    const url = `https://buff.163.com/api/market/goods?game=csgo&page_num=1&category=${category}`;

    const db = new sqlite3.Database(DB_PATH);

    try {
        console.log(`[Buff] Starting fetch for category: ${category}`);

        // Intercept the API response to get the raw JSON data
        const responsePromise = page.waitForResponse(response => 
            response.url().includes('/api/market/goods') && response.status() === 200
        );

        // Add random delay (1-3 seconds) to mimic human behavior
        await page.waitForTimeout(Math.random() * 2000 + 1000);

        await page.goto(url);

        const response = await responsePromise;
        const data = await response.json();

        // Error handling for session expiration or API errors
        if (data.code !== 'OK') {
            console.error(`[Buff] API Error: ${data.code}`);
            if (data.code === 'Login Required') {
                throw new Error('Buff session expired or invalid. Please update cookies.');
            }
            return;
        }

        const items = data.data.items;
        console.log(`[Buff] Successfully retrieved ${items.length} items.`);

        // Prepare data for batch insertion inside a Promise to ensure we await completion
        await new Promise((resolve, reject) => {
            db.serialize(() => {
                const stmt = db.prepare(`
                    INSERT OR REPLACE INTO prices (market_hash_name, price, source, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                `);

                items.forEach(item => {
                    const name = item.market_hash_name;
                    const price = parseFloat(item.sell_min_price);
                    stmt.run(name, price, 'buff');
                });

                stmt.finalize(err => {
                    if (err) {
                        console.error(`[Buff] Finalize error: ${err.message}`);
                        return reject(err);
                    }
                    console.log(`[Buff] Database updated for ${items.length} items.`);
                    resolve();
                });
            });
        });

    } catch (error) {
        console.error(`[Buff] Critical failure: ${error.message}`);
    } finally {
        db.close();
        await browser.close();
    }
}

// CLI Support for manual testing
if (require.main === module) {
    const category = process.argv[2] || 'knife_butterfly';
    const session = process.env.BUFF_SESSION;
    
    if (!session) {
        console.error('Error: Please set the BUFF_SESSION environment variable.');
        process.exit(1);
    }
    
    fetchBuffPrices(category, session);
}

module.exports = { fetchBuffPrices };
