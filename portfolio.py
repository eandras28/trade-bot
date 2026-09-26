"""Simulated Portfolio & Position Management for Trading Bot."""
from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd


@dataclass
class Position:
    symbol: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    stop_loss: float
    take_profit: Optional[float]
    highest_price: float
    atr_at_entry: float


@dataclass
class TradeRecord:
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: int
    pnl: float
    pnl_pct: float
    exit_reason: str
    commission_paid: float


class Portfolio:
    def __init__(
        self,
        initial_capital: float,
        commission_per_share: float = 0.005,
        slippage_pct: float = 0.0005,
        risk_per_trade_pct: float = 0.02,
        max_allocation_per_stock: float = 0.35,
        atr_stop_multiplier: float = 2.0,
        atr_profit_multiplier: float = 4.0,
        trailing_stop: bool = True
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_per_share = commission_per_share
        self.slippage_pct = slippage_pct
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_allocation_per_stock = max_allocation_per_stock
        self.atr_stop_multiplier = atr_stop_multiplier
        self.atr_profit_multiplier = atr_profit_multiplier
        self.trailing_stop = trailing_stop

        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[TradeRecord] = []
        self.history: List[dict] = []

    def total_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total liquidation value of the portfolio."""
        positions_value = sum(
            pos.shares * current_prices.get(symbol, pos.entry_price)
            for symbol, pos in self.positions.items()
        )
        return self.cash + positions_value

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        atr: float,
        current_equity: float
    ) -> int:
        """Calculate volatility-adjusted position size based on risk and maximum allocation."""
        if atr <= 0 or price <= 0:
            return 0

        # Risk budget in dollars
        risk_dollars = current_equity * self.risk_per_trade_pct
        stop_distance = atr * self.atr_stop_multiplier
        if stop_distance <= 0:
            return 0

        # Sizing based on risk
        shares_by_risk = int(risk_dollars / stop_distance)

        # Cap by maximum portfolio allocation per stock
        max_capital = current_equity * self.max_allocation_per_stock
        shares_by_allocation = int(max_capital / price)

        # Cap by available cash
        shares_by_cash = int(self.cash / (price * (1.0 + self.slippage_pct)))

        shares = min(shares_by_risk, shares_by_allocation, shares_by_cash)
        return max(0, shares)

    def open_position(
        self,
        symbol: str,
        date: pd.Timestamp,
        price: float,
        atr: float,
        current_equity: float
    ) -> Optional[Position]:
        """Open a new long position."""
        if symbol in self.positions:
            return None

        shares = self.calculate_position_size(symbol, price, atr, current_equity)
        if shares <= 0:
            return None

        # Apply slippage to entry price
        executed_price = price * (1.0 + self.slippage_pct)
        total_cost = shares * executed_price
        commission = shares * self.commission_per_share

        if total_cost + commission > self.cash:
            return None

        self.cash -= (total_cost + commission)

        stop_loss = executed_price - (atr * self.atr_stop_multiplier)
        take_profit = executed_price + (atr * self.atr_profit_multiplier)

        pos = Position(
            symbol=symbol,
            entry_date=date,
            entry_price=executed_price,
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            highest_price=executed_price,
            atr_at_entry=atr
        )
        self.positions[symbol] = pos
        return pos

    def close_position(
        self,
        symbol: str,
        date: pd.Timestamp,
        price: float,
        reason: str
    ) -> Optional[TradeRecord]:
        """Close an existing position."""
        if symbol not in self.positions:
            return None

        pos = self.positions.pop(symbol)
        # Apply slippage on exit
        executed_price = price * (1.0 - self.slippage_pct)
        proceeds = pos.shares * executed_price
        commission = pos.shares * self.commission_per_share

        self.cash += (proceeds - commission)

        pnl = (executed_price - pos.entry_price) * pos.shares - (2 * commission)
        pnl_pct = (executed_price - pos.entry_price) / pos.entry_price

        record = TradeRecord(
            symbol=symbol,
            entry_date=pos.entry_date,
            exit_date=date,
            entry_price=pos.entry_price,
            exit_price=executed_price,
            shares=pos.shares,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
            commission_paid=2 * commission
        )
        self.closed_trades.append(record)
        return record

    def update_trailing_stops(self, symbol: str, high_price: float, current_atr: float):
        """Raise stop loss if price made new high."""
        if symbol not in self.positions or not self.trailing_stop:
            return

        pos = self.positions[symbol]
        if high_price > pos.highest_price:
            pos.highest_price = high_price
            new_stop = high_price - (current_atr * self.atr_stop_multiplier)
            if new_stop > pos.stop_loss:
                pos.stop_loss = new_stop
