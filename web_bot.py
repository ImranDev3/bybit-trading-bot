from flask import Flask, render_template_string, jsonify, request
import threading
import time
import requests
import pandas as pd
import hmac
import hashlib
from datetime import datetime

CONFIG = {
    "api_key": "2WBOt9g7EevFJ9Vs8i",
    "api_secret": "HcPN5yzSiEmCkHFuU234iOAYC3KqOPilbfXI",
    "testnet": True,
    "leverage": 10,
    "timeframe": "15",
    "stop_loss_pct": 1.5,
    "take_profit_pct": 3.0,
}

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]
BASE_URL = "https://api-testnet.bybit.com" if CONFIG["testnet"] else "https://api.bybit.com"

app = Flask(__name__)

class BybitAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = BASE_URL
        self.recv_window = "5000"

    def _sign(self, timestamp, params_str):
        sign_str = f"{timestamp}{self.api_key}{self.recv_window}{params_str}"
        return hmac.new(self.api_secret.encode(), sign_str.encode(), hashlib.sha256).hexdigest()

    def get_kline(self, symbol, interval, limit=100):
        url = f"{self.base_url}/v5/market/kline"
        params = {"category": "linear", "symbol": symbol, "interval": interval, "limit": limit}
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                df = pd.DataFrame(data["result"]["list"][::-1])
                df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
                df = df.astype(float)
                df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
                return df
        except:
            pass
        return None

    def get_all_positions(self):
        url = f"{self.base_url}/v5/position/list"
        params = {"category": "linear", "settleCoin": "USDT"}
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if data.get("retCode") == 0:
                return data["result"]["list"]
        except:
            pass
        return []

    def get_closed_pnl(self, limit=20):
        url = f"{self.base_url}/v5/position/closed-pnl"
        params = {"category": "linear", "settleCoin": "USDT", "limit": limit}
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if data.get("retCode") == 0:
                return data["result"]["list"]
        except:
            pass
        return []

    def get_balance(self):
        url = f"{self.base_url}/v5/account/wallet-balance"
        params = {"accountType": "UNIFIED"}
        timestamp = str(int(time.time() * 1000))
        signature = self._sign(timestamp, "accountType=UNIFIED")
        
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type": "application/json"
        }
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            data = r.json()
            if data.get("retCode") == 0:
                return float(data["result"]["list"][0]["totalEquity"])
        except:
            pass
        return 0

    def set_leverage(self, symbol, leverage):
        url = f"{self.base_url}/v5/position/set-leverage"
        params = f"category=linear&symbol={symbol}&buyLeverage={leverage}&sellLeverage={leverage}"
        timestamp = str(int(time.time() * 1000))
        signature = self._sign(timestamp, params)
        
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type": "application/json"
        }
        try:
            r = requests.post(url, params=params, headers=headers, timeout=10)
            return r.json()
        except:
            pass
        return None

    def place_order(self, symbol, side, qty, order_type="Market"):
        url = f"{self.base_url}/v5/order/create"
        data = {"category": "linear", "symbol": symbol, "side": side, "orderType": order_type, "qty": str(qty), "timeInForce": "GTC"}
        timestamp = str(int(time.time() * 1000))
        import json
        params = json.dumps(data)
        signature = self._sign(timestamp, params)
        
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type": "application/json"
        }
        try:
            r = requests.post(url, data=params, headers=headers, timeout=10)
            return r.json()
        except:
            pass
        return None

    def close_position(self, symbol):
        url = f"{self.base_url}/v5/order/create"
        pos = self.get_all_positions()
        for p in pos:
            if p["symbol"] == symbol and float(p.get("size", 0)) > 0:
                side = "Sell" if p["side"] == "Buy" else "Buy"
                data = {"category": "linear", "symbol": symbol, "side": side, "orderType": "Market", "qty": p["size"], "timeInForce": "GTC"}
                timestamp = str(int(time.time() * 1000))
                import json
                params = json.dumps(data)
                signature = self._sign(timestamp, params)
                
                headers = {
                    "X-BAPI-API-KEY": self.api_key,
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-TIMESTAMP": timestamp,
                    "X-BAPI-RECV-WINDOW": self.recv_window,
                    "Content-Type": "application/json"
                }
                try:
                    r = requests.post(url, data=params, headers=headers, timeout=10)
                    return r.json()
                except:
                    pass
        return None

