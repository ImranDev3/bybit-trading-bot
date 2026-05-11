import tkinter as tk
from tkinter import ttk
import threading
import time
import requests
import pandas as pd
import hmac
import hashlib
from datetime import datetime
import os
import sys

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
                equity = float(data["result"]["list"][0]["totalEquity"])
                return equity
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
    df["macd_hist"] = df["macd"] - df["macd_signal"]
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
        return "BUY", buy_score, last["rsi"], last["macd"]
    elif sell_score >= 50:
        return "SELL", sell_score, last["rsi"], last["macd"]
    return "HOLD", 0, last["rsi"], last["macd"]

class MatrixBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BYBIT TRADING TERMINAL")
        self.root.geometry("1300x900")
        self.root.configure(bg="#0d1117")
        
        self.api = BybitAPI(CONFIG["api_key"], CONFIG["api_secret"])
        self.running = True  # Always running!
        self.start_balance = 0
        self.auto_trading = True
        self.selected_symbol = "BTCUSDT"
        
        self.setup_ui()
        self.refresh_all_data()
        
        # Start auto loop after 2 seconds
        self.root.after(2000, self.start_auto_trading)

    def setup_ui(self):
        main = tk.Frame(self.root, bg="#0d1117")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # HEADER
        header = tk.Frame(main, bg="#161b22", height=60)
        header.pack(fill="x", pady=(0,10))
        header.pack_propagate(False)

        tk.Label(header, text="BYBIT TRADING TERMINAL", font=("Arial", 18, "bold"),
                bg="#161b22", fg="#58a6ff").pack(side="left", padx=15)

        self.lbl_balance = tk.Label(header, text="BALANCE: $0.00", font=("Arial", 14, "bold"),
                bg="#161b22", fg="#3fb950", width=20)
        self.lbl_balance.pack(side="left", padx=10)

        self.lbl_pnl = tk.Label(header, text="PnL: $0.00", font=("Arial", 12),
                bg="#161b22", fg="#ffffff", width=15)
        self.lbl_pnl.pack(side="left", padx=10)

        # Keep running - no close button
        tk.Label(header, text="AUTO-ON", font=("Arial", 10, "bold"),
                bg="#161b22", fg="#3fb950").pack(side="right", padx=15)

        self.lbl_status = tk.Label(header, text="LIVE", font=("Arial", 10, "bold"),
                bg="#161b22", fg="#3fb950")
        self.lbl_status.pack(side="right", padx=10)

        # TRADING PANEL
        trade_frame = tk.Frame(main, bg="#21262d", bd=1, relief="solid")
        trade_frame.pack(fill="x", pady=(0,10))

        tk.Label(trade_frame, text="MANUAL TRADE", font=("Arial", 11, "bold"),
                bg="#21262d", fg="#f0883e").pack(side="left", padx=10)

        tk.Label(trade_frame, text="Symbol:", bg="#21262d", fg="white").pack(side="left", padx=5)
        self.sym_var = tk.StringVar(value="BTCUSDT")
        tk.OptionMenu(trade_frame, self.sym_var, *SYMBOLS).config(bg="#30363d", fg="#3fb950").pack(side="left", padx=5)

        tk.Label(trade_frame, text="Qty:", bg="#21262d", fg="white").pack(side="left", padx=5)
        self.qty_entry = tk.Entry(trade_frame, bg="#30363d", fg="#3fb950", width=8)
        self.qty_entry.insert(0, "0.01")
        self.qty_entry.pack(side="left", padx=5)

        # SL/TP Settings
        tk.Label(trade_frame, text="SL%:", bg="#21262d", fg="white").pack(side="left", padx=10)
        self.sl_entry = tk.Entry(trade_frame, bg="#30363d", fg="#f85149", width=5)
        self.sl_entry.insert(0, "1.5")
        self.sl_entry.pack(side="left", padx=2)

        tk.Label(trade_frame, text="TP%:", bg="#21262d", fg="white").pack(side="left", padx=5)
        self.tp_entry = tk.Entry(trade_frame, bg="#30363d", fg="#3fb950", width=5)
        self.tp_entry.insert(0, "3.0")
        self.tp_entry.pack(side="left", padx=2)

        tk.Button(trade_frame, text="BUY", bg="#3fb950", fg="black", font=("Arial", 10, "bold"),
                command=self.manual_buy).pack(side="left", padx=10)
        tk.Button(trade_frame, text="SELL", bg="#f85149", fg="white", font=("Arial", 10, "bold"),
                command=self.manual_sell).pack(side="left", padx=5)
        tk.Button(trade_frame, text="CLOSE", bg="#f0883e", fg="black", font=("Arial", 10, "bold"),
                command=self.close_pos).pack(side="left", padx=10)

        # MAIN CONTENT
        content = tk.Frame(main, bg="#0d1117")
        content.pack(fill="both", expand=True)

        # LEFT - PAIRS
        left = tk.LabelFrame(content, text="MARKET PAIRS", font=("Arial", 11, "bold"),
                            bg="#0d1117", fg="#58a6ff", bd=2)
        left.pack(side="left", fill="both", expand=True, padx=(0,5))

        self.pair_frames = {}
        for i, sym in enumerate(SYMBOLS):
            row, col = i // 2, i % 2
            f = tk.Frame(left, bg="#21262d", bd=1, relief="solid")
            f.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            f.pack_propagate(False)
            f.configure(height=90)

            tk.Label(f, text=sym, font=("Arial", 11, "bold"), bg="#21262d", fg="#58a6ff").pack(pady=2)
            lbl_price = tk.Label(f, text="$0.00", font=("Arial", 14, "bold"), bg="#21262d", fg="white")
            lbl_price.pack()
            lbl_sig = tk.Label(f, text="...", font=("Arial", 9), bg="#21262d", fg="#8b949e")
            lbl_sig.pack()
            self.pair_frames[sym] = {"price": lbl_price, "signal": lbl_sig}

        left.columnconfigure(0, weight=1)
        left.columnconfigure(1, weight=1)

        # RIGHT - POSITIONS
        right = tk.LabelFrame(content, text="POSITIONS & HISTORY", font=("Arial", 11, "bold"),
                            bg="#0d1117", fg="#58a6ff", bd=2)
        right.pack(side="right", fill="both", expand=True, padx=(5,0))

        self.pos_text = tk.Text(right, bg="#161b22", fg="#3fb950", font=("Arial", 9), height=25)
        self.pos_text.pack(fill="both", expand=True, padx=5, pady=5)

        # LOG
        log_frame = tk.LabelFrame(main, text="ACTIVITY LOG", font=("Arial", 10),
                                bg="#0d1117", fg="#8b949e", bd=1)
        log_frame.pack(fill="x", pady=10)

        self.log_text = tk.Text(log_frame, bg="#161b22", fg="#3fb950", font=("Arial", 9), height=5)
        self.log_text.pack(fill="x", padx=5, pady=5)

        # INFO
        info = tk.Frame(main, bg="#21262d")
        info.pack(fill="x", pady=5)
        tk.Label(info, text="Auto Trading: ON | SL/TP: Enabled", bg="#21262d", fg="#3fb950").pack()

    def log(self, msg):
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)

    def refresh_all_data(self):
        threading.Thread(target=self._refresh_data, daemon=True).start()

    def _refresh_data(self):
        try:
            bal = self.api.get_balance()
            if bal > 0:
                if self.start_balance == 0:
                    self.start_balance = bal
                self.lbl_balance.config(text=f"BALANCE: ${bal:.2f}")
                
                pnl = bal - self.start_balance
                color = "#3fb950" if pnl >= 0 else "#f85149"
                sign = "+" if pnl >= 0 else ""
                self.lbl_pnl.config(text=f"PnL: {sign}${pnl:.2f}", fg=color)

            positions = self.api.get_all_positions()
            closed = self.api.get_closed_pnl()

            self.pos_text.delete(1.0, tk.END)
            self.pos_text.insert(tk.END, "="*50 + "\n")
            self.pos_text.insert(tk.END, "OPEN POSITIONS\n", "bold")
            self.pos_text.insert(tk.END, "="*50 + "\n")

            open_count = 0
            if positions:
                for p in positions:
                    if float(p.get("size", 0)) > 0:
                        open_count += 1
                        sym = p["symbol"]
                        side = p["side"]
                        size = p["size"]
                        entry = float(p["entryPrice"])
                        upnl = float(p["unrealizedPnl"])
                        
                        # Check SL/TP
                        current_price = entry
                        try:
                            df = self.api.get_kline(sym, "1", 1)
                            if df is not None:
                                current_price = df["close"].iloc[-1]
                        except:
                            pass
                        
                        sl_pct = float(self.sl_entry.get())
                        tp_pct = float(self.tp_entry.get())
                        
                        if side == "Buy":
                            sl_price = entry * (1 - sl_pct/100)
                            tp_price = entry * (1 + tp_pct/100)
                        else:
                            sl_price = entry * (1 + sl_pct/100)
                            tp_price = entry * (1 - tp_pct/100)
                        
                        # Auto close if SL/TP hit
                        close_reason = ""
                        if side == "Buy" and current_price <= sl_price:
                            self.api.close_position(sym)
                            close_reason = " [SL HIT]"
                        elif side == "Buy" and current_price >= tp_price:
                            self.api.close_position(sym)
                            close_reason = " [TP HIT]"
                        elif side == "Sell" and current_price >= sl_price:
                            self.api.close_position(sym)
                            close_reason = " [SL HIT]"
                        elif side == "Sell" and current_price <= tp_price:
                            self.api.close_position(sym)
                            close_reason = " [TP HIT]"
                        
                        uc = "#3fb950" if upnl >= 0 else "#f85149"
                        self.pos_text.insert(tk.END, f"{sym} | {side} | {size}\n")
                        self.pos_text.insert(tk.END, f"Entry: ${entry:.2f} | Now: ${current_price:.2f}\n", "normal")
                        self.pos_text.insert(tk.END, f"PnL: ${upnl:.2f}{close_reason}\n", uc)

            if open_count == 0:
                self.pos_text.insert(tk.END, "No open positions\n")

            self.pos_text.insert(tk.END, "\n" + "="*50 + "\n")
            self.pos_text.insert(tk.END, "CLOSED TRADES (Recent)\n")
            self.pos_text.insert(tk.END, "="*50 + "\n")

            if closed:
                for t in closed[:10]:
                    sym = t["symbol"]
                    side = t["side"]
                    pnl = float(t["closedPnl"])
                    entry = t["avgEntryPrice"]
                    ex = t["avgExitPrice"]
                    c = "#3fb950" if pnl >= 0 else "#f85149"
                    self.pos_text.insert(tk.END, f"{sym} ({side})\n")
                    self.pos_text.insert(tk.END, f"Entry: ${entry} -> Exit: ${ex}\n", "normal")
                    self.pos_text.insert(tk.END, f"PnL: ${pnl:.2f}\n", c)

            self.pos_text.tag_config("bold", foreground="#f0883e")
            self.pos_text.tag_config("normal", foreground="#8b949e")

        except Exception as e:
            self.log(f"Error: {str(e)}")

    def manual_buy(self):
        sym = self.sym_var.get()
        qty = self.qty_entry.get()
        self.log(f"BUY {sym} x {qty}")
        threading.Thread(target=self._trade, args=(sym, "Buy", qty), daemon=True).start()

    def manual_sell(self):
        sym = self.sym_var.get()
        qty = self.qty_entry.get()
        self.log(f"SELL {sym} x {qty}")
        threading.Thread(target=self._trade, args=(sym, "Sell", qty), daemon=True).start()

    def _trade(self, sym, side, qty):
        try:
            self.api.set_leverage(sym, CONFIG["leverage"])
            res = self.api.place_order(sym, side, qty)
            if res and res.get("retCode") == 0:
                self.log(f"ORDER FILLED: {sym}")
                time.sleep(2)
                self.refresh_all_data()
            else:
                self.log(f"ORDER FAILED: {res.get('retMsg', 'Error')}")
        except Exception as e:
            self.log(f"Error: {str(e)}")

    def close_pos(self):
        sym = self.sym_var.get()
        self.log(f"CLOSE position: {sym}")
        threading.Thread(target=self._close, args=(sym,), daemon=True).start()

    def _close(self, sym):
        try:
            res = self.api.close_position(sym)
            if res and res.get("retCode") == 0:
                self.log(f"POSITION CLOSED: {sym}")
                time.sleep(2)
                self.refresh_all_data()
            else:
                self.log(f"CLOSE FAILED: No position or error")
        except Exception as e:
            self.log(f"Error: {str(e)}")

    def start_auto_trading(self):
        self.log("AUTO TRADING STARTED - Will run continuously!")
        threading.Thread(target=self.run_bot, daemon=True).start()

    def run_bot(self):
        while self.auto_trading:
            try:
                bal = self.api.get_balance()
                if bal > 0:
                    self.lbl_balance.config(text=f"BALANCE: ${bal:.2f}")
                    pnl = bal - self.start_balance
                    color = "#3fb950" if pnl >= 0 else "#f85149"
                    sign = "+" if pnl >= 0 else ""
                    self.lbl_pnl.config(text=f"PnL: {sign}${pnl:.2f}", fg=color)

                for sym in SYMBOLS:
                    df = self.api.get_kline(sym, CONFIG["timeframe"], 100)
                    if df is not None and not df.empty:
                        df = calculate_indicators(df)
                        sig, score, rsi, macd = get_signal(df)
                        price = df["close"].iloc[-1]
                        f = self.pair_frames[sym]
                        f["price"].config(text=f"${price:,.2f}")
                        c = "#3fb950" if sig == "BUY" else "#f85149" if sig == "SELL" else "#f0883e"
                        f["signal"].config(text=f"{sig} ({score}%)", fg=c)

                self.refresh_all_data()

            except Exception as e:
                self.log(f"Error: {str(e)}")

            time.sleep(8)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MatrixBot()
    app.run()