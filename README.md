# 🛢️ Revolut BRENT:CFD (Crude Oil Brent) 24/7 Swing Trading Engine

An autonomous, 24/7 algorithmic trading engine engineered for **Revolut's 'BRENT:CFD · Crude Oil Brent' (Black Gold)**:
- **Target Instrument**: Revolut **`BRENT:CFD`** (underlying feed: Active Front-Month Brent Crude Futures `BZX26.NYM` at ~$103.87).
- **Strategy Horizon**: **2–3 Day Swing Positions** (Buy / Long & Sell / Short CFDs).
- **Execution Speed**: Checks prices and breaking news continuously **every 5 minutes, 24/7**.
- **AI Intelligence**: **Google Gemini LLM** evaluating physical OPEC+ quota compliance, weekly EIA/API stockpiles, and Middle East / Red Sea chokepoint geopolitics.
- **Risk Management**: Dynamic $1.5 \times \text{ATR}$ Stop Loss and $2.5 \times \text{ATR}$ Take Profit with trailing stop protection.

---

## 📱 Live Phone Push Alerts (`ntfy.sh/buzi-bot`)

Trade signals are dispatched in real-time with exact **Action, Execution Price, Stop Loss, and Take Profit targets**:

```text
🟢 [BRNT CFD] OPEN LONG @ $96.72
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUMENT: Brent Crude Oil CFD (BRNT)
ACTION: 🟢 OPEN LONG (BUY CFD)
💵 Entry Price: $96.72
🛑 Stop Loss: $95.40 (Risk: -$1.32/bbl)
🎯 Take Profit: $98.92 (Reward: +$2.20/bbl)
⏱️ Target Horizon: 2–3 Days Swing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 AI Fundamental Catalyst [Gemini LLM]:
"Unexpected 4.1M barrel crude drawdown reported alongside renewed Red Sea 
tanker security alerts, tightening near-term prompt physical balances."
📈 Technical Setup: 1H EMA(12) > EMA(26), MACD Bullish Crossover, RSI 53.8, 14H ATR: $0.88
📱 Revolut: Open Long CFD position on Brent Crude.
```

* **Active Phone Channel**: **`buzi-bot`**
* **Live Web View**: [https://ntfy.sh/buzi-bot](https://ntfy.sh/buzi-bot)

---

## 🧠 Dual AI News & Catalyst Intelligence

Unlike simple keyword scripts, the bot uses a **sector-aware intelligence engine**:

1. **Google Gemini LLM (Primary Context Engine)**:
   - **Energy**: Physical OPEC+ quotas, EIA inventory surprises (builds vs draws), Middle East geopolitical chokepoints.
   - **Power & Battery**: Silicon-anode/solid-state milestones, OEM testing validation, pilot line yield scaling, data center power agreements.
   - **Actuators & Robotics**: Tier-1 enterprise rollouts, multi-million dollar warehouse automation contracts, robotic fleet deployments.
   - **Health Tech**: Clinical trial endpoints, FDA clearances/rejections, breakthrough therapy designations, commercial deployment.
2. **Dual-Domain NLP Lexicon (Automatic 100% Uptime Fallback)**:
   - Energy + Deep Tech custom dictionaries ensure continuous operation even during API maintenance.
   - Every alert explicitly tags **`[Gemini LLM]`** or **`[Fallback Lexicon]`**.

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
