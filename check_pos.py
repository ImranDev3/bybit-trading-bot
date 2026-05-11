import requests
import time
import hmac
import hashlib

api_key = "2WBOt9g7EevFJ9Vs8i"
api_secret = "HcPN5yzSiEmCkHFuU234iOAYC3KqOPilbfXI"
recv_window = "5000"

# Check positions
timestamp = str(int(time.time() * 1000))
query = "category=linear&settleCoin=USDT"
sign_str = f"{timestamp}{api_key}{recv_window}{query}"
signature = hmac.new(api_secret.encode(), sign_str.encode(), hashlib.sha256).hexdigest()

headers = {
    "X-BAPI-API-KEY": api_key,
    "X-BAPI-SIGN": signature,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": recv_window,
    "Content-Type": "application/json"
}

r = requests.get(f"https://api-testnet.bybit.com/v5/position/list?{query}", headers=headers, timeout=10)
data = r.json()

print(data)