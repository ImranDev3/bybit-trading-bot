# 🚀 Bybit Trading Bot

A professional-grade automated cryptocurrency trading bot for Bybit exchange. Designed for both spot and futures trading with multiple strategies, real-time monitoring, and risk management.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows/Linux/Mac-orange)

---

## 📋 Description

This trading bot is a comprehensive solution for automated cryptocurrency trading on Bybit. It combines technical analysis, risk management, and automated execution to help traders execute strategies consistently without emotional interference.

**Key Highlights:**
- Multiple trading strategies (Grid, DCA, Scalping, Trend Following)
- Real-time market data analysis
- Automated position management with Stop Loss & Take Profit
- Backtesting capabilities
- Telegram/Discord alerts for trade notifications

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 **Automated Trading** | Fully automated trade execution based on configured strategies |
| 📊 **Multiple Timeframes** | Support for 1m, 5m, 15m, 1H, 4H, 1D charts |
| 📈 **Multiple Strategies** | Grid, DCA, Scalping, Trend Following, RSI/EMA strategies |
| 🛡️ **Risk Management** | Stop Loss, Take Profit, position size management |
| 📉 **Backtesting** | Test strategies on historical data before live trading |
| 🔔 **Real-time Alerts** | Get notified via Telegram/Discord for all trade activities |
| 💰 **Futures Trading** | USDT Perpetual futures support |
| 🎯 **Spot Trading** | Spot market trading capability |

---

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Bybit account with API keys

### 1. Clone the Repository
```bash
git clone https://github.com/ImranDev3/bybit-trading-bot.git
cd bybit-trading-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests pandas numpy ta scikit-learn
```

---

## ⚙️ Configuration

### 1. Create Bybit API Keys
1. Go to [Bybit](https://www.bybit.com)
2. Navigate to: Account → API Management → Create New Key
3. Select permissions: **Trade** + **Read**
4. IP Whitelist: Leave empty or add your IP address
5. Copy your **API Key** and **API Secret**

### 2. Configure the Bot
Edit the configuration in the bot files:
```python
# Example configuration
API_KEY = "your_api_key_here"
API_SECRET = "your_api_secret_here"

# Trading settings
SYMBOL = "BTCUSDT"
TIMEFRAME = "15"
LEVERAGE = 10
STOP_LOSS_PERCENT = 2
TAKE_PROFIT_PERCENT = 4
```

---

## 🚀 Usage

### Start Trading
```bash
# Run the main trading bot
python rgb_bot.py

# Or run web-based version
python web_bot.py

# Check positions
python check_pos.py
```

### Demo Mode
Always test your strategies in demo mode first:
```python
IS_DEMO = True  # Enable demo trading
```

---

## 📁 Project Structure

```
bybit-trading-bot/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── rgb_bot.py          # Main trading bot (RGB strategy)
├── web_bot.py          # Web interface version
├── check_pos.py        # Position checker utility
└── config.py           # Configuration file (optional)
```

---

## 📊 Trading Strategies

### 1. Grid Trading
Places buy/sell orders at predetermined price levels to profit from market volatility.

### 2. DCA (Dollar Cost Averaging)
Buys at regular intervals to average down/up the entry price.

### 3. Scalping
Quick trades targeting small price movements with high frequency.

### 4. Trend Following
Uses EMA/Moving Average crossovers to identify market trends.

### 5. RSI/EMA Strategy
Combines RSI overbought/oversold signals with EMA for entries.

---

## ⚠️ Risk Warning

**Trading cryptocurrency carries significant risk. Please note:**

- ⚠️ Always use demo mode first to test strategies
- ⚠️ Only trade with money you can afford to lose
- ⚠️ Set proper Stop Loss to limit losses
- ⚠️ The bot may not guarantee profits
- ⚠️ Market conditions can change rapidly

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 License

This project is licensed under the MIT License.

---

## 🔗 Links

- [Bybit Official](https://www.bybit.com)
- [Bybit API Documentation](https://bybit-exchange.github.io/docs/intro)
- [GitHub Repository](https://github.com/ImranDev3/bybit-trading-bot)

---

**Happy Trading! 🚀**