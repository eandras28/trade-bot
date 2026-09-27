"""Live Monitoring Daemon for Oil Trading Bot with Universal Push Notifications."""
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from config import BotConfig
from scanner import MarketScanner
from notifier import UniversalNotifier


class LiveDaemon:
    def __init__(self, config: BotConfig):
        self.config = config
        self.scanner = MarketScanner(config)
        self.notifier = UniversalNotifier(
            ntfy_topic=config.ntfy_topic,
            telegram_bot_token=config.telegram_bot_token,
            telegram_chat_id=config.telegram_chat_id,
            whatsapp_phone=config.whatsapp_phone,
            callmebot_api_key=config.callmebot_api_key,
            twilio_account_sid=config.twilio_account_sid,
            twilio_auth_token=config.twilio_auth_token
        )
        self.state_file = Path(__file__).parent / "daemon_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"positions": {}, "last_signals": {}}

    def _save_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def run_cycle(self):
        """Execute a single scan cycle and notify if new action is required."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Running Live Scan across Revolut universe: {self.config.symbols}...")

        scan_result = self.scanner.scan_universe(include_news=True)
        table = scan_result.get("table", [])
        sent_rep = scan_result.get("sentiment_report", {})
        macro_score = sent_rep.get("macro_score", 0.0)
        engine_mode = sent_rep.get("engine_mode", "Energy Domain Lexicon")

        for row in table:
            sym = row["Symbol"]
            sector = row.get("Sector", "Equities")
            price = row["Price ($)"]
            decision = row["Combined Decision"]
            stop_loss = float(row["Stop Loss"].replace("$", ""))
            rationale = row.get("Rationale", "Macro momentum & catalyst alignment")
            sym_macro_score = sent_rep.get("symbols", {}).get(sym, {}).get("macro_score", 0.0)

            last_signal = self.state["last_signals"].get(sym, "NONE")

            # 1. NEW BUY TRIGGER
            if "BUY" in decision and "BUY" not in last_signal:
                print(f"[!] New BUY Alert detected for {sym} ({sector}) at ${price:.2f} [Engine: {engine_mode}]")
                target_price = price * 1.10
                self.notifier.send_trade_signal(
                    symbol=sym,
                    action="BUY",
                    price=price,
                    stop_loss=stop_loss,
                    target=target_price,
                    catalyst=rationale,
                    engine_name=engine_mode,
                    tech_reason=f"Fast EMA > Slow EMA, RSI {row['RSI']}, Sector Macro: {sym_macro_score:+.2f}",
                    sector=sector
                )
                self.state["positions"][sym] = {
                    "entry_price": price,
                    "stop_loss": stop_loss,
                    "entry_time": timestamp,
                    "sector": sector
                }
                self.state["last_signals"][sym] = "BUY"
                self._save_state()

            # 2. NEW EXIT / SELL TRIGGER
            elif ("EXIT" in decision or "SHORT" in decision or "BEARISH" in row["Tech Regime"]) and last_signal == "BUY":
                print(f"[!] EXIT Alert detected for {sym} ({sector}) at ${price:.2f} [Engine: {engine_mode}]")
                entry_info = self.state["positions"].pop(sym, {})
                entry_p = entry_info.get("entry_price", price)
                ret_pct = ((price - entry_p) / entry_p) * 100 if entry_p else 0.0

                self.notifier.send_trade_signal(
                    symbol=sym,
                    action="EXIT",
                    price=price,
                    stop_loss=None,
                    target=None,
                    catalyst=rationale,
                    engine_name=engine_mode,
                    tech_reason=f"Regime breakdown. Return: {ret_pct:+.2f}%",
                    sector=sector
                )
                self.state["last_signals"][sym] = "EXIT"
                self._save_state()

            elif "BUY" not in decision:
                self.state["last_signals"][sym] = decision

        self._save_state()
        print(f"[{timestamp}] Scan completed using [{engine_mode}]. Next cycle in {self.config.scan_interval_minutes} minutes.")

    def start_loop(self):
        print("=" * 65)
        print("      🛢️  OIL TRADING BOT: LIVE PUSH DAEMON STARTED")
        print(f"  • Revolut Universe: {self.config.symbols}")
        print(f"  • Polling Frequency: Every {self.config.scan_interval_minutes} minutes")
        print("=" * 65)

        self.notifier.send_message(
            "🤖 *Oil Trading Bot Active*\n"
            f"Now scanning Revolut energy stocks ({', '.join(self.config.symbols)}) & breaking oil news.\n"
            "You will receive instant alerts for entries, stop-losses, and profit targets.",
            title="🟢 Bot Activated"
        )

        while True:
            try:
                self.run_cycle()
            except Exception as e:
                print(f"[!] Error in daemon cycle: {e}")
            
            time.sleep(self.config.scan_interval_minutes * 60)
