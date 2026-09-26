"""Daily Scanner combining Multi-Strategy Technicals with Live News & Geopolitical Sentiment."""
from typing import Dict, Any, List
import pandas as pd
from tabulate import tabulate

from config import BotConfig
from data import MarketDataLoader
from strategy import MultiStrategyEngine
from news_sentiment import OilSentimentAnalyzer


class MarketScanner:
    def __init__(self, config: BotConfig):
        self.config = config
        self.data_loader = MarketDataLoader()
        self.strategy_engine = MultiStrategyEngine(config)
        self.sentiment_analyzer = OilSentimentAnalyzer()

    def scan_universe(self, include_news: bool = True) -> Dict[str, Any]:
        """Scan symbols for technical signals and news sentiment."""
        results = []
        active_symbols = list(self.config.symbols)
        if self.config.mode == "leveraged_crude":
            active_symbols = list(self.config.leveraged_symbols)

        all_fetch = list(set(active_symbols + [self.config.macro_symbol]))
        raw_data = self.data_loader.fetch_all(
            all_fetch,
            start_date="2023-01-01",
            force_refresh=True
        )

        sentiment_data = {}
        if include_news:
            sentiment_data = self.sentiment_analyzer.get_market_sentiment_report(active_symbols)

        processed = self.strategy_engine.prepare_data(raw_data)

        for symbol in active_symbols:
            if symbol not in processed:
                continue

            df = processed[symbol]
            if df.empty or len(df) < 50:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            signal_val = latest['signal']
            prev_signal_val = prev['signal']

            # Technical Status
            if signal_val == 1 and prev_signal_val != 1:
                tech_status = "NEW BUY"
            elif signal_val == 1:
                tech_status = "BULLISH"
            elif signal_val in [-1, -2] and prev_signal_val not in [-1, -2]:
                tech_status = "NEW EXIT / SHORT"
            elif signal_val in [-1, -2]:
                tech_status = "BEARISH"
            else:
                tech_status = "NEUTRAL"

            # News Sentiment Score
            news_info = sentiment_data.get("symbols", {}).get(symbol, {})
            sentiment_score = news_info.get("composite_score", 0.0)

            # Combined AI Conviction Signal
            if tech_status in ["NEW BUY", "BULLISH"] and sentiment_score >= 0.15:
                conviction = "🔥 HIGH CONVICTION BUY"
            elif tech_status in ["NEW BUY", "BULLISH"] and sentiment_score < -0.10:
                conviction = "⚠️ DIVERGENCE (Tech Up / News Down)"
            elif tech_status in ["NEW BUY", "BULLISH"]:
                conviction = "🟢 MODERATE BUY / HOLD"
            elif tech_status in ["NEW EXIT / SHORT", "BEARISH"] and sentiment_score <= -0.15:
                conviction = "🛑 HIGH CONVICTION SHORT / CASH"
            elif tech_status in ["NEW EXIT / SHORT", "BEARISH"]:
                conviction = "🔴 DEFENSIVE / CASH"
            else:
                conviction = "⚪ NEUTRAL / WAIT"

            close = latest['Close']
            atr = latest['atr']
            stop_loss = close - (atr * self.config.atr_stop_multiplier)
            take_profit = close + (atr * self.config.atr_profit_multiplier) if self.config.atr_profit_multiplier else None

            results.append({
                "Symbol": symbol,
                "Price ($)": round(close, 2),
                "Combined Decision": conviction,
                "News Sent.": f"{sentiment_score:+.2f}",
                "Tech Regime": tech_status,
                "RSI": round(latest['rsi'], 1),
                "MACD": round(latest['macd'], 2),
                "EMA 12/26": f"{latest['ema_fast']:.1f}/{latest['ema_slow']:.1f}",
                "Stop Loss": f"${stop_loss:.2f}",
                "Target": f"${take_profit:.2f}" if take_profit else "Trailing Stop"
            })

        return {
            "table": results,
            "sentiment_report": sentiment_data
        }

    def print_scan_report(self):
        """Print full combined scan and news catalyst report."""
        scan_output = self.scan_universe(include_news=True)
        results = scan_output["table"]
        sent_rep = scan_output["sentiment_report"]

        print("\n" + "=" * 105)
        print(f"       🛢️  OIL TRADING BOT: MULTI-FACTOR SCANNER (MODE: {self.config.mode.upper()})")
        print("=" * 105)
        print(tabulate(results, headers="keys", tablefmt="fancy_grid"))

        if sent_rep:
            macro_score = sent_rep.get("macro_score", 0.0)
            print(f"\n🌍 MACRO CRUDE & GEOPOLITICAL SENTIMENT: {macro_score:+.3f} "
                  f"({'🟢 BULLISH SUPPLY SQUEEZE' if macro_score > 0.1 else '🔴 BEARISH SURPLUS/EASING' if macro_score < -0.1 else '⚪ NEUTRAL'})")

            print("\n📰 TOP BREAKING MACRO CATALYSTS:")
            for a in sent_rep.get("top_macro_news", [])[:4]:
                score_icon = "🟢" if a['score'] > 0.1 else "🔴" if a['score'] < -0.1 else "⚪"
                print(f"  {score_icon} [{a['score']:+.2f}] {a['title']} ({a['publisher']})")

            print("\n🗞️ KEY COMPANY/ETF HEADLINES:")
            for sym, sdata in sent_rep.get("symbols", {}).items():
                articles = sdata.get("top_articles", [])
                if articles:
                    top = articles[0]
                    score_icon = "🟢" if top['score'] > 0.1 else "🔴" if top['score'] < -0.1 else "⚪"
                    print(f"  • {sym} ({sdata['composite_score']:+.2f}): {score_icon} {top['title']} ({top['publisher']})")

        print("=" * 105 + "\n")
