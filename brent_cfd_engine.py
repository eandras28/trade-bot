"""Revolut Crude Oil Tracker (BRNT / CL=F) 24/7 CFD Swing Trading Engine.

Specialized for 2-3 day CFD positions on Revolut's Crude Oil Tracker (BRNT):
- Tracks NYMEX Crude Oil Futures (CL=F) which Revolut uses for BRNT pricing
- Long (Buy CFD) & Short (Sell CFD) execution
- 1-Hour & 4-Hour Trend Momentum + Dynamic ATR Risk Management
- Real-Time 5-minute news scraping & Google Gemini contextual catalyst evaluation
- 24/7 continuous monitoring with position state tracking and mobile push alerts via ntfy.sh
"""
import os
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import yfinance as yf
import feedparser

from news_sentiment import GeminiEnergyAnalyst, parse_llm_json
from notifier import UniversalNotifier
from indicators import compute_ema, compute_macd, compute_rsi, compute_atr


class BrentCFDEngine:
    """Dedicated Revolut Crude Oil Tracker (BRNT / CL=F) 24/7 Swing Trading Engine."""

    def __init__(self, ntfy_topic: str = "buzi-bot"):
        # Revolut's "BRNT - Crude oil tracker" uses NYMEX Light Sweet Crude (CL=F) futures pricing
        self.symbol = "CL=F"
        self.asset_name = "Revolut Crude Oil Tracker (BRNT)"
        self.ntfy_topic = ntfy_topic or os.getenv("NTFY_TOPIC", "buzi-bot")
        self.notifier = UniversalNotifier(ntfy_topic=self.ntfy_topic)
        self.gemini_analyst = GeminiEnergyAnalyst()
        
        self.state_file = Path(__file__).parent / "daemon_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        default_state = {
            "active_trade": None,
            "last_signal": "NONE",
            "last_pulse_time": 0,
            "last_news_hash": "",
            "trade_history": []
        }
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    # Migrate legacy state if needed
                    if "active_trade" not in data:
                        data["active_trade"] = None
                    if "trade_history" not in data:
                        data["trade_history"] = []
                    return data
            except Exception as e:
                print(f"[!] Warning reading state file: {e}")
        return default_state

    def _save_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[!] Error saving state: {e}")

    # =========================================================================
    # 1. Market Data Fetching (1-Hour Candles for 2-3 Day Swing Horizons)
    # =========================================================================
    def fetch_market_data(self) -> pd.DataFrame:
        """Fetch latest 1-hour candles for Revolut Crude Tracker (CL=F)."""
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period="1mo", interval="1h", auto_adjust=True)
            if not df.empty and len(df) >= 30:
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        except Exception as e:
            print(f"[!] yfinance fetch error: {e}")

        # Fallback to direct Yahoo Finance chart API
        try:
            import urllib.request
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.symbol}?interval=1h&range=1mo"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode())
                res = raw["chart"]["result"][0]
                timestamps = res["timestamp"]
                q = res["indicators"]["quote"][0]
                df = pd.DataFrame({
                    "Open": q["open"],
                    "High": q["high"],
                    "Low": q["low"],
                    "Close": q["close"],
                    "Volume": q.get("volume", [0]*len(q["open"]))
                }, index=pd.to_datetime(timestamps, unit="s")).dropna()
                return df
        except Exception as e2:
            print(f"[!] Yahoo REST fallback error: {e2}")

        raise RuntimeError("Failed to fetch Crude Oil market data from all sources.")

    def compute_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend momentum and ATR risk management metrics."""
        d = df.copy()
        d['ema_fast'] = compute_ema(d['Close'], 12)
        d['ema_slow'] = compute_ema(d['Close'], 26)
        macd, sig, hist = compute_macd(d['Close'], 12, 26, 9)
        d['macd'] = macd
        d['macd_sig'] = sig
        d['macd_hist'] = hist
        d['rsi'] = compute_rsi(d['Close'], 14)
        d['atr'] = compute_atr(d, 14)
        return d

    # =========================================================================
    # 2. Real-Time Crude News Scraper & Gemini AI Context
    # =========================================================================
    def fetch_brent_news(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetch breaking headlines specific to Crude Oil, OPEC+, EIA, and geopolitical energy supply."""
        articles = []
        try:
            query = "crude+oil+OR+WTI+OR+Brent+crude+OR+OPEC+OR+petroleum+inventory+OR+Strait+of+Hormuz"
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                published = entry.get("published", "")
                link = entry.get("link", "")
                source = entry.get("source", {}).get("title", "Energy Wire")

                if title:
                    articles.append({
                        "title": title,
                        "summary": "",
                        "publisher": source,
                        "pubDate": published,
                        "url": link
                    })
        except Exception as e:
            print(f"[!] Error fetching crude news: {e}")

        return articles

    def evaluate_news_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate breaking headlines using Google Gemini LLM with physical commodity reasoning."""
        if not articles:
            return {"score": 0.0, "regime": "NEUTRAL", "rationale": "No breaking headlines found."}

        # Check if headlines changed since last analysis to avoid unnecessary API calls
        content_str = "".join([a.get("title", "") for a in articles[:4]])
        current_hash = hashlib.md5(content_str.encode()).hexdigest()

        if self.gemini_analyst.is_active:
            res = self.gemini_analyst.analyze_news_batch("Crude Oil Tracker (CL=F / Revolut BRNT)", articles, sector="Energy")
            if res and res.get("rationale"):
                res["news_hash"] = current_hash
                return res

        # Lexicon Fallback if Gemini unavailable
        from news_sentiment import ENERGY_LEXICON
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        vader = SentimentIntensityAnalyzer()
        vader.lexicon.update(ENERGY_LEXICON)

        scores = [vader.polarity_scores(a['title'])['compound'] for a in articles]
        valid_scores = [s for s in scores if s != 0]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        if avg_score >= 0.15:
            regime = "STRONG BULLISH"
            rationale = "Prompt supply tightening or geopolitical shipping risks dominating."
        elif avg_score >= 0.05:
            regime = "MILD BULLISH"
            rationale = "Modest physical supply constraints supporting prompt Brent spreads."
        elif avg_score <= -0.15:
            regime = "STRONG BEARISH"
            rationale = "Unexpected inventory builds or weak refinery demand pressuring prices."
        elif avg_score <= -0.05:
            regime = "MILD BEARISH"
            rationale = "Demand softness or quota expansion concerns weighing on crude."
        else:
            regime = "NEUTRAL"
            rationale = "Physical Brent crude fundamentals balanced with no sharp catalyst."

        return {
            "score": round(avg_score, 3),
            "regime": regime,
            "rationale": rationale,
            "news_hash": current_hash,
            "model_used": "Fallback Lexicon"
        }

    # =========================================================================
    # 3. Swing CFD Decision Engine (2-3 Day Horizon)
    # =========================================================================
    def evaluate_trading_signals(self, df: pd.DataFrame, news_eval: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate 1H technical setup + Gemini Fundamental News for Long & Short CFD entries.
        Designed for swing positions held 2 to 3 days (48 to 72 hours).
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        price = float(latest['Close'])
        atr = float(latest['atr']) if not pd.isna(latest['atr']) else 0.90
        rsi = float(latest['rsi'])
        ema_fast = float(latest['ema_fast'])
        ema_slow = float(latest['ema_slow'])
        macd = float(latest['macd'])
        macd_sig = float(latest['macd_sig'])

        news_score = news_eval.get("score", 0.0)
        news_regime = news_eval.get("regime", "NEUTRAL")
        catalyst = news_eval.get("rationale", "")

        active_trade = self.state.get("active_trade")

        # ---------------------------------------------------------------------
        # A. MANAGE ACTIVE TRADE (Trailing Stop & Target Checks)
        # ---------------------------------------------------------------------
        if active_trade is not None:
            trade_type = active_trade["type"]  # "LONG" or "SHORT"
            entry_p = active_trade["entry_price"]
            stop_loss = active_trade["stop_loss"]
            take_profit = active_trade["take_profit"]
            entry_time = datetime.fromisoformat(active_trade["entry_time"])
            hours_held = (datetime.now() - entry_time).total_seconds() / 3600.0

            # 1. Update extreme prices for trailing stop
            if trade_type == "LONG":
                active_trade["highest_price"] = max(active_trade.get("highest_price", entry_p), price)
                # Trail stop loss upward as price advances (ratchet)
                new_trailing_sl = active_trade["highest_price"] - (1.5 * atr)
                if new_trailing_sl > stop_loss:
                    active_trade["stop_loss"] = round(new_trailing_sl, 2)
                    self._save_state()

                # Check Take Profit
                if price >= take_profit:
                    return {
                        "action": "EXIT",
                        "trade_type": "LONG",
                        "reason": f"🎯 Take Profit Hit (${price:.2f} >= ${take_profit:.2f})",
                        "price": price,
                        "pnl_pct": ((price - entry_p) / entry_p) * 100,
                        "hours_held": hours_held
                    }

                # Check Stop Loss
                if price <= stop_loss:
                    return {
                        "action": "EXIT",
                        "trade_type": "LONG",
                        "reason": f"🛑 Stop Loss Triggered (${price:.2f} <= ${stop_loss:.2f})",
                        "price": price,
                        "pnl_pct": ((price - entry_p) / entry_p) * 100,
                        "hours_held": hours_held
                    }

                # Check 2-3 Day Swing Horizon Time Stop (>= 72 hours)
                if hours_held >= 72 and (ema_fast < ema_slow or macd < macd_sig):
                    return {
                        "action": "EXIT",
                        "trade_type": "LONG",
                        "reason": f"⏱️ 3-Day Swing Duration Reached ({hours_held:.0f}h) & momentum softening",
                        "price": price,
                        "pnl_pct": ((price - entry_p) / entry_p) * 100,
                        "hours_held": hours_held
                    }

            elif trade_type == "SHORT":
                active_trade["lowest_price"] = min(active_trade.get("lowest_price", entry_p), price)
                # Trail stop loss downward as price falls
                new_trailing_sl = active_trade["lowest_price"] + (1.5 * atr)
                if new_trailing_sl < stop_loss:
                    active_trade["stop_loss"] = round(new_trailing_sl, 2)
                    self._save_state()

                # Check Take Profit
                if price <= take_profit:
                    return {
                        "action": "EXIT",
                        "trade_type": "SHORT",
                        "reason": f"🎯 Take Profit Hit (${price:.2f} <= ${take_profit:.2f})",
                        "price": price,
                        "pnl_pct": ((entry_p - price) / entry_p) * 100,
                        "hours_held": hours_held
                    }

                # Check Stop Loss
                if price >= stop_loss:
                    return {
                        "action": "EXIT",
                        "trade_type": "SHORT",
                        "reason": f"🛑 Stop Loss Triggered (${price:.2f} >= ${stop_loss:.2f})",
                        "price": price,
                        "pnl_pct": ((entry_p - price) / entry_p) * 100,
                        "hours_held": hours_held
                    }

                # Check 2-3 Day Swing Horizon Time Stop (>= 72 hours)
                if hours_held >= 72 and (ema_fast > ema_slow or macd > macd_sig):
                    return {
                        "action": "EXIT",
                        "trade_type": "SHORT",
                        "reason": f"⏱️ 3-Day Swing Duration Reached ({hours_held:.0f}h) & momentum turning",
                        "price": price,
                        "pnl_pct": ((entry_p - price) / entry_p) * 100,
                        "hours_held": hours_held
                    }

            # Still in trade
            return {
                "action": "HOLD",
                "trade_type": trade_type,
                "price": price,
                "entry_price": entry_p,
                "stop_loss": active_trade["stop_loss"],
                "take_profit": take_profit,
                "pnl_pct": ((price - entry_p) / entry_p * 100) if trade_type == "LONG" else ((entry_p - price) / entry_p * 100),
                "hours_held": hours_held
            }

        # ---------------------------------------------------------------------
        # B. SEARCH FOR NEW 2-3 DAY SWING CFD ENTRIES (Long or Short)
        # ---------------------------------------------------------------------
        # Bullish criteria: Trend + Momentum + Gemini Fundamental Alignment
        is_bullish_tech = (ema_fast > ema_slow) and (macd > macd_sig) and (42 <= rsi <= 68)
        is_bullish_news = (news_score >= 0.08)

        # Bearish criteria: Trend breakdown + Bearish Momentum + Gemini Fundamental Bearishness
        is_bearish_tech = (ema_fast < ema_slow) and (macd < macd_sig) and (32 <= rsi <= 58)
        is_bearish_news = (news_score <= -0.08)

        # 1. LONG CFD ENTRY TRIGGER
        if is_bullish_tech and (is_bullish_news or news_score >= -0.05):
            sl = round(price - (1.5 * atr), 2)
            tp = round(price + (2.5 * atr), 2)
            return {
                "action": "OPEN_LONG",
                "price": price,
                "stop_loss": sl,
                "take_profit": tp,
                "atr": atr,
                "rsi": rsi,
                "catalyst": catalyst,
                "tech_reason": f"1H EMA(12) > EMA(26), MACD Bullish Crossover, RSI {rsi:.1f}, 14H ATR: ${atr:.2f}"
            }

        # 2. SHORT CFD ENTRY TRIGGER
        elif is_bearish_tech and (is_bearish_news or news_score <= 0.05):
            sl = round(price + (1.5 * atr), 2)
            tp = round(price - (2.5 * atr), 2)
            return {
                "action": "OPEN_SHORT",
                "price": price,
                "stop_loss": sl,
                "take_profit": tp,
                "atr": atr,
                "rsi": rsi,
                "catalyst": catalyst,
                "tech_reason": f"1H EMA(12) < EMA(26), MACD Bearish Breakdown, RSI {rsi:.1f}, 14H ATR: ${atr:.2f}"
            }

        return {
            "action": "NEUTRAL",
            "price": price,
            "rsi": rsi,
            "atr": atr,
            "news_score": news_score,
            "news_regime": news_regime,
            "catalyst": catalyst
        }

    # =========================================================================
    # 4. Push Notification Dispatchers
    # =========================================================================
    def notify_trade_open(self, trade_type: str, price: float, stop_loss: float, target: float, catalyst: str, tech_reason: str):
        """Send actionable mobile alert when a new 2-3 day CFD position opens."""
        icon = "🟢" if trade_type == "LONG" else "🔴"
        action_text = f"OPEN {trade_type} (BUY CFD)" if trade_type == "LONG" else f"OPEN {trade_type} (SELL CFD)"
        risk_per_bbl = abs(price - stop_loss)
        reward_per_bbl = abs(target - price)

        title = f"{icon} [Revolut BRNT] {action_text} @ ${price:.2f}"
        msg = f"""*ACTION*: *{action_text}*
