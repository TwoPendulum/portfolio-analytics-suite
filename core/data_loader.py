import hashlib
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
import yfinance as yf


class DataLoadError(Exception):
    pass


def load_asset_config(config_path: Optional[str] = None) -> List[Dict]:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "assets.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("assets", [])
    except FileNotFoundError:
        return [
            {"ticker": "QQQ", "name": "纳斯达克100ETF", "group": "US Equity"},
            {"ticker": "SPY", "name": "标普500ETF", "group": "US Equity"},
            {"ticker": "IWM", "name": "罗素2000ETF", "group": "US Equity"},
            {"ticker": "COWZ", "name": "现金流ETF", "group": "US Equity"},
            {"ticker": "GLD", "name": "黄金ETF", "group": "Commodity"},
            {"ticker": "STIP", "name": "短期TIPS ETF", "group": "Fixed Income"},
            {"ticker": "TLT", "name": "20年期美债ETF", "group": "Fixed Income"},
            {"ticker": "SHY", "name": "短期美债ETF", "group": "Fixed Income"},
            {"ticker": "BTC-USD", "name": "比特币", "group": "Crypto"},
            {"ticker": "ETH-USD", "name": "以太坊", "group": "Crypto"},
        ]


def fetch_data(
    tickers: List[str],
    start_date: str,
    end_date: str,
    ttl_seconds: int = 3600,
) -> Tuple[pd.DataFrame, List[str]]:
    """Fetch adjusted close prices from yfinance, compute log returns, cache to parquet."""
    key_str = "_".join(sorted(tickers)) + start_date + end_date
    cache_key = hashlib.md5(key_str.encode()).hexdigest()
    cache_path = Path(tempfile.gettempdir()) / f"portfolio_cache_{cache_key}.parquet"
    warnings: List[str] = []

    # Try cache
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < ttl_seconds:
            returns = pd.read_parquet(cache_path)
            available = [t for t in tickers if t in returns.columns]
            if len(available) >= 2:
                return returns[available], warnings
            else:
                cache_path.unlink(missing_ok=True)

    # Download
    try:
        raw = yf.download(
            tickers, start=start_date, end=end_date, auto_adjust=True,
            group_by="ticker", threads=True, progress=False,
        )
    except Exception:
        time.sleep(2)
        try:
            raw = yf.download(
                tickers, start=start_date, end=end_date, auto_adjust=True,
                group_by="ticker", threads=True, progress=False,
            )
        except Exception as e:
            raise DataLoadError(f"Failed to fetch data: {e}")

    if raw.empty:
        raise DataLoadError("No data returned from yfinance for the given tickers/date range.")

    # Handle multi-level vs single-level columns
    if isinstance(raw.columns, pd.MultiIndex):
        close_prices = pd.DataFrame()
        for t in tickers:
            if t in raw.columns.get_level_values(0):
                close_prices[t] = raw[(t, "Close")]
    else:
        close_prices = raw[["Close"]] if "Close" in raw.columns else raw
        if len(tickers) == 1 and "Close" not in raw.columns:
            close_prices.columns = tickers

    # Forward-fill close prices so non-trading days carry last price (return=0 naturally)
    close_prices = close_prices.ffill(limit=5)
    close_prices = close_prices.dropna(how="all")

    # Log returns (zero on non-trading days since price is carried forward)
    returns = np.log(close_prices / close_prices.shift(1)).dropna(how="all")

    # Filter to business days only (crypto trades 7d/wk and would pad weekends for all)
    returns = returns[returns.index.dayofweek < 5]

    # Drop tickers with >50% NaN before fillna
    valid_tickers = [t for t in returns.columns if returns[t].isna().mean() < 0.5]
    dropped = set(tickers) - set(valid_tickers)
    for t in dropped:
        warnings.append(f"{t}: dropped (>50% missing data).")

    # Fill remaining NaN returns (genuine data gaps)
    for t in valid_tickers:
        nan_count = returns[t].isna().sum()
        if nan_count > 5:
            warnings.append(f"{t}: {nan_count} missing return values.")
        returns[t] = returns[t].fillna(0.0)

    returns = returns[valid_tickers].dropna()

    # Date alignment: check if actual range shorter than requested
    if len(returns) > 0:
        actual_start = returns.index[0].strftime("%Y-%m-%d")
        actual_end = returns.index[-1].strftime("%Y-%m-%d")
        if actual_start > start_date or actual_end < end_date:
            last_ticker_start = returns.index[0]
            warnings.append(
                f"Data range shortened to [{actual_start}, {actual_end}]. "
                f"Earliest available: {last_ticker_start.strftime('%Y-%m-%d')}."
            )

    # Cache
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    returns.to_parquet(cache_path)

    return returns, warnings