api = BybitAPI(CONFIG["api_key"], CONFIG["api_secret"])
start_balance = 0
auto_trading = True
logs = []

def calculate_indicators(df):
    close = df["close"]
    df["ema_9"] = close.ewm(span=9, adjust=False).mean()
    df["ema_21"] = close.ewm(span=21, adjust=False).mean()
    df["ema_50"] = close.ewm(span=50, adjust=False).mean()
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = exp1 - exp2
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    return df

def get_signal(df):
    df = calculate_indicators(df)
    last = df.iloc[-1]
    buy_score = 0
    sell_score = 0

    if last["ema_9"] > last["ema_21"] > last["ema_50"]:
        buy_score += 25
    elif last["ema_9"] < last["ema_21"] < last["ema_50"]:
        sell_score += 25

    if 35 < last["rsi"] < 55:
        buy_score += 15
    elif 55 < last["rsi"] < 75:
        sell_score += 15

    if last["macd"] > last["macd_signal"]:
        buy_score += 25
    else:
        sell_score += 25

    if buy_score >= 50:
        return "BUY", buy_score, round(last["rsi"], 1), round(last["macd"], 2)
    elif sell_score >= 50:
        return "SELL", sell_score, round(last["rsi"], 1), round(last["macd"], 2)
    return "HOLD", 0, round(last["rsi"], 1), round(last["macd"], 2)

def add_log(msg):
    global logs
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(logs) > 50:
        logs = logs[-50:]

def auto_trader():
    global start_balance
    while auto_trading:
        try:
            bal = api.get_balance()
            if bal > 0 and start_balance == 0:
                start_balance = bal
            
            for sym in SYMBOLS:
                df = api.get_kline(sym, CONFIG["timeframe"], 100)
                if df is not None and not df.empty:
                    sig, score, rsi, macd = get_signal(df)
                    price = df["close"].iloc[-1]
            
            positions = api.get_all_positions()
            closed = api.get_closed_pnl()
            
            add_log(f"Updated | Bal: ${bal:.2f}")
        except Exception as e:
            add_log(f"Error: {str(e)}")
        
        time.sleep(10)