🛢️ *Instrument*: Revolut Crude Oil Tracker (BRNT)
💵 *Entry Price*: ${price:.2f}
🛑 *Stop Loss*: ${stop_loss:.2f} (Risk: -${risk_per_bbl:.2f}/bbl)
🎯 *Take Profit*: ${target:.2f} (Reward: +${reward_per_bbl:.2f}/bbl)
⏱️ *Target Horizon*: 2–3 Days Swing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 *AI Fundamental Catalyst [Gemini LLM]*:
{catalyst}

📈 *Technical Setup*: {tech_reason}
📱 *Revolut*: Ready to trade on Revolut 'BRNT'."""

        print(f"\n[>>> DISPATCHING {trade_type} CFD ENTRY ALERT >>>]")
        self.notifier.send_message(msg, title=title, priority="high")

    def notify_trade_exit(self, trade_type: str, price: float, pnl_pct: float, hours_held: float, reason: str):
        """Send mobile alert when active CFD position closes."""
        pnl_icon = "💰" if pnl_pct >= 0 else "🛑"
        days_held = hours_held / 24.0

        title = f"{pnl_icon} [Revolut BRNT] CLOSE {trade_type} @ ${price:.2f} ({pnl_pct:+.2f}%)"
        msg = f"""*ACTION*: *CLOSE {trade_type} POSITION*
