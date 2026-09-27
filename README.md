# 🛢️ Automated Oil Stock Trading Bot (Revolut Hungary Edition)

A 24/7 algorithmic trading bot and cloud scanner engineered for **Hungarian Revolut users** trading major energy equities:
**`XOM` (ExxonMobil), `CVX` (Chevron), `OXY` (Occidental), `COP` (ConocoPhillips), `BP` (BP), and `SHEL` (Shell)**, anchored by physical **WTI Crude Futures (`CL=F`)**.

---

## 📱 Live Phone Push Alerts (`ntfy.sh`)

Trade signals are dispatched in real-time with exact **Action, Execution Price, Stop Loss, and Take Profit targets**:

```text
🟢 OIL BOT: BUY XOM @ $160.59
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION: BUY XOM (ExxonMobil)
💵 Execution Price: $160.59
🛑 Stop Loss: $150.56
🎯 Take Profit Target: $176.64
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 AI Reasoning [Gemini LLM]:
"Saudi energy ministry confirmed strict quota compliance alongside 
an unexpected 3.2M barrel US crude inventory draw, tightening short-term 
physical balances despite European economic softness."
📈 Technical: Fast EMA(12) > Slow EMA(26), RSI 48.9, Macro Crude: +0.42
📱 Revolut: Ready to execute on your phone.
```

* **Active Phone Channel**: **`buzi-bot`**
* **Live Web View**: [https://ntfy.sh/buzi-bot](https://ntfy.sh/buzi-bot)

---

## 🧠 Dual AI News & Catalyst Intelligence

Unlike simple keyword scripts, the bot uses a **two-tier intelligence engine**:

1. **Google Gemini LLM (Primary Context Engine)**:
   - Evaluates physical OPEC+ supply quotas and compliance.
   - Detects US EIA inventory surprise builds vs draws.
   - Assesses geopolitical transit chokepoints (Strait of Hormuz, Red Sea) and sanctions.
   - Explains its rationale in a crisp 1–2 sentence executive summary delivered directly to your lock screen.
2. **Energy Domain Lexicon (Automatic 100% Uptime Fallback)**:
   - If the API key is not configured or encounters rate limits, the bot automatically falls back to a physical commodity supply/demand lexicon.
   - Every alert explicitly states whether it was analyzed by **`[Gemini LLM]`** or **`[Fallback Lexicon]`**.

---

## 📊 6-Year Backtest on Revolut Hungary Stocks (2020–2026)

Tested over the exact 6-year period (September 26, 2020 – September 26, 2026) across `XOM`, `CVX`, `OXY`, `COP`, `BP`, and `SHEL`:

- **Starting Capital**: \$100,000.00 $\rightarrow$ **Ending Equity**: **\$163,657.89** (**+63.66% return**)
- **CAGR**: **8.60%**
- **Profit Factor**: **1.37**
- **Average Win vs. Average Loss**: **+\$3,441.73 vs. -\$1,538.24** (**2.24x payoff ratio**)
- **Max Drawdown**: **-26.91%** (strictly controlled via $2.5 \times \text{ATR}$ dynamic trailing stops)

---

## ☁️ 24/7 Cloud Scanner (Runs with MacBook Closed)

The bot runs on GitHub Actions in the cloud via [`.github/workflows/scanner.yml`](.github/workflows/scanner.yml):
- **US Market Hours**: Runs automatically **every 30 minutes** (Monday–Friday 13:00 to 22:00 UTC / 15:00 to 00:00 CET).
- **Off-Market & Weekends**: Runs **every 2 hours** to scan for weekend OPEC announcements, pipeline outages, and geopolitical flares.
- **MacBook Independent**: **Runs 24/7 in GitHub's cloud data centers even when your laptop is closed, asleep, or turned off.**

---

## 🔑 Activating Google Gemini LLM in GitHub Actions

To enable deep Gemini AI context reasoning in your 24/7 cloud runner:

1. Get a free API key at **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. In this GitHub repo, go to **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
3. Click **New repository secret**:
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: *paste your Gemini API key*
4. Click **Add secret**.

The cloud scanner will automatically use Gemini LLM context reasoning on every run!

---

## 📄 Complete PDF Setup & Operational Guide

Download the full 2-page manual:
👉 [**Oil_Trading_Bot_User_Guide.pdf**](Oil_Trading_Bot_User_Guide.pdf)

Includes the complete Revolut execution playbook (Buy orders, Stop-Loss entry, Exit alerts, and notification privacy).

---

## 🛠️ Local CLI Usage

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Test phone push notification (sends to buzi-bot)
python main.py test-alert --ntfy buzi-bot

# 3. Test Gemini LLM integration directly
python main.py test-gemini --ntfy buzi-bot --key "YOUR_GEMINI_API_KEY"

# 4. Run full multi-factor scan (technicals + AI news)
python main.py scan

# 5. Run 6-year historical backtest
python main.py backtest --start 2020-09-26
```