# Start auto trader in background
threading.Thread(target=auto_trader, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Bybit Trading Terminal</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #c9d1d9; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        .header { background: #161b22; padding: 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .header h1 { color: #58a6ff; font-size: 24px; }
        .stats { display: flex; gap: 30px; }
        .stat { text-align: center; }
        .stat-label { font-size: 12px; color: #8b949e; }
        .stat-value { font-size: 20px; font-weight: bold; }
        .green { color: #3fb950; }
        .red { color: #f85149; }
        .live { background: #3fb950; color: #0d1117; padding: 5px 15px; border-radius: 5px; font-weight: bold; }
        
        /* Trading Panel */
        .trade-panel { background: #21262d; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .trade-panel h2 { color: #f0883e; margin-bottom: 15px; }
        .trade-controls { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
        .trade-controls select, .trade-controls input { background: #30363d; color: #c9d1d9; border: 1px solid #30363d; padding: 10px; border-radius: 5px; font-size: 14px; }
        .btn { padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px; }
        .btn-buy { background: #3fb950; color: #0d1117; }
        .btn-sell { background: #f85149; color: white; }
        .btn-close { background: #f0883e; color: #0d1117; }
        .btn:hover { opacity: 0.8; }
        
        /* Market Grid */
        .market-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
        .pair-card { background: #21262d; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
        .pair-card h3 { color: #58a6ff; margin-bottom: 10px; }
        .pair-price { font-size: 24px; font-weight: bold; color: white; }
        .pair-signal { font-size: 16px; font-weight: bold; margin-top: 5px; }
        .pair-stats { font-size: 12px; color: #8b949e; margin-top: 5px; }
        .signal-buy { color: #3fb950; }
        .signal-sell { color: #f85149; }
        .signal-hold { color: #f0883e; }
        
        /* Positions */
        .positions { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .pos-section { background: #161b22; padding: 20px; border-radius: 10px; }
        .pos-section h3 { color: #58a6ff; margin-bottom: 15px; }
        .pos-item { background: #21262d; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        .pos-item .sym { font-weight: bold; color: #58a6ff; }
        .pos-item .details { font-size: 12px; margin-top: 5px; }
        
        /* Logs */
        .logs { background: #161b22; padding: 15px; border-radius: 10px; max-height: 200px; overflow-y: auto; }
        .logs h3 { color: #8b949e; margin-bottom: 10px; }
        .log-item { font-family: monospace; font-size: 12px; color: #3fb950; margin: 3px 0; }
        
        /* Refresh */
        .refresh-btn { background: #238636; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        
        @media (max-width: 900px) {
            .market-grid { grid-template-columns: repeat(2, 1fr); }
            .positions { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BYBIT TRADING TERMINAL</h1>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">BALANCE</div>
                    <div class="stat-value green" id="balance">Loading...</div>
                </div>
                <div class="stat">
                    <div class="stat-label">PnL</div>
                    <div class="stat-value" id="pnl">$0.00</div>
                </div>
                <div class="stat">
                    <div class="stat-label">STATUS</div>
                    <div class="live">LIVE</div>
                </div>
            </div>
        </div>
        
        <div class="trade-panel">
            <h2>MANUAL TRADE</h2>
            <div class="trade-controls">
                <select id="symbol">
                    <option value="BTCUSDT">BTCUSDT</option>
                    <option value="ETHUSDT">ETHUSDT</option>
                    <option value="SOLUSDT">SOLUSDT</option>
                    <option value="XRPUSDT">XRPUSDT</option>
                    <option value="DOGEUSDT">DOGEUSDT</option>
                    <option value="ADAUSDT">ADAUSDT</option>
                </select>
                <input type="text" id="qty" value="0.01" style="width: 80px;">
                <button class="btn btn-buy" onclick="trade('Buy')">BUY</button>
                <button class="btn btn-sell" onclick="trade('Sell')">SELL</button>
                <button class="btn btn-close" onclick="close_pos()">CLOSE</button>
                <button class="refresh-btn" onclick="refresh()">REFRESH</button>
            </div>
        </div>
        
        <div class="market-grid" id="market">
            <!-- Market pairs will be loaded here -->
        </div>
        
        <div class="positions">
            <div class="pos-section">
                <h3>OPEN POSITIONS</h3>
                <div id="open-positions">Loading...</div>
            </div>
            <div class="pos-section">
                <h3>CLOSED TRADES</h3>
                <div id="closed-positions">Loading...</div>
            </div>
        </div>
        
        <div class="logs" style="margin-top: 20px;">
            <h3>ACTIVITY LOG</h3>
            <div id="log-content"></div>
        </div>
    </div>
    
    <script>
        function refresh() {
            fetch('/api/data').then(r => r.json()).then(data => {
                document.getElementById('balance').innerText = '$' + data.balance.toFixed(2);
                
                let pnl = data.balance - data.start_balance;
                let pnlEl = document.getElementById('pnl');
                pnlEl.innerText = (pnl >= 0 ? '+' : '') + '$' + pnl.toFixed(2);
                pnlEl.className = 'stat-value ' + (pnl >= 0 ? 'green' : 'red');
                
                // Market pairs
                let marketHTML = '';
                data.pairs.forEach(p => {
                    let signalClass = p.signal === 'BUY' ? 'signal-buy' : (p.signal === 'SELL' ? 'signal-sell' : 'signal-hold');
                    marketHTML += `
                        <div class="pair-card">
                            <h3>${p.symbol}</h3>
                            <div class="pair-price">$${p.price.toLocaleString()}</div>
                            <div class="pair-signal ${signalClass}">${p.signal} (${p.score}%)</div>
                            <div class="pair-stats">RSI: ${p.rsi} | MACD: ${p.macd}</div>
                        </div>
                    `;
                });
                document.getElementById('market').innerHTML = marketHTML;
                
                // Open positions
                let openHTML = '';
                data.positions.forEach(p => {
                    let pnlClass = parseFloat(p.pnl) >= 0 ? 'green' : 'red';
                    openHTML += `
                        <div class="pos-item">
                            <div class="sym">${p.symbol} (${p.side})</div>
                            <div class="details">Size: ${p.size} | Entry: $${p.entry} | PnL: <span class="${pnlClass}">$${p.pnl}</span></div>
                        </div>
                    `;
                });
                if (openHTML === '') openHTML = 'No open positions';
                document.getElementById('open-positions').innerHTML = openHTML;
                
                // Closed positions
                let closedHTML = '';
                data.closed.forEach(p => {
                    let pnlClass = parseFloat(p.pnl) >= 0 ? 'green' : 'red';
                    closedHTML += `
                        <div class="pos-item">
                            <div class="sym">${p.symbol} (${p.side})</div>
                            <div class="details">Entry: $${p.entry} -> Exit: $${p.exit} | PnL: <span class="${pnlClass}">$${p.pnl}</span></div>
                        </div>
                    `;
                });
                if (closedHTML === '') closedHTML = 'No closed trades';
                document.getElementById('closed-positions').innerHTML = closedHTML;
                
                // Logs
                let logHTML = '';
                data.logs.forEach(l => {
                    logHTML += `<div class="log-item">${l}</div>`;
                });
                document.getElementById('log-content').innerHTML = logHTML;
            });
        }
        
        function trade(side) {
            let sym = document.getElementById('symbol').value;
            let qty = document.getElementById('qty').value;
            fetch('/api/trade?symbol=' + sym + '&side=' + side + '&qty=' + qty)
                .then(r => r.json())
                .then(d => {
                    alert(d.message);
                    setTimeout(refresh, 2000);
                });
        }
        
        function close_pos() {
            let sym = document.getElementById('symbol').value;
            fetch('/api/close?symbol=' + sym)
                .then(r => r.json())
                .then(d => {
                    alert(d.message);
                    setTimeout(refresh, 2000);
                });
        }
        
        // Auto refresh every 5 seconds
        refresh();
        setInterval(refresh, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/data')
def get_data():
    try:
        bal = api.get_balance()
        global start_balance
        if bal > 0 and start_balance == 0:
            start_balance = bal
        
        pairs = []
        for sym in SYMBOLS:
            df = api.get_kline(sym, CONFIG["timeframe"], 100)
            if df is not None and not df.empty:
                sig, score, rsi, macd = get_signal(df)
                price = float(df["close"].iloc[-1])
                pairs.append({"symbol": sym, "price": price, "signal": sig, "score": score, "rsi": rsi, "macd": macd})
        
        positions = api.get_all_positions()
        open_pos = []
        for p in positions:
            if float(p.get("size", 0)) > 0:
                open_pos.append({
                    "symbol": p["symbol"],
                    "side": p["side"],
                    "size": p["size"],
                    "entry": p["entryPrice"],
                    "pnl": p["unrealizedPnl"]
                })
        
        closed = api.get_closed_pnl()
        closed_list = []
        for c in closed[:10]:
            closed_list.append({
                "symbol": c["symbol"],
                "side": c["side"],
                "entry": c["avgEntryPrice"],
                "exit": c["avgExitPrice"],
                "pnl": c["closedPnl"]
            })
        
        return jsonify({
            "balance": bal,
            "start_balance": start_balance,
            "pairs": pairs,
            "positions": open_pos,
            "closed": closed_list,
            "logs": logs
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/trade')
def trade():
    sym = request.args.get('symbol', 'BTCUSDT')
    side = request.args.get('side', 'Buy')
    qty = request.args.get('qty', '0.01')
    
    try:
        api.set_leverage(sym, CONFIG["leverage"])
        res = api.place_order(sym, side, qty)
        if res and res.get("retCode") == 0:
            add_log(f"ORDER FILLED: {side} {sym} x {qty}")
            return jsonify({"status": "success", "message": f"Order placed: {side} {sym}"})
        else:
            add_log(f"ORDER FAILED: {res.get('retMsg', 'Error')}")
            return jsonify({"status": "error", "message": res.get("retMsg", "Error")})
    except Exception as e:
        add_log(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/close')
def close():
    sym = request.args.get('symbol', 'BTCUSDT')
    try:
        res = api.close_position(sym)
        if res and res.get("retCode") == 0:
            add_log(f"POSITION CLOSED: {sym}")
            return jsonify({"status": "success", "message": f"Position closed: {sym}"})
        else:
            return jsonify({"status": "error", "message": "No position or error"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    add_log("Server started - Open http://localhost:5000 in browser")
    app.run(host='0.0.0.0', port=5000, debug=False)