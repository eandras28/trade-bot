"""Multi-Strategy Signal Generation Engine for Oil Equities, Commodities & Leveraged ETFs."""
from typing import Dict
import pandas as pd
import numpy as np

from config import BotConfig
from indicators import compute_ema, compute_macd, compute_rsi, compute_atr, compute_sma


class MultiStrategyEngine:
    def __init__(self, config: BotConfig):
        self.config = config

    def prepare_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Compute technical indicators for all assets and align macro catalyst."""
        processed = {}

        # 1. Process Macro Benchmarks (CL=F for Energy, QQQ for Tech)
        cl = None
        if self.config.macro_symbol in data:
            cl = data[self.config.macro_symbol].copy()
            cl['ema_fast'] = compute_ema(cl['Close'], self.config.ema_fast)
            cl['ema_slow'] = compute_ema(cl['Close'], self.config.ema_slow)
            macd, sig, _ = compute_macd(cl['Close'], self.config.ema_fast, self.config.ema_slow, self.config.macd_signal_period)
            cl['macd'] = macd
            cl['macd_sig'] = sig
            cl['macro_bullish'] = (cl['ema_fast'] > cl['ema_slow']) & (cl['macd'] > cl['macd_sig'])
            cl['macro_bearish'] = (cl['ema_fast'] < cl['ema_slow']) & (cl['macd'] < cl['macd_sig'])
            processed[self.config.macro_symbol] = cl

        qqq = None
        tech_macro = getattr(self.config, 'tech_macro_symbol', 'QQQ')
        if tech_macro in data:
            qqq = data[tech_macro].copy()
            qqq['ema_fast'] = compute_ema(qqq['Close'], self.config.ema_fast)
            qqq['ema_slow'] = compute_ema(qqq['Close'], self.config.ema_slow)
            macd, sig, _ = compute_macd(qqq['Close'], self.config.ema_fast, self.config.ema_slow, self.config.macd_signal_period)
            qqq['macd'] = macd
            qqq['macd_sig'] = sig
            qqq['macro_bullish'] = (qqq['ema_fast'] > qqq['ema_slow']) & (qqq['macd'] > qqq['macd_sig'])
            qqq['macro_bearish'] = (qqq['ema_fast'] < qqq['ema_slow']) & (qqq['macd'] < qqq['macd_sig'])
            processed[tech_macro] = qqq

        macro_symbols_set = {self.config.macro_symbol, tech_macro}
        tech_symbols_set = set(getattr(self.config, 'tech_symbols', []))

        # 2. Process all symbols
        for sym, df in data.items():
            if sym in macro_symbols_set:
                continue

            d = df.copy()
            d['ema_fast'] = compute_ema(d['Close'], self.config.ema_fast)
            d['ema_slow'] = compute_ema(d['Close'], self.config.ema_slow)
            macd, sig, hist = compute_macd(d['Close'], self.config.ema_fast, self.config.ema_slow, self.config.macd_signal_period)
            d['macd'] = macd
            d['macd_sig'] = sig
            d['macd_hist'] = hist
            d['rsi'] = compute_rsi(d['Close'], self.config.rsi_period)
            d['atr'] = compute_atr(d, self.config.atr_period)
            d['vol_sma20'] = compute_sma(d['Volume'], 20)

            # Route macro benchmark: QQQ for Tech, CL=F for Energy
            target_macro = qqq if (sym in tech_symbols_set and qqq is not None) else cl
            if target_macro is not None and self.config.enable_macro_catalyst:
                d['macro_bullish'] = target_macro['macro_bullish'].reindex(d.index).ffill().fillna(True)
                d['macro_bearish'] = target_macro['macro_bearish'].reindex(d.index).ffill().fillna(False)
            else:
                d['macro_bullish'] = True
                d['macro_bearish'] = False

            # Generate signals based on config.mode
            d['signal'] = 0  # 1: Long, -1: Short or Exit

            if self.config.mode == "trend_dynamic":
                # Long entry: Stock technicals + Macro Crude alignment
                long_cond = (
                    (d['ema_fast'] > d['ema_slow']) &
                    (d['macd'] > d['macd_sig']) &
                    (d['rsi'] >= self.config.rsi_lower_threshold) &
                    (d['macro_bullish'] == True)
                )
                exit_cond = (d['ema_fast'] < d['ema_slow']) | (d['macd'] < d['macd_sig'])
                d.loc[long_cond, 'signal'] = 1
                d.loc[exit_cond, 'signal'] = -1

            elif self.config.mode == "long_short":
                # Both Long and Short signals
                long_cond = (
                    (d['ema_fast'] > d['ema_slow']) &
                    (d['macd'] > d['macd_sig']) &
                    (d['rsi'] >= self.config.rsi_lower_threshold) &
                    (d['macro_bullish'] == True)
                )
                short_cond = (
                    (d['ema_fast'] < d['ema_slow']) &
                    (d['macd'] < d['macd_sig']) &
                    (d['rsi'] <= 55) &
                    (d['macro_bearish'] == True)
                )
                d.loc[long_cond, 'signal'] = 1
                d.loc[short_cond, 'signal'] = -2  # -2 represents short entry
                # Neutral / exit flips
                d.loc[(d['ema_fast'] < d['ema_slow']) & ~short_cond, 'signal'] = -1

            elif self.config.mode == "leveraged_crude":
                # Leveraged Crude UCO / SCO mode
                long_cond = (d['ema_fast'] > d['ema_slow']) & (d['macd'] > d['macd_sig']) & (d['macro_bullish'] == True)
                exit_cond = (d['ema_fast'] < d['ema_slow']) | (d['macro_bullish'] == False)
                d.loc[long_cond, 'signal'] = 1
                d.loc[exit_cond, 'signal'] = -1

            processed[sym] = d

        return processed
