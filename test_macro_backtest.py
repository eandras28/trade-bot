import pandas as pd
import numpy as np
import yfinance as yf
from config import BotConfig
from indicators import compute_ema, compute_macd, compute_rsi, compute_atr, compute_sma
from portfolio import Portfolio

# Download data
symbols = ["XLE", "USO", "XOM", "CVX"]
start = "2020-09-26"
data = {}
for s in symbols + ["CL=F"]:
    df = yf.Ticker(s).history(start=start, auto_adjust=True)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    data[s] = df

# Compute CL=F macro catalyst
cl = data["CL=F"]
cl["ema_fast"] = compute_ema(cl["Close"], 12)
cl["ema_slow"] = compute_ema(cl["Close"], 26)
cl["macro_bullish"] = cl["ema_fast"] > cl["ema_slow"]

# Compute signals for each symbol
for s in symbols:
    df = data[s]
    df["ema_fast"] = compute_ema(df["Close"], 12)
    df["ema_slow"] = compute_ema(df["Close"], 26)
    macd, sig, hist = compute_macd(df["Close"], 12, 26, 9)
    df["macd"] = macd
    df["macd_sig"] = sig
    df["macd_hist"] = hist
    df["rsi"] = compute_rsi(df["Close"], 14)
    df["atr"] = compute_atr(df, 14)

    # Join macro catalyst
    df["macro_bullish"] = cl["macro_bullish"].reindex(df.index).ffill()

    # Buy only when both stock and macro crude catalyst are aligned
    buy = (df["ema_fast"] > df["ema_slow"]) & (df["macd"] > df["macd_sig"]) & (df["rsi"] >= 45) & (df["rsi"] <= 75) & (df["macro_bullish"] == True)
    exit_cond = (df["ema_fast"] < df["ema_slow"]) | (df["macd"] < df["macd_sig"]) | (df["macro_bullish"] == False)

    df["signal"] = 0
    df.loc[buy, "signal"] = 1
    df.loc[exit_cond, "signal"] = -1

# Simulate portfolio
portfolio = Portfolio(initial_capital=100000.0, risk_per_trade_pct=0.03, max_allocation_per_stock=0.35, atr_stop_multiplier=2.0, atr_profit_multiplier=4.0)

all_dates = sorted(list(data["XLE"].index))
equity = []

for date in all_dates:
    prices = {s: data[s].loc[date, "Close"] for s in symbols if date in data[s].index}
    # Exits
    for s in list(portfolio.positions.keys()):
        if date not in data[s].index:
            continue
        bar = data[s].loc[date]
        pos = portfolio.positions[s]
        if bar["Low"] <= pos.stop_loss:
            portfolio.close_position(s, date, min(bar["Open"], pos.stop_loss), "Stop Loss")
        elif pos.take_profit and bar["High"] >= pos.take_profit:
            portfolio.close_position(s, date, max(bar["Open"], pos.take_profit), "Take Profit")
        elif bar["signal"] == -1:
            portfolio.close_position(s, date, bar["Close"], "Macro/Tech Exit")
        else:
            portfolio.update_trailing_stops(s, bar["High"], bar["atr"])

    # Buys
    cur_eq = portfolio.total_equity(prices)
    for s in symbols:
        if s not in portfolio.positions and date in data[s].index:
            bar = data[s].loc[date]
            if bar["signal"] == 1 and not np.isnan(bar["atr"]):
                portfolio.open_position(s, date, bar["Close"], bar["atr"], cur_eq)

    equity.append(portfolio.total_equity(prices))

total_ret = (equity[-1] - 100000) / 100000
trades = portfolio.closed_trades
wins = [t for t in trades if t.pnl > 0]
win_rate = len(wins) / len(trades) if trades else 0
print(f"Ending Equity: ${equity[-1]:,.2f} ({total_ret*100:.1f}%)")
print(f"Total Trades: {len(trades)}, Win Rate: {win_rate*100:.1f}%")
