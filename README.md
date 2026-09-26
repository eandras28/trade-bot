# 🛢️ 24/7 Oil Trading Bot with WhatsApp Push Notifications (Revolut Hungary Edition)

An automated algorithmic trading bot that scans live energy news, calculates macro catalysts, evaluates technical indicators, and sends **real-time WhatsApp trade notifications** to your phone with exact **Buy/Sell actions, Stop Loss, and Take Profit targets**.

Tailored specifically for **Hungarian Revolut users** tracking energy stocks accessible on the platform:
`XOM` (ExxonMobil), `CVX` (Chevron), `OXY` (Occidental Petroleum), `COP` (ConocoPhillips), `BP` (BP), and `SHEL` (Shell).

---

## 📱 What You Receive on WhatsApp

```text
🛢️ OIL BOT TRADE ALERT 🟢
━━━━━━━━━━━━━━━━━━━━━
ACTION: BUY XOM (ExxonMobil)
💵 Execution Price: $160.59
🛑 Stop Loss: $150.56
🎯 Take Profit Target: $176.64
━━━━━━━━━━━━━━━━━━━━━
📰 News Catalyst:
"OPEC+ weighs extending output cuts into next quarter" (Reuters)
📈 Technical Reason:
Fast EMA(12) > Slow EMA(26), RSI 48.9, Macro Crude Sentiment: +0.42
📱 Revolut: Ready to execute on your phone.
```

---

## 📊 6-Year Performance on Revolut Hungary Stocks (2020–2026)

- **Starting Capital**: \$100,000.00 $\rightarrow$ **Ending Equity**: **\$163,657.89** (**+63.66%**)
- **CAGR**: **8.60%**
- **Profit Factor**: **1.37**
- **Average Win vs Average Loss**: **+\$3,441.73 vs -\$1,538.24** (**2.24x payoff ratio**)
- **Max Drawdown**: **-26.91%**

---

## ⚡ 30-Second WhatsApp Setup (CallMeBot)

1. Save **`+34 644 44 24 99`** in your phone contacts as *CallMeBot*.
2. Open WhatsApp and send this message:
   ```text
   I allow callmebot to send me messages
   ```
3. CallMeBot will reply with your personal API Key:
   ```text
   APIKey: 123456
   ```
4. Test delivery immediately:
   ```bash
   python main.py test-alert --phone "+36XXXXXXXXX" --apikey "123456"
   ```

---

## 🚀 Running the Bot Continuously (24/7 Daemon)

```bash
cd /Users/andrasegressy/.gemini/antigravity/scratch/oil_trading_bot
source .venv/bin/activate

# Set your credentials
export WHATSAPP_PHONE="+36301234567"
export CALLMEBOT_API_KEY="your_api_key_here"

# Start the continuous 24/7 scanning daemon (scans every 15 mins)
python main.py live --interval 15
```
