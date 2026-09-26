"""Market data provider with local caching for oil stocks and ETFs."""
import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf


class MarketDataLoader:
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = str(Path(__file__).parent / ".cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_symbol_data(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """Fetch OHLCV data for a single ticker with disk caching."""
        cache_file = self.cache_dir / f"{symbol}_{start_date}_{end_date or 'latest'}.parquet"

        if not force_refresh and cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                return df
            except Exception:
                pass

        # Download from yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)

        if df.empty:
            raise ValueError(f"No data returned for symbol: {symbol}")

        # Ensure index is standard datetime
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

        # Save cache
        try:
            df.to_parquet(cache_file)
        except Exception:
            pass

        return df

    def fetch_all(
        self,
        symbols: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols."""
        data = {}
        for s in symbols:
            data[s] = self.fetch_symbol_data(s, start_date, end_date, force_refresh)
        return data
