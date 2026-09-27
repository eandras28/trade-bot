# 🛢️⚡ Dual-Universe Trading Bot & Cloud Scanner (Revolut Hungary Edition)

A 24/7 algorithmic trading bot and cloud scanner engineered for **Hungarian Revolut users** scanning two high-conviction market universes:
1. **Energy & Macro Oil Equities**: `XOM` (ExxonMobil), `CVX` (Chevron), `OXY` (Occidental), `COP` (ConocoPhillips), `BP` (BP), and `SHEL` (Shell), anchored by physical **WTI Crude Futures (`CL=F`)**.
2. **High-Growth Deep Tech Niches**:
   - **🔋 Power & Next-Gen Battery Tech**: `VRT` (Vertiv AI cooling & power), `ENVX` (Enovix silicon-anode), `QS` (QuantumScape solid-state), `FLNC` (Fluence grid storage).
   - **🤖 Actuators & Advanced Robotics**: `SYM` (Symbotic warehouse automation & robotic actuation).
   - **🧬 Health Tech & Bio AI**: `TEM` (Tempus AI oncology diagnostics), `HIMS` (Hims & Hers telehealth), `RXRX` (Recursion AI pharma with NVIDIA), `TMDX` (TransMedics organ transplant perfusion).
   - Anchored by **Invesco Nasdaq 100 (`QQQ`)**.

---

## 📱 Live Phone Push Alerts (`ntfy.sh`)

Trade signals are dispatched in real-time with exact **Sector Badge, Action, Execution Price, Stop Loss, and Take Profit targets**:

```text
🟢 🔋 [Power/Battery] BUY VRT @ $253.28
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION: BUY VRT (Power & AI Cooling)
💵 Execution Price: $253.28
🛑 Stop Loss: $238.40
🎯 Take Profit Target: $278.60
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 AI Reasoning [Gemini LLM]:
"Vertiv secured an expanded tier-1 hyperscaler contract for high-density 
liquid cooling deployments in next-gen AI data centers, accelerating 
forward backlog while QQQ maintains a bullish technical regime."
📈 Technical: Fast EMA(12) > Slow EMA(26), RSI 54.2, Sector Macro: +0.45
📱 Revolut: Ready to trade.
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
