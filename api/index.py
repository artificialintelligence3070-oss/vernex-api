from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

GLOBAL_BRANDING = {
    "name": "VERNEX",
    "channel": "https://t.me/shayan_explorer_channel"
}

def check_access_token(user_key, requested_endpoint, client_db):
    if not user_key:
        return False, jsonify({"status": "error", "message": "Missing authorization key. Append ?key=YOUR_KEY to the URL."}), 400
        
    if not client_db or "keys" not in client_db:
        return False, jsonify({"status": "error", "message": "Ecosystem database sync mismatch. Please check your dashboard setup."}), 500
        
    if user_key not in client_db["keys"]:
        return False, jsonify({"status": "error", "message": "Invalid VERNEX API key. This key does not exist in the database."}), 403
        
    profile = client_db["keys"][user_key]
    
    # 1. STRICT PAUSE / RESUME CHECK (Directly checks the state sent by client)
    if str(profile.get("status")).strip().lower() != "on":
        return False, jsonify({"status": "error", "message": "Access Denied: This VERNEX API key is currently PAUSED by the operator."}), 403
        
    # 2. ALLOWED ENDPOINTS CHECK
    allowed_list = profile.get("allowed_apis", [])
    if requested_endpoint not in allowed_list:
        return False, jsonify({
            "status": "error", 
            "message": f"Access Denied: This key does not have permission to use the '{requested_endpoint}' API."
        }), 403
        
    # 3. REAL-TIME EXPIRATION MATRIX CHECK
    try:
        expiry_date = datetime.strptime(profile.get("expiry"), "%Y-%m-%d").date()
        if datetime.now().date() > expiry_date:
            return False, jsonify({"status": "error", "message": "Access Denied: This token allocation has expired."}), 403
    except Exception:
        return False, jsonify({"status": "error", "message": "Internal date compliance validation error."}), 500

    # 4. QUOTA CAPACITY CHECK
    if int(profile.get("used", 0)) >= int(profile.get("limit", 0)):
        return False, jsonify({"status": "error", "message": "Daily request quota volume exhausted for this key."}), 429
        
    return True, profile

def forward_and_brand_request(endpoint_path, query_params, profile, log_identifier):
    # Upstream authentication key
    query_params['key'] = "vernex-6a9dc4fdd5923c40b0aba27bf1e39e3f"
    target_url = f"https://ft-osint-api.duckdns.org/api/{endpoint_path}"
    
    try:
        response = requests.get(target_url, params=query_params, timeout=12)
        raw_text = response.text
        
        # Intercepting upstream infrastructure limit messages
        if "Too many requests" in raw_text or "same number" in raw_text:
            return jsonify({
                "status": "error",
                "message": "Rate Limit Triggered: Too many requests for this specific number. Please wait 5-10 minutes before retrying."
            }), 429
        
        # Clean rebranding filtering rules
        for term in ["@ftgamer2", "@bornex", "ftgamer2", "bornex"]:
            if term in raw_text:
                raw_text = raw_text.replace(term, GLOBAL_BRANDING["name"].lower())
        if "Ultra" in raw_text:
            raw_text = raw_text.replace("Ultra", GLOBAL_BRANDING["name"])
            
        if "t.me/" in raw_text or "youtube.com/" in raw_text:
            raw_text = raw_text.replace("https://t.me/lynx_api. ", GLOBAL_BRANDING["channel"])
            raw_text = raw_text.replace("https://youtube.com/@ftgamer2", GLOBAL_BRANDING["channel"])
            raw_text = raw_text.replace("https://t.me/bornex", GLOBAL_BRANDING["channel"])
            
        upstream_payload = json.loads(raw_text)
        return {"status": "success", "payload": upstream_payload}
        
    except Exception as e:
        return {"status": "error", "message": f"Data stream forwarding fault: {str(e)}"}

@app.route('/api/<path:endpoint>', methods=['GET', 'POST'])
def universal_router(endpoint):
    # Fallback to handle direct options/db calls safely
    if endpoint == "db":
        return jsonify({"status": "success", "info": "State synced directly via dynamic middleware pipelines."})

    user_key = request.args.get('key')
    
    # Extraction parameters map
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
        return jsonify({"status": "error", "message": "Missing required service parameter (e.g., ?num=, ?uid=, etc.)."}), 400

    # Read state payload sent dynamically from frontend headers/parameters if available, else blank structure
    client_db = {"keys": {}, "history": []}
    client_state_raw = request.headers.get('X-Ecosystem-State')
    
    if client_state_raw:
        try:
            client_db = json.loads(client_state_raw)
        except Exception:
            pass

    # Authorize usage rules
    is_authorized, context = check_access_token(user_key, endpoint, client_db)
    if not is_authorized: 
        return context
        
    forward_params = {active_param: active_value}
    execution_result = forward_and_brand_request(endpoint, forward_params, context, active_value)
    
    if isinstance(execution_result, tuple) or hasattr(execution_result, 'json'):
        return execution_result

    if execution_result.get("status") == "error":
        return jsonify({"status": "error", "message": execution_result.get("message")}), 502

    # Prepare response alongside new state tracking values to update client
    updated_used = int(context.get("used", 0)) + 1
    new_log = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "key_name": context.get("name"),
        "queried_num": f"[{endpoint.upper()}] -> {active_value}",
        "status": "Success"
    }

    return jsonify({
        "status": "success",
        "provider": GLOBAL_BRANDING["name"],
        "channel": GLOBAL_BRANDING["channel"],
        "user": context.get("name"),
        "remaining_calls": int(context["limit"]) - updated_used,
        "sync_update": {
            "target_key": user_key,
            "new_used_value": updated_used,
            "log_entry": new_log
        },
        "result": execution_result.get("payload")
    })

def handler(environ, start_response):
    return app(environ, start_response)
