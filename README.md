# Bybit Trading Bot - High Accuracy Strategy

## Setup Instructions

### 1. Install Dependencies
```bash
pip install requests pandas numpy ta scikit-learn
```

### 2. Create Bybit API Keys
1. Go to: https://www.bybit.com
2. Account → API Management → Create New Key
3. Select: Trade + Read permissions
4. IP Whitelist: Leave empty or add your IP
5. Copy: API Key, API Secret

### 3. Configure
Edit `CONFIG` in `bybit_bot.py`:
```python
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
```

### 4. Run
```bash
python bybit_bot.py
```

## Features
- ✅ Futures Trading (USDT Perpetual)
- ✅ Multiple Timeframes (1m, 5m, 15m, 1H, 4H, 1D)
- ✅ 5 Trading Strategies
- ✅ Stop Loss / Take Profit
- ✅ Position Management
- ✅ Backtesting
- ✅ Real-time Alerts