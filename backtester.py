"""Advanced Multi-Strategy Backtesting Engine with Dynamic Sizing and Trailing Stops."""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from config import BotConfig
from data import MarketDataLoader
from strategy import MultiStrategyEngine
from portfolio import Portfolio, TradeRecord, Position


class BacktestEngine:
    def __init__(self, config: BotConfig):
        self.config = config
        self.data_loader = MarketDataLoader()
        self.strategy_engine = MultiStrategyEngine(config)

    def run(self) -> Tuple[pd.DataFrame, List[TradeRecord], Dict[str, float]]:
        """Run backtest over the selected strategy mode and symbols."""
        active_symbols = list(self.config.symbols)
        if self.config.mode == "leveraged_crude":
            active_symbols = list(self.config.leveraged_symbols)

        all_fetch = list(set(active_symbols + [self.config.macro_symbol]))
        raw_data = self.data_loader.fetch_all(
            all_fetch,
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )

        processed = self.strategy_engine.prepare_data(raw_data)

        # Align all dates across symbols
        common_dates = sorted(list(set.intersection(*[set(processed[s].index) for s in active_symbols if s in processed])))

        portfolio = Portfolio(
            initial_capital=self.config.initial_capital,
            commission_per_share=self.config.commission_per_share,
            slippage_pct=self.config.slippage_pct,
            risk_per_trade_pct=self.config.risk_per_trade_pct,
            max_allocation_per_stock=self.config.max_portfolio_allocation_per_stock,
            atr_stop_multiplier=self.config.atr_stop_multiplier,
            atr_profit_multiplier=self.config.atr_profit_multiplier or 999.0,
            trailing_stop=self.config.trailing_stop
        )

        equity_curve = []

        for date in common_dates:
            current_prices = {s: processed[s].loc[date, 'Close'] for s in active_symbols}

            # 1. Check Exits on Open Positions
            for symbol in list(portfolio.positions.keys()):
                bar = processed[symbol].loc[date]
                pos = portfolio.positions[symbol]

                # Stop loss check
                if bar['Low'] <= pos.stop_loss:
                    exit_price = min(bar['Close'], pos.stop_loss)
                    portfolio.close_position(symbol, date, exit_price, reason="Stop Loss")
                    continue

                # Take profit check (if enabled)
                if self.config.atr_profit_multiplier and pos.take_profit and bar['High'] >= pos.take_profit:
                    exit_price = max(bar['Close'], pos.take_profit)
                    portfolio.close_position(symbol, date, exit_price, reason="Take Profit")
                    continue

                # Technical exit signal
                if bar['signal'] == -1:
                    portfolio.close_position(symbol, date, bar['Close'], reason="Trend Reversal Exit")
                    continue

                # Trailing stop update
                if self.config.trailing_stop:
                    portfolio.update_trailing_stops(symbol, bar['High'], bar['atr'])

            # 2. Entries with Dynamic Position Sizing
            current_equity = portfolio.total_equity(current_prices)

            for symbol in active_symbols:
                if symbol in portfolio.positions:
                    continue

                bar = processed[symbol].loc[date]
                if bar['signal'] == 1 and not np.isnan(bar['atr']):
                    # Dynamic sizing: 25% per symbol up to high conviction exposure limit
                    target_alloc = current_equity * self.config.max_portfolio_allocation_per_stock
                    shares = int(target_alloc / (bar['Close'] * (1.0 + self.config.slippage_pct)))
                    total_cost = shares * bar['Close'] * (1.0 + self.config.slippage_pct) + (shares * self.config.commission_per_share)

                    if shares > 0 and portfolio.cash >= total_cost:
                        portfolio.cash -= total_cost
                        stop_loss = bar['Close'] - (bar['atr'] * self.config.atr_stop_multiplier)
                        take_profit = (bar['Close'] + (bar['atr'] * self.config.atr_profit_multiplier)) if self.config.atr_profit_multiplier else None
                        
                        pos = Position(
                            symbol=symbol,
                            entry_date=date,
                            entry_price=bar['Close'] * (1.0 + self.config.slippage_pct),
                            shares=shares,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            highest_price=bar['Close'],
                            atr_at_entry=bar['atr']
                        )
                        portfolio.positions[symbol] = pos

            # Record daily equity
            daily_eq = portfolio.total_equity(current_prices)
            equity_curve.append({
                'date': date,
                'equity': daily_eq,
                'cash': portfolio.cash,
                'num_positions': len(portfolio.positions)
            })

        equity_df = pd.DataFrame(equity_curve).set_index('date')
        metrics = self._calculate_metrics(equity_df, portfolio.closed_trades, raw_data, active_symbols)

        return equity_df, portfolio.closed_trades, metrics

    def _calculate_metrics(
        self,
        equity_df: pd.DataFrame,
        trades: List[TradeRecord],
        raw_data: Dict[str, pd.DataFrame],
        active_symbols: List[str]
    ) -> Dict[str, float]:
        if equity_df.empty:
            return {}

        eq = equity_df['equity']
        initial = eq.iloc[0]
        final = eq.iloc[-1]
        total_return = (final - initial) / initial

        daily_returns = eq.pct_change().dropna()
        n_days = len(daily_returns)
        years = max(n_days / 252.0, 0.1)
        cagr = ((final / initial) ** (1.0 / years)) - 1.0

        cum_max = eq.cummax()
        drawdowns = (eq - cum_max) / cum_max
        max_drawdown = drawdowns.min()

        rf_daily = (1.04 ** (1 / 252.0)) - 1.0
        excess_returns = daily_returns - rf_daily
        volatility = daily_returns.std() * np.sqrt(252)
        sharpe = (excess_returns.mean() * 252) / (volatility + 1e-10)

        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino = (excess_returns.mean() * 252) / (downside_std + 1e-10)

        total_trades = len(trades)
        if total_trades > 0:
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl <= 0]
            win_rate = len(winning_trades) / total_trades
            gross_profits = sum(t.pnl for t in winning_trades)
            gross_losses = abs(sum(t.pnl for t in losing_trades))
            profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else np.nan
            avg_pnl = sum(t.pnl for t in trades) / total_trades
            avg_win = (sum(t.pnl for t in winning_trades) / len(winning_trades)) if winning_trades else 0.0
            avg_loss = (sum(t.pnl for t in losing_trades) / len(losing_trades)) if losing_trades else 0.0
        else:
            win_rate, profit_factor, avg_pnl, avg_win, avg_loss = 0.0, 0.0, 0.0, 0.0, 0.0

        # Benchmark: XLE Buy & Hold
        xle_return = 0.0
        if 'XLE' in raw_data and not raw_data['XLE'].empty:
            xle_close = raw_data['XLE']['Close']
            xle_return = (xle_close.iloc[-1] - xle_close.iloc[0]) / xle_close.iloc[0]

        return {
            "Strategy Mode": self.config.mode,
            "Initial Capital ($)": self.config.initial_capital,
            "Ending Equity ($)": round(final, 2),
            "Total Return (%)": round(total_return * 100, 2),
            "CAGR (%)": round(cagr * 100, 2),
            "Benchmark XLE Buy&Hold (%)": round(xle_return * 100, 2),
            "Max Drawdown (%)": round(max_drawdown * 100, 2),
            "Annualized Volatility (%)": round(volatility * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Sortino Ratio": round(sortino, 2),
            "Total Trades": total_trades,
            "Win Rate (%)": round(win_rate * 100, 2),
            "Profit Factor": round(profit_factor, 2) if not np.isnan(profit_factor) else 0.0,
            "Avg Trade PnL ($)": round(avg_pnl, 2),
            "Avg Win ($)": round(avg_win, 2),
            "Avg Loss ($)": round(avg_loss, 2)
        }

    def plot_results(self, equity_df: pd.DataFrame, save_path: str = "backtest_results.png"):
        if equity_df.empty:
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

        ax1.plot(equity_df.index, equity_df['equity'], label=f'Portfolio Equity ({self.config.mode})', color='#00b4d8', linewidth=2)
        ax1.set_ylabel('Equity ($)', fontsize=12)
        ax1.set_title(f'Oil Trading Bot ({self.config.mode}): Equity Curve & Drawdown', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')

        cum_max = equity_df['equity'].cummax()
        dd = (equity_df['equity'] - cum_max) / cum_max * 100
        ax2.fill_between(equity_df.index, dd, 0, color='#e63946', alpha=0.4, label='Drawdown (%)')
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='lower left')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
