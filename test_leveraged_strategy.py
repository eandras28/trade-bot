"""Test script for Long/Short Leveraged Strategy (UCO/SCO) with dynamic sizing."""
import pandas as pd
import numpy as np
import yfinance as yf
from indicators import compute_ema, compute_macd, compute_rsi, compute_atr

# Load data
cl = yf.Ticker("CL=F").history(start="2020-09-26", auto_adjust=True)
uco = yf.Ticker("UCO").history(start="2020-09-26", auto_adjust=True)
sco = yf.Ticker("SCO").history(start="2020-09-26", auto_adjust=True)

for df in [cl, uco, sco]:
    df.index = pd.to_datetime(df.index).tz_localize(None)

common_idx = sorted(list(set(cl.index).intersection(set(uco.index)).intersection(set(sco.index))))

cl = cl.reindex(common_idx)
uco = uco.reindex(common_idx)
sco = sco.reindex(common_idx)

# Indicators on Crude & Instruments
cl_ema12 = compute_ema(cl["Close"], 12)
cl_ema26 = compute_ema(cl["Close"], 26)
cl_macd, cl_sig, _ = compute_macd(cl["Close"], 12, 26, 9)

uco_ema12 = compute_ema(uco["Close"], 12)
uco_ema26 = compute_ema(uco["Close"], 26)
uco_atr = compute_atr(uco, 14)

sco_ema12 = compute_ema(sco["Close"], 12)
sco_ema26 = compute_ema(sco["Close"], 26)
sco_atr = compute_atr(sco, 14)

cash = 100000.0
position = None
equity_curve = []
trades = []

for date in common_idx:
    u_close = uco.loc[date, "Close"]
    s_close = sco.loc[date, "Close"]
    u_low = uco.loc[date, "Low"]
    s_low = sco.loc[date, "Low"]
    u_high = uco.loc[date, "High"]
    s_high = sco.loc[date, "High"]

    # Multi-factor conviction: alignment of Crude Futures trend + ETF momentum
    bullish_regime = (cl_ema12.loc[date] > cl_ema26.loc[date]) and (uco_ema12.loc[date] > uco_ema26.loc[date]) and (cl_macd.loc[date] > cl_sig.loc[date])
    bearish_regime = (cl_ema12.loc[date] < cl_ema26.loc[date]) and (sco_ema12.loc[date] > sco_ema26.loc[date]) and (cl_macd.loc[date] < cl_sig.loc[date])

    # Check exit on existing position
    if position is not None:
        sym, shares, entry_p, stop_p, high_p, entry_date = position
        cur_p = u_close if sym == "UCO" else s_close
        low_p = u_low if sym == "UCO" else s_low
        high_now = u_high if sym == "UCO" else s_high
        cur_atr = uco_atr.loc[date] if sym == "UCO" else sco_atr.loc[date]

        # Stop loss check
        if low_p <= stop_p:
            exit_p = min(cur_p, stop_p) * 0.9995
            pnl = (exit_p - entry_p) * shares - (2 * shares * 0.005)
            cash += shares * exit_p - (shares * 0.005)
            trades.append({"symbol": sym, "pnl": pnl, "entry": entry_date, "exit": date, "reason": "Stop Loss"})
            position = None
        # Regime flip check
        elif (sym == "UCO" and not (cl_ema12.loc[date] > cl_ema26.loc[date])) or (sym == "SCO" and not (cl_ema12.loc[date] < cl_ema26.loc[date])):
            exit_p = cur_p * 0.9995
            pnl = (exit_p - entry_p) * shares - (2 * shares * 0.005)
            cash += shares * exit_p - (shares * 0.005)
            trades.append({"symbol": sym, "pnl": pnl, "entry": entry_date, "exit": date, "reason": "Regime Exit"})
            position = None
        else:
            # Trailing stop update (protect profits after 1.5 ATR move)
            if high_now > high_p:
                high_p = high_now
                new_stop = high_now - (2.5 * cur_atr)
                if new_stop > stop_p:
                    stop_p = new_stop
                position = (sym, shares, entry_p, stop_p, high_p, entry_date)

    # Enter new position with regime-adaptive sizing
    total_eq = cash + (position[1] * (u_close if position[0] == "UCO" else s_close) if position else 0)
    if position is None:
        if bullish_regime and not np.isnan(uco_atr.loc[date]):
            # High conviction regime: allocate 70% of equity
            target_alloc = total_eq * 0.70
            shares = int(target_alloc / (u_close * 1.0005))
            if shares > 0 and cash >= shares * u_close * 1.0005:
                cost = shares * u_close * 1.0005 + (shares * 0.005)
                cash -= cost
                stop = u_close - (2.5 * uco_atr.loc[date])
                position = ("UCO", shares, u_close, stop, u_close, date)
        elif bearish_regime and not np.isnan(sco_atr.loc[date]):
            # Bearish regime: rotate into SCO (2x Short) with 70% allocation
            target_alloc = total_eq * 0.70
            shares = int(target_alloc / (s_close * 1.0005))
            if shares > 0 and cash >= shares * s_close * 1.0005:
                cost = shares * s_close * 1.0005 + (shares * 0.005)
                cash -= cost
                stop = s_close - (2.5 * sco_atr.loc[date])
                position = ("SCO", shares, s_close, stop, s_close, date)

    daily_eq = cash + (position[1] * (u_close if position[0] == "UCO" else s_close) if position else 0)
    equity_curve.append({"date": date, "equity": daily_eq})

eq_df = pd.DataFrame(equity_curve).set_index("date")
final_equity = eq_df["equity"].iloc[-1]
tot_return = (final_equity - 100000.0) / 100000.0 * 100

wins = [t for t in trades if t["pnl"] > 0]
win_rate = len(wins) / len(trades) * 100 if trades else 0

gross_profit = sum(t["pnl"] for t in wins)
gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] <= 0))
profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

cummax = eq_df["equity"].cummax()
dd = (eq_df["equity"] - cummax) / cummax * 100
max_dd = dd.min()

print(f"=== 6-YEAR LONG/SHORT LEVERAGED (UCO/SCO) RESULTS ===")
print(f"Initial Capital: $100,000.00")
print(f"Ending Equity:   ${final_equity:,.2f}")
print(f"Total Return:    {tot_return:.2f}%")
print(f"Max Drawdown:    {max_dd:.2f}%")
print(f"Total Trades:    {len(trades)}")
print(f"Win Rate:        {win_rate:.2f}%")
print(f"Profit Factor:   {profit_factor:.2f}")
