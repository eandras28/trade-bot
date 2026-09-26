"""Configuration settings for the Oil Stock Trading Bot."""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BotConfig:
    # Revolut Hungary Energy Equities Universe
    symbols: List[str] = field(default_factory=lambda: ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"])
    macro_symbol: str = "CL=F"
    leveraged_symbols: List[str] = field(default_factory=lambda: ["UCO", "SCO"])

    # Strategy mode: 'trend_dynamic' (recommended), 'leveraged_crude', 'long_short'
    mode: str = "trend_dynamic"

    # Backtest parameters
    start_date: str = "2020-09-26"
    end_date: Optional[str] = None
    initial_capital: float = 100_000.0
    commission_per_share: float = 0.005
    slippage_pct: float = 0.0005

    # Technical parameters
    ema_fast: int = 12
    ema_slow: int = 26
    macd_signal_period: int = 9
    rsi_period: int = 14
    rsi_lower_threshold: float = 45.0
    rsi_upper_threshold: float = 75.0
    atr_period: int = 14

    # Risk Management & Dynamic Sizing
    risk_per_trade_pct: float = 0.03
    max_portfolio_allocation_per_stock: float = 0.25
    high_conviction_total_exposure: float = 0.85
    atr_stop_multiplier: float = 2.5
    atr_profit_multiplier: Optional[float] = None
    trailing_stop: bool = True
    enable_macro_catalyst: bool = True

    # Real-Time Daemon & Push Notifications
    scan_interval_minutes: int = 15
    # Option 1: ntfy.sh (Zero signup, instant private phone push)
    ntfy_topic: str = field(default_factory=lambda: os.getenv("NTFY_TOPIC", ""))
    # Option 2: Telegram Bot (Private personal bot)
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    # Option 3: WhatsApp
    whatsapp_phone: str = field(default_factory=lambda: os.getenv("WHATSAPP_PHONE", ""))
    callmebot_api_key: str = field(default_factory=lambda: os.getenv("CALLMEBOT_API_KEY", ""))
    twilio_account_sid: str = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", ""))
