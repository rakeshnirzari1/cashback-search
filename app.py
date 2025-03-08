from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

app = Flask(__name__)

# Load merchants from file in the same directory as app.py
MERCHANTS_FILE = "merchants.txt"
with open(MERCHANTS_FILE, 'r', encoding='utf-8') as f:
    MERCHANTS = [line.strip() for line in f if line.strip()]

def get_cashback_percentage(search_term):
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    topcashback_term = re.sub(r'\.com(\.au)?', '', search_term, flags=re.IGNORECASE).lower()
    encoded_term = quote(search_term)
    encoded_topcashback_term = quote(topcashback_term)

    # ShopBack
    shopback_url = f"https://www.shopback.com.au/search?keyword={encoded_term}"
    try:
        response = requests.get(shopback_url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        selector = ".pos_relative.p_12px_8px.smDown\\:p_8px_4px.rounded_16.border_solid_1px_\\{colors\\.sbds-global-color-gray-5\\}.cursor_pointer.hover\\:shadow_0_1px_8px_\\{colors\\.sbds-global-color-gray-10\\}"
        element = soup.select_one(selector)
        if element and element.text:
            text = element.text.strip()
            match = re.search(r'(Up to )?(\$?\d+\.?\d*%\s*Cashback|\$\d+\.?\d*\s*Cashback)', text, re.IGNORECASE)
            cashback = match.group(0) if match else "No Cashback Available"
        else:
            cashback = "No Cashback Available"
        results.append({"Site": "ShopBack", "Cashback": cashback, "URL": shopback_url})
    except Exception as e:
        results.append({"Site": "ShopBack", "Cashback": f"Error: {str(e)}", "URL": shopback_url})

    # TopCashback
    topcashback_url = f"https://www.topcashback.com.au/search/merchants/?s={encoded_topcashback_term}"
    try:
        response = requests.get(topcashback_url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        selector = "#ctl00_GeckoTwoColPrimary_ctl04_price"
        element = soup.select_one(selector)
        cashback = element.text.strip() if element else "No Cashback Available"
        results.append({"Site": "TopCashback", "Cashback": cashback, "URL": topcashback_url})
    except Exception as e:
        results.append({"Site": "TopCashback", "Cashback": f"Error: {str(e)}", "URL": topcashback_url})

    # Cashrewards
    cashrewards_url = f"https://www.cashrewards.com.au/search/?keyword={encoded_term}"
    try:
        response = requests.get(cashrewards_url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        selector = "div[class*='grid grid-cols-2 divide-x divide-neutral-100 w-full'] p[class='p font-extrabold text-purple-500 break-words font-primary']"
        element = soup.select_one(selector)
        cashback = element.text.strip() if element else "No Cashback Available"
        results.append({"Site": "Cashrewards", "Cashback": cashback, "URL": cashrewards_url})
    except Exception as e:
        results.append({"Site": "Cashrewards", "Cashback": f"Error: {str(e)}", "URL": cashrewards_url})

    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('q', '').lower()
    suggestions = [m for m in MERCHANTS if query in m.lower()]
    return jsonify(suggestions[:10])  # Return top 10 matches

@app.route('/search', methods=['POST'])
def search():
    merchant = request.form.get('merchant')
    if merchant in MERCHANTS:
        results = get_cashback_percentage(merchant)
        return jsonify(results)
    return jsonify({"error": "Merchant not found"}), 400

# Only run locally for testing
if __name__ == "__main__":
    app.run(debug=True)
