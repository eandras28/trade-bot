"""Main Entry Point for Oil Stock Trading Bot."""
import os
import argparse
from tabulate import tabulate

from config import BotConfig
from backtester import BacktestEngine
from scanner import MarketScanner
from news_sentiment import OilSentimentAnalyzer, GeminiEnergyAnalyst
from notifier import UniversalNotifier
from live_daemon import LiveDaemon


def run_backtest(args):
    config = BotConfig(
        symbols=args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"],
        mode=args.mode,
        start_date=args.start,
        initial_capital=args.capital
    )
    active = config.leveraged_symbols if config.mode == "leveraged_crude" else config.symbols
    print(f"\n[+] Running Backtest (Mode: {config.mode.upper()})")
    print(f"[+] Universe: {active} | Macro Anchor: {config.macro_symbol}")
    print(f"[+] Period: {config.start_date} to {config.end_date or 'Present'}")
    print(f"[+] Initial Capital: ${config.initial_capital:,.2f}\n")

    engine = BacktestEngine(config)
    equity_df, trades, metrics = engine.run()

    print("=" * 60)
    print("             📊 BACKTEST PERFORMANCE SUMMARY")
    print("=" * 60)
    table_data = [[k, v] for k, v in metrics.items()]
    print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="fancy_grid"))

    output_img = f"backtest_{config.mode}.png"
    engine.plot_results(equity_df, save_path=output_img)
    print(f"\n[✓] Equity curve chart saved to: {output_img}")


def run_scan(args):
    symbols = args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]
    config = BotConfig(symbols=symbols, mode=args.mode)
    scanner = MarketScanner(config)
    scanner.print_scan_report()


def run_news(args):
    symbols = args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]
    analyzer = OilSentimentAnalyzer()
    print("\n🔍 Fetching latest energy news and evaluating sentiment...")
    report = analyzer.get_market_sentiment_report(symbols)

    print("\n" + "=" * 80)
    print(f"       🌍 MACRO CRUDE OIL & GEOPOLITICAL SENTIMENT [{report.get('engine_mode', '')}]")
    print("=" * 80)
    macro_score = report.get("macro_score", 0.0)
    print(f"Overall Macro Score: {macro_score:+.3f}")
    if report.get("macro_rationale"):
        print(f"AI Rationale: {report.get('macro_rationale')}")

    print("\nTop Macro Headlines:")
    for a in report.get("top_macro_news", [])[:6]:
        icon = "🟢" if a['score'] > 0.1 else "🔴" if a['score'] < -0.1 else "⚪"
        print(f"  {icon} [{a['score']:+.2f}] {a['title']} ({a['publisher']})")

    print("\n" + "=" * 80)
    print("           🏢 REVOLUT ENERGY EQUITIES SENTIMENT")
    print("=" * 80)
    summary_table = []
    for sym, sdata in report.get("symbols", {}).items():
        summary_table.append({
            "Symbol": sym,
            "Composite Score": f"{sdata['composite_score']:+.3f}",
            "Ticker Score": f"{sdata['ticker_score']:+.3f}",
            "Sentiment Regime": sdata["sentiment_regime"],
            "Articles": sdata["news_count"]
        })
    print(tabulate(summary_table, headers="keys", tablefmt="fancy_grid"))
    print("=" * 80 + "\n")


def run_live(args):
    symbols = args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]
    config = BotConfig(
        symbols=symbols,
        mode=args.mode,
        scan_interval_minutes=args.interval,
        ntfy_topic=args.ntfy or "buzi-bot",
        telegram_bot_token=args.tg_token or "",
        telegram_chat_id=args.tg_chat or ""
    )
    daemon = LiveDaemon(config)
    daemon.start_loop()


def run_check_and_notify(args):
    symbols = args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]
    config = BotConfig(
        symbols=symbols,
        mode=args.mode,
        ntfy_topic=args.ntfy or "buzi-bot"
    )
    daemon = LiveDaemon(config)
    daemon.run_cycle()


def test_alert(args):
    notifier = UniversalNotifier(ntfy_topic=args.ntfy or "buzi-bot")
    print(f"\n[+] Testing Notification Dispatcher to topic: {notifier.ntfy_topic}...")
    notifier.send_trade_signal(
        symbol="XOM",
        action="BUY",
        price=160.59,
        stop_loss=150.56,
        target=176.64,
        catalyst="\"OPEC+ weighs extending output cuts into next quarter\" (Reuters)",
        engine_name="Energy Domain Lexicon",
        tech_reason="Fast EMA(12) crossed above Slow EMA(26) & Bullish MACD"
    )


