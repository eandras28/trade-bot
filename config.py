"""Configuration settings for the Oil Stock Trading Bot."""
import os
from dataclasses import dataclass, field
from typing import List, Optional


ENERGY_SYMBOLS = ["XOM", "CVX", "OXY", "COP", "BP", "SHEL"]

TECH_SYMBOLS = [
    # Power & Next-Gen Battery Tech
    "VRT",   # Vertiv Holdings (AI data center power, thermal & liquid cooling)
    "ENVX",  # Enovix Corporation (Silicon-anode high-energy density batteries)
    "QS",    # QuantumScape (Solid-state lithium metal EV & industrial batteries)
    "FLNC",  # Fluence Energy (Siemens/AES grid battery energy storage systems)
    # Actuators & Advanced Robotics
    "SYM",   # Symbotic (AI-powered warehouse robotics & robotic arm actuators)
    # Health Tech & Bio AI
    "TEM",   # Tempus AI (Precision medicine, oncology genomic AI diagnostics)
    "HIMS",  # Hims & Hers Health (Personalized telehealth platform)
    "RXRX",  # Recursion Pharmaceuticals (AI drug discovery powered by NVIDIA)
    "TMDX",  # TransMedics Group (Warm perfusion organ transplant technologies)
]

SECTOR_MAP = {
    "XOM": "Energy & Oil",
    "CVX": "Energy & Oil",
    "OXY": "Energy & Oil",
    "COP": "Energy & Oil",
    "BP": "Energy & Oil",
    "SHEL": "Energy & Oil",
    "VRT": "Power & AI Cooling",
    "ENVX": "Power & Battery Tech",
    "QS": "Solid-State Battery",
    "FLNC": "Grid Battery Storage",
    "SYM": "Actuators & Robotics",
    "TEM": "Health Tech & AI Bio",
    "HIMS": "Health Tech & Telehealth",
    "RXRX": "Health Tech & AI Pharma",
    "TMDX": "Health Tech & MedTech",
}


@dataclass
class BotConfig:
    # Dual-Universe Configuration (Revolut Hungary accessible equities)
    energy_symbols: List[str] = field(default_factory=lambda: list(ENERGY_SYMBOLS))
    tech_symbols: List[str] = field(default_factory=lambda: list(TECH_SYMBOLS))
    symbols: List[str] = field(default_factory=lambda: list(ENERGY_SYMBOLS + TECH_SYMBOLS))

    # Macro benchmarks
    macro_symbol: str = "CL=F"         # Physical WTI Crude Futures benchmark for Energy
    tech_macro_symbol: str = "QQQ"     # Invesco Nasdaq 100 benchmark for Tech
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