🛢️ *Instrument*: Revolut Crude Oil Tracker (BRNT)
💵 *Exit Price*: ${price:.2f}
{pnl_icon} *Return*: *{pnl_pct:+.2f}%*
⏱️ *Duration*: {days_held:.1f} Days ({hours_held:.0f} hours)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Exit Reason*: {reason}
📱 *Revolut*: Close active position in Revolut app."""

        print(f"\n[>>> DISPATCHING CFD EXIT ALERT ({pnl_pct:+.2f}%) >>>]")
        self.notifier.send_message(msg, title=title, priority="high")

    def notify_market_pulse(self, price: float, news_eval: Dict[str, Any], rsi: float, atr: float):
        """Send regular market status digest so the user is never in the dark."""
        active = self.state.get("active_trade")
        status_line = "No Open Position (Monitoring next 2-3 day swing window)"
        if active:
            t_type = active["type"]
            e_p = active["entry_price"]
            pnl = ((price - e_p) / e_p * 100) if t_type == "LONG" else ((e_p - price) / e_p * 100)
            status_line = f"Active {t_type} (Entry: ${e_p:.2f}, P&L: {pnl:+.2f}%)"

        title = f"🛢️ [Revolut BRNT] Market Pulse: ${price:.2f}"
        msg = f"""🛢️ *Revolut Crude Tracker (BRNT)*: *${price:.2f}*