def test_gemini(args):
    api_key = args.key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    target_topic = args.ntfy or "buzi-bot"
    notifier = UniversalNotifier(ntfy_topic=target_topic)

    if not api_key:
        print("\n[!] Error: No Gemini API Key provided.")
        print("Please ensure the secret name is GEMINI_API_KEY under GitHub Repository Secrets.")
        notifier.send_message(
            "⚠️ *Gemini Test Notice*\n"
            "The cloud runner did not detect `GEMINI_API_KEY`.\n\n"
            "Please check GitHub: *Settings -> Secrets and variables -> Actions -> Repository Secrets* "
            "and verify the secret is named exactly *GEMINI_API_KEY*.",
            title="⚠️ GEMINI_API_KEY Missing"
        )
        return

    print("\n[1] Initializing Google Gemini LLM Client...")
    analyst = GeminiEnergyAnalyst(api_key=api_key)
    if not analyst.is_active:
        print("[!] Failed to initialize Gemini. Check that your API key is valid.")
        notifier.send_message(
            "⚠️ *Gemini Test Notice*\n"
            "The Gemini Client failed to initialize. Please check that your API key is active and valid.",
            title="⚠️ Gemini Key Invalid"
        )
        return

    print("[2] Fetching live breaking news headlines for ExxonMobil (XOM)...")
    analyzer = OilSentimentAnalyzer()
    articles = analyzer.fetch_ticker_news("XOM", limit=5)
    if not articles:
        articles = analyzer.fetch_macro_crude_news(limit=5)

    print(f"[3] Sending {len(articles)} real headlines to Gemini for quantitative analysis...")
    for a in articles[:3]:
        print(f"  • {a['title']}")

    llm_result = analyst.analyze_news_batch("ExxonMobil (XOM)", articles)
    target_topic = args.ntfy or "buzi-bot"
    notifier = UniversalNotifier(ntfy_topic=target_topic)

    if not llm_result or not llm_result.get("rationale"):
        print("[!] Gemini API call failed to produce analysis. Check API key permissions.")
        notifier.send_message(
            "⚠️ *Gemini Call Failed*\n"
            "The Gemini API key was loaded, but the API request failed.\n"
            "Please check that your key from https://aistudio.google.com/app/apikey is active.",
            title="⚠️ Gemini API Call Failed"
        )
        return

    model_used = llm_result.get("model_used", "gemini-1.5-flash")
    print(f"\n[4] Gemini LLM Response ({model_used}):")
    print(f"  Score:    {llm_result.get('score', 0.0):+0.2f}")
    print(f"  Regime:   {llm_result.get('regime', 'N/A')}")
    print(f"  Rationale: {llm_result.get('rationale', 'N/A')}")

    print(f"\n[5] Dispatching Gemini-generated alert to your phone via '{target_topic}'...")
    notifier.send_trade_signal(
        symbol="XOM",
        action="BUY",
        price=160.59,
        stop_loss=150.56,
        target=176.64,
        catalyst=llm_result["rationale"],
        engine_name="Gemini LLM Contextual",
        tech_reason=f"Fast EMA(12) > Slow EMA(26), RSI 48.9, Gemini Catalyst [{model_used}]"
    )
    print(f"\n[✓] Successfully delivered Gemini-powered trade alert to your phone!")


def main():
    parser = argparse.ArgumentParser(description="Automated Oil Stock Trading Bot with Push Alerts")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Cloud runner check-and-notify
    cron_parser = subparsers.add_parser("check-and-notify", help="Run single scan and notify (ideal for GitHub Actions)")
    cron_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")
    cron_parser.add_argument("--mode", type=str, default="trend_dynamic")
    cron_parser.add_argument("--ntfy", type=str, default="buzi-bot")

    # Live daemon subcommand
    live_parser = subparsers.add_parser("live", help="Start continuous live daemon with push alerts")
    live_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")
    live_parser.add_argument("--mode", type=str, default="trend_dynamic", choices=["trend_dynamic", "leveraged_crude", "long_short"])
    live_parser.add_argument("--interval", type=int, default=15)
    live_parser.add_argument("--ntfy", type=str, default="buzi-bot")
    live_parser.add_argument("--tg-token", type=str, default=None)
    live_parser.add_argument("--tg-chat", type=str, default=None)

    # Test alert subcommand
    test_parser = subparsers.add_parser("test-alert", help="Send a test trade alert to your phone")
    test_parser.add_argument("--ntfy", type=str, default="buzi-bot")

    # Test gemini subcommand
    gemini_parser = subparsers.add_parser("test-gemini", help="Test live Gemini LLM reasoning and send alert")
    gemini_parser.add_argument("--key", type=str, default=None, help="Gemini API Key")
    gemini_parser.add_argument("--ntfy", type=str, default="buzi-bot", help="ntfy topic")

    # Backtest subcommand
    backtest_parser = subparsers.add_parser("backtest", help="Run historical backtest")
    backtest_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")
    backtest_parser.add_argument("--mode", type=str, default="trend_dynamic", choices=["trend_dynamic", "leveraged_crude", "long_short"])
    backtest_parser.add_argument("--start", type=str, default="2020-09-26")
    backtest_parser.add_argument("--capital", type=float, default=100000.0)

    # Scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan technicals + live news sentiment")
    scan_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")
    scan_parser.add_argument("--mode", type=str, default="trend_dynamic", choices=["trend_dynamic", "leveraged_crude", "long_short"])

    # News subcommand
    news_parser = subparsers.add_parser("news", help="Deep dive into current news sentiment and catalysts")
    news_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")

    args = parser.parse_args()

    if args.command == "check-and-notify":
        run_check_and_notify(args)
    elif args.command == "live":
        run_live(args)
    elif args.command == "test-alert":
        test_alert(args)
    elif args.command == "test-gemini":
        test_gemini(args)
    elif args.command == "backtest":
        run_backtest(args)
    elif args.command == "scan":
        run_scan(args)
    elif args.command == "news":
        run_news(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
