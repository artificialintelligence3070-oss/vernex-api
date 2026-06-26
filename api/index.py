from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
DB_FILE = os.path.join('/tmp', 'vernex_simple_vault.json')

# BRANDING CONFIGURATION - Your Personalized Channel Details
MY_NAME = "VERNEX"
MY_CHANNEL_URL = "https://t.me/shayan_explorer_channel"

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "keys": {
                "vernex-key-1": {
                    "name": "Default Test User",
                    "expiry": "2026-12-31",
                    "limit": 1000,
                    "used": 0,
                    "status": "on"
                }
            },
            "history": []
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/api/db', methods=['GET', 'POST'])
def manage_db():
    db = load_db()
    if request.method == 'POST':
        req_data = request.get_json()
        if "keys" in req_data: db["keys"] = req_data["keys"]
        if "history" in req_data: db["history"] = req_data["history"]
        save_db(db)
        return jsonify({"status": "success", "db": db})
    return jsonify(db)

@app.route('/api/number', methods=['GET'])
def resolve_number():
    user_key = request.args.get('key')
    phone_num = request.args.get('num')
    
    if not user_key or not phone_num:
        return jsonify({"status": "error", "message": "Missing key or num parameters"}), 400
        
    db = load_db()
    
    # 1. Key Check
    if user_key not in db["keys"]:
        return jsonify({"status": "error", "message": "Invalid API key"}), 403
        
    key_profile = db["keys"][user_key]
    
    # 2. Status Check
    if key_profile.get("status", "on") != "on":
        return jsonify({"status": "error", "message": "This key is paused"}), 403
        
    # 3. Expiration Check
    try:
        expiry_date = datetime.strptime(key_profile.get("expiry"), "%Y-%m-%d").date()
        if datetime.now().date() > expiry_date:
            return jsonify({"status": "error", "message": "This key has expired"}), 403
    except:
        return jsonify({"status": "error", "message": "Date tracking error"}), 500

    # 4. Limit Check
    if int(key_profile.get("used", 0)) >= int(key_profile.get("limit", 0)):
        return jsonify({"status": "error", "message": "Daily usage limit reached"}), 429

    # 5. Upstream Request Fetching & Branding Replacement
    target_url = f"https://ft-osint-api.duckdns.org/api/number?key=vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f&num={phone_num}"
    try:
        response = requests.get(target_url, timeout=10)
        raw_text = response.text
        
        # Automatically clean out old username markers from the upstream content text
        if "@ftgamer2" in raw_text:
            raw_text = raw_text.replace("@ftgamer2", f"@{MY_NAME.lower()}")
            
        # Overwrite all old reference channel links with your Telegram group link
        if "t.me/" in raw_text or "youtube.com/" in raw_text:
            raw_text = raw_text.replace("https://t.me/ftgamer2", MY_CHANNEL_URL)
            raw_text = raw_text.replace("https://youtube.com/@ftgamer2", MY_CHANNEL_URL)
            
        upstream_payload = json.loads(raw_text)
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Could not process or re-brand payload data: {str(e)}"}), 502

    # 6. Auto-Increment Usage Counter Tracking & Log Ingestion
    key_profile["used"] = int(key_profile.get("used", 0)) + 1
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "key_name": key_profile.get("name"),
        "queried_num": phone_num,
        "status": "Success"
    }
    db["history"].insert(0, log_entry)
    db["history"] = db["history"][:20] 
    save_db(db)

    return jsonify({
        "status": "success",
        "provider": MY_NAME,
        "channel": MY_CHANNEL_URL,
        "user": key_profile.get("name"),
        "remaining_calls": int(key_profile["limit"]) - int(key_profile["used"]),
        "result": upstream_payload
    })

def handler(environ, start_response):
    return app(environ, start_response)
