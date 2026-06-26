from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
DB_FILE = os.path.join('/tmp', 'vernex_vault.json')

# GLOBAL BRANDING CONFIGURATION
MY_NAME = "VERNEX"
MY_CHANNEL_URL = "https://t.me/shayan_explorer_channel"  # Reverted to your main channel

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "keys": {
                "vernex-admin-key": {
                    "name": "Vernex Root Operator",
                    "expiry": "2030-12-31",
                    "limit": 100000,
                    "used": 0,
                    "status": "on",
                    "allowed_apis": ["number", "adv", "numleak", "paytm", "aadhar", "adharfamily", "imei", "upi", "ifsc", "pincode", "vehicle", "challan", "bgmi", "pan", "git", "email", "insta", "snap", "tgidinfo"]
                }
            },
            "history": []
        }
        with open(DB_FILE, 'w') as f:
            json.dump(default_data, f)
        return default_data
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {
                "keys": {
                    "vernex-admin-key": {
                        "name": "Vernex Root Operator",
                        "expiry": "2030-12-31",
                        "limit": 100000,
                        "used": 0,
                        "status": "on",
                        "allowed_apis": ["number", "adv", "numleak", "paytm", "aadhar", "adharfamily", "imei", "upi", "ifsc", "pincode", "vehicle", "challan", "bgmi", "pan", "git", "email", "insta", "snap", "tgidinfo"]
                    }
                },
                "history": []
            }

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def check_access_token(user_key, requested_endpoint):
    if not user_key:
        return False, jsonify({"status": "error", "message": "Missing authorization key"}), 400
        
    db = load_db()
    if user_key not in db["keys"]:
        return False, jsonify({"status": "error", "message": "Invalid VERNEX API key"}), 403
        
    profile = db["keys"][user_key]
    if profile.get("status", "on") != "on":
        return False, jsonify({"status": "error", "message": "This authorization key is paused"}), 403
        
    allowed_list = profile.get("allowed_apis", [])
    if requested_endpoint not in allowed_list:
        return False, jsonify({
            "status": "error", 
            "message": f"Access Denied: This key does not have permission to use the '{requested_endpoint}' API."
        }), 403
        
    try:
        expiry_date = datetime.strptime(profile.get("expiry"), "%Y-%m-%d").date()
        if datetime.now().date() > expiry_date:
            return False, jsonify({"status": "error", "message": "This key allocation has expired"}), 403
    except:
        return False, jsonify({"status": "error", "message": "Internal date compliance error"}), 500

    if int(profile.get("used", 0)) >= int(profile.get("limit", 0)):
        return False, jsonify({"status": "error", "message": "Daily request quota volume exhausted"}), 429
        
    return True, profile, db

def forward_and_brand_request(endpoint_path, query_params, profile, db, log_identifier):
    query_params['key'] = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"
    target_url = f"https://ft-osint-api.duckdns.org/api/{endpoint_path}"
    
    try:
        response = requests.get(target_url, params=query_params, timeout=12)
        raw_text = response.text
        
        for term in ["@ftgamer2", "@bornex", "ftgamer2", "bornex"]:
            if term in raw_text:
                raw_text = raw_text.replace(term, MY_NAME.lower())
        if "Ultra" in raw_text:
            raw_text = raw_text.replace("Ultra", MY_NAME)
            
        if "t.me/" in raw_text or "youtube.com/" in raw_text:
            raw_text = raw_text.replace("https://t.me/lynx_api", MY_CHANNEL_URL)
            raw_text = raw_text.replace("https://youtube.com/@ftgamer2", MY_CHANNEL_URL)
            raw_text = raw_text.replace("https://t.me/bornex", MY_CHANNEL_URL)
            
        upstream_payload = json.loads(raw_text)
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Data stream clean fault: {str(e)}"}), 502

    profile["used"] = int(profile.get("used", 0)) + 1
    
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "key_name": profile.get("name"),
        "queried_num": f"[{endpoint_path.upper()}] -> {log_identifier}",
        "status": "Success"
    }
    db["history"].insert(0, log_entry)
    db["history"] = db["history"][:20] 
    save_db(db)

    return jsonify({
        "status": "success",
        "provider": MY_NAME,
        "channel": MY_CHANNEL_URL,
        "user": profile.get("name"),
        "remaining_calls": int(profile["limit"]) - int(profile["used"]),
        "result": upstream_payload
    })

@app.route('/api/db', methods=['GET', 'POST'])
def handle_database_sync():
    db = load_db()
    if request.method == 'POST':
        req_data = request.get_json()
        if "keys" in req_data: db["keys"] = req_data["keys"]
        if "history" in req_data: db["history"] = req_data["history"]
        save_db(db)
        return jsonify({"status": "success", "db": db})
    return jsonify(db)

@app.route('/api/<path:endpoint>', methods=['GET'])
def universal_router(endpoint):
    user_key = request.args.get('key')
    
    param_keys = ['num', 'imei', 'upi', 'ifsc', 'pin', 'vehicle', 'challan', 'uid', 'username', 'email', 'info', 'pan', 'id', 'ip']
    active_param = None
    active_value = None
    
    for p_key in param_keys:
        val = request.args.get(p_key)
        if val:
            active_param = p_key
            active_value = val
            break
            
    if not active_param or not active_value:
        return jsonify({"status": "error", "message": "Missing required service parameter"}), 400
        
    is_authorized, *context = check_access_token(user_key, endpoint)
    if not is_authorized: 
        return context[0]
        
    forward_params = {active_param: active_value}
    return forward_and_brand_request(endpoint, forward_params, context[0], context[1], active_value)

def handler(environ, start_response):
    return app(environ, start_response)
