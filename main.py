"""Main Entry Point for Oil Stock Trading Bot."""
import argparse
from tabulate import tabulate

from config import BotConfig
from backtester import BacktestEngine
from scanner import MarketScanner
from news_sentiment import OilSentimentAnalyzer
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
    print("           🌍 MACRO CRUDE OIL & GEOPOLITICAL SENTIMENT")
    print("=" * 80)
    macro_score = report.get("macro_score", 0.0)
    print(f"Overall Macro Score: {macro_score:+.3f}")
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
            "Articles Analyzed": sdata["news_count"]
        })
    print(tabulate(summary_table, headers="keys", tablefmt="fancy_grid"))
    print("=" * 80 + "\n")


def run_live(args):
    symbols = args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]
    config = BotConfig(
        symbols=symbols,
        mode=args.mode,
        scan_interval_minutes=args.interval,
        ntfy_topic=args.ntfy or "",
        telegram_bot_token=args.tg_token or "",
        telegram_chat_id=args.tg_chat or ""
    )
    daemon = LiveDaemon(config)
    daemon.start_loop()


def run_check_and_notify(args):
    """Single scan cycle designed for scheduled cloud runners (e.g. GitHub Actions)."""
    symbols = args.symbols.split(",") if args.symbols else ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]
    config = BotConfig(
        symbols=symbols,
        mode=args.mode,
        ntfy_topic=args.ntfy or ""
    )
    daemon = LiveDaemon(config)
    daemon.run_cycle()


def test_alert(args):
    config = BotConfig()
    notifier = UniversalNotifier(
        ntfy_topic=args.ntfy or config.ntfy_topic,
        telegram_bot_token=args.tg_token or config.telegram_bot_token,
        telegram_chat_id=args.tg_chat or config.telegram_chat_id,
        whatsapp_phone=args.phone or config.whatsapp_phone,
        callmebot_api_key=args.apikey or config.callmebot_api_key
    )
    print(f"\n[+] Testing Notification Dispatcher...")
    notifier.send_trade_signal(
        symbol="XOM",
        action="BUY",
        price=160.59,
        stop_loss=150.56,
        target=176.64,
        catalyst="\"OPEC+ weighs extending output cuts into next quarter\" (Reuters)",
        tech_reason="Fast EMA(12) crossed above Slow EMA(26) & Bullish MACD"
    )


def main():
    parser = argparse.ArgumentParser(description="Automated Oil Stock Trading Bot with Push Alerts")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Cloud runner check-and-notify
    cron_parser = subparsers.add_parser("check-and-notify", help="Run single scan and notify (ideal for GitHub Actions)")
    cron_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")
    cron_parser.add_argument("--mode", type=str, default="trend_dynamic")
    cron_parser.add_argument("--ntfy", type=str, default=None)

    # Live daemon subcommand
    live_parser = subparsers.add_parser("live", help="Start continuous live daemon with push alerts")
    live_parser.add_argument("--symbols", type=str, default="XOM,CVX,OXY,COP,BP,SHEL")
    live_parser.add_argument("--mode", type=str, default="trend_dynamic", choices=["trend_dynamic", "leveraged_crude", "long_short"])
    live_parser.add_argument("--interval", type=int, default=15, help="Scan interval in minutes")
    live_parser.add_argument("--ntfy", type=str, default=None, help="Private ntfy topic name")
    live_parser.add_argument("--tg-token", type=str, default=None, help="Telegram bot token")
    live_parser.add_argument("--tg-chat", type=str, default=None, help="Telegram chat ID")

    # Test alert subcommand
    test_parser = subparsers.add_parser("test-alert", help="Send a test trade alert to your phone")
    test_parser.add_argument("--ntfy", type=str, default=None, help="Private ntfy topic name")
    test_parser.add_argument("--tg-token", type=str, default=None, help="Telegram bot token")
    test_parser.add_argument("--tg-chat", type=str, default=None, help="Telegram chat ID")
    test_parser.add_argument("--phone", type=str, default=None, help="Phone number")
    test_parser.add_argument("--apikey", type=str, default=None, help="CallMeBot API key")

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