📊 *1H RSI*: {rsi:.1f} | *14H ATR*: ${atr:.2f}
🧠 *AI News Regime*: {news_eval.get('regime', 'NEUTRAL')} ({news_eval.get('score', 0.0):+.2f})
📋 *Position Status*: {status_line}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Latest Catalyst*: {news_eval.get('rationale', 'Market balanced.')}"""

        print("\n[>>> DISPATCHING MARKET PULSE DIGEST >>>]")
        self.notifier.send_message(msg, title=title, priority="default")

    # =========================================================================
    # 5. Continuous 5-Minute 24/7 Scan Cycle
    # =========================================================================
    def run_single_cycle(self, send_pulse_if_due: bool = True) -> Dict[str, Any]:
        """Execute one complete 5-minute news & price scan cycle."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now_str}] 🔍 Scanning Revolut Crude Oil Tracker ({self.symbol})...")

        df = self.fetch_market_data()
        df = self.compute_technical_indicators(df)
        articles = self.fetch_brent_news(limit=6)
        news_eval = self.evaluate_news_sentiment(articles)

        decision = self.evaluate_trading_signals(df, news_eval)
        action = decision.get("action")
        price = decision.get("price", df['Close'].iloc[-1])
        rsi = float(df['rsi'].iloc[-1])
        atr = float(df['atr'].iloc[-1]) if not pd.isna(df['atr'].iloc[-1]) else 0.85

        print(f"  • Price: ${price:.2f} | RSI: {rsi:.1f} | ATR: ${atr:.2f}")
        print(f"  • AI Sentiment: {news_eval.get('regime')} ({news_eval.get('score'):+.2f})")
        print(f"  • Decision: {action}")

        # 1. Process New Entry
        if action in ["OPEN_LONG", "OPEN_SHORT"]:
            trade_type = "LONG" if action == "OPEN_LONG" else "SHORT"
            sl = decision["stop_loss"]
            tp = decision["take_profit"]
            cat = decision["catalyst"]
            tech_r = decision["tech_reason"]

            self.notify_trade_open(trade_type, price, sl, tp, cat, tech_r)
            self.state["active_trade"] = {
                "type": trade_type,
                "entry_price": price,
                "entry_time": datetime.now().isoformat(),
                "stop_loss": sl,
                "take_profit": tp,
                "highest_price": price,
                "lowest_price": price,
                "atr_entry": atr,
                "catalyst": cat
            }
            self.state["last_signal"] = trade_type
            self._save_state()

        # 2. Process Exit
        elif action == "EXIT":
            trade_type = decision["trade_type"]
            pnl_pct = decision["pnl_pct"]
            hours_held = decision["hours_held"]
            reason = decision["reason"]

            self.notify_trade_exit(trade_type, price, pnl_pct, hours_held, reason)
            
            # Record in history
            closed_trade = self.state["active_trade"] or {}
            closed_trade["exit_price"] = price
            closed_trade["exit_time"] = datetime.now().isoformat()
            closed_trade["pnl_pct"] = pnl_pct
            closed_trade["reason"] = reason
            self.state["trade_history"].append(closed_trade)

            self.state["active_trade"] = None
            self.state["last_signal"] = "EXIT"
            self._save_state()

        # 3. Regular Market Pulse (sent every 12 hours or on forced flag)
        now_ts = time.time()
        last_pulse = self.state.get("last_pulse_time", 0)
        if send_pulse_if_due and (now_ts - last_pulse >= 43200):  # 12 hours = 43200 seconds
            self.notify_market_pulse(price, news_eval, rsi, atr)
            self.state["last_pulse_time"] = now_ts
            self._save_state()

        return decision

    def start_continuous_loop(self, duration_minutes: int = 240, interval_seconds: int = 300, send_pulse_on_start: bool = False):
        """
        Run continuous 24/7 loop for duration_minutes, checking every interval_seconds.
        Designed for persistent GitHub Actions runners and local background operation.
        """
        print("=" * 70)
        print("   🛢️ REVOLUT CRUDE OIL TRACKER (BRNT) 24/7 CFD SWING ENGINE")
        print(f"  • Asset: {self.asset_name} ({self.symbol})")
        print(f"  • Scan Interval: Every {interval_seconds} seconds ({interval_seconds/60:.1f} mins)")
        print(f"  • Session Duration: {duration_minutes} minutes ({duration_minutes/60:.1f} hours)")
        print(f"  • Mobile Notification Topic: '{self.ntfy_topic}'")
        print("=" * 70)

        if send_pulse_on_start:
            df = self.fetch_market_data()
            df = self.compute_technical_indicators(df)
            articles = self.fetch_brent_news(limit=6)
            news_eval = self.evaluate_news_sentiment(articles)
            price = float(df['Close'].iloc[-1])
            rsi = float(df['rsi'].iloc[-1])
            atr = float(df['atr'].iloc[-1]) if not pd.isna(df['atr'].iloc[-1]) else 0.85
            self.notify_market_pulse(price, news_eval, rsi, atr)
            self.state["last_pulse_time"] = time.time()
            self._save_state()

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        cycle_count = 0

        while time.time() < end_time:
            cycle_count += 1
            print(f"\n--- [Cycle #{cycle_count}] Remaining Session: {(end_time - time.time())/60:.1f} mins ---")
            try:
                self.run_single_cycle(send_pulse_if_due=True)
            except Exception as e:
                print(f"[!] Error in scan cycle #{cycle_count}: {e}")

            time.sleep(interval_seconds)

        print(f"\n[✓] Continuous session completed after {cycle_count} cycles. State persisted.")
