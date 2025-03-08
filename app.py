from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
import os
import asyncio
import aiohttp

app = Flask(__name__)

# Load merchants from file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MERCHANTS_FILE = os.path.join(SCRIPT_DIR, "merchants.txt")
try:
    with open(MERCHANTS_FILE, 'r', encoding='utf-8') as f:
        MERCHANTS = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Error: Could not find {MERCHANTS_FILE}")
    MERCHANTS = []

async def fetch_url(session, url, headers):
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        return str(e)

async def get_cashback_percentage(search_term):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    encoded_term = quote(search_term)
    topcashback_term = re.sub(r'\.com(\.au)?', '', search_term, flags=re.IGNORECASE).lower()
    encoded_topcashback_term = quote(topcashback_term)

    async with aiohttp.ClientSession() as session:
        tasks = [
            ("ShopBack", f"https://www.shopback.com.au/search?keyword={encoded_term}"),
            ("TopCashback", f"https://www.topcashback.com.au/search/merchants/?s={encoded_topcashback_term}"),
            ("Cashrewards", f"https://www.cashrewards.com.au/search/?keyword={encoded_term}")
        ]

        for site, url in tasks:
            html = await fetch_url(session, url, headers)
            if isinstance(html, str) and not html.startswith("Error"):
                soup = BeautifulSoup(html, 'html.parser')
                if site == "ShopBack":
                    selector = ".pos_relative.p_12px_8px.smDown\\:p_8px_4px.rounded_16.border_solid_1px_\\{colors\\.sbds-global-color-gray-5\\}.cursor_pointer.hover\\:shadow_0_1px_8px_\\{colors\\.sbds-global-color-gray-10\\}"
                    element = soup.select_one(selector)
                    cashback = "No Cashback Available"
                    if element and element.text:
                        text = element.text.strip()
                        match = re.search(r'(Up to )?(\$?\d+\.?\d*%\s*Cashback|\$\d+\.?\d*\s*Cashback)', text, re.IGNORECASE)
                        if match:
                            cashback = match.group(0)
                elif site == "TopCashback":
                    selector = "#ctl00_GeckoTwoColPrimary_ctl04_price"
                    element = soup.select_one(selector)
                    cashback = element.text.strip() if element else "No Cashback Available"
                elif site == "Cashrewards":
                    selector = "div[class*='grid grid-cols-2 divide-x divide-neutral-100 w-full'] p[class='p font-extrabold text-purple-500 break-words font-primary']"
                    element = soup.select_one(selector)
                    cashback = element.text.strip() if element else "No Cashback Available"
            else:
                cashback = f"Error: {html}"
            yield {"Site": site, "Cashback": cashback, "URL": url}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q', '').lower()
    suggestions = [m for m in MERCHANTS if query in m.lower()]
    return jsonify(suggestions[:10])

@app.route('/search', methods=['POST'])
async def search():
    merchant = request.form.get('merchant')
    if merchant not in MERCHANTS:
        return jsonify({"error": "Merchant not found"}), 400
    results = []
    async for result in get_cashback_percentage(merchant):
        results.append(result)
    return jsonify(results)

@app.route('/merchants', methods=['GET'])
def get_merchants():
    return jsonify(MERCHANTS)

if __name__ == "__main__":
    app.run(debug=True)
