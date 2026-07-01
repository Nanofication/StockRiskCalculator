import os
from datetime import datetime
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment  # <-- New Lego piece for adjustments
from config.config import ALPACA


# =====================================================================
# 1. CORE ATOMIC BLOCKS (Single-Responsibility Functions)
# =====================================================================

def get_data_client() -> StockHistoricalDataClient:
    """Initializes and returns the Alpaca historical data client connection."""
    key = ALPACA['KEY']
    secret = ALPACA['SECRET_KEY']
    return StockHistoricalDataClient(key, secret)


def parse_date(date_str: str) -> datetime:
    """Standardizes a string date into a UTC-aware datetime object."""
    return pd.to_datetime(date_str, utc=True).to_pydatetime()


def build_bars_request(
        symbol: str,
        timeframe: TimeFrame,
        start_dt: datetime,
        end_dt: datetime,
        include_splits: bool = False
) -> StockBarsRequest:
    """Constructs the configuration payload for the data request with split settings."""
    # Toggle between stock-split adjusted data or raw unadjusted data
    adjustment_type = Adjustment.SPLIT if include_splits else Adjustment.RAW

    return StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=timeframe,
        start=start_dt,
        end=end_dt,
        adjustment=adjustment_type,
        feed='sip',
        limit=10000
    )


def format_bars_dataframe(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Cleans multi-indexes, standardizes timezones, and drops unnecessary metadata."""
    if df.empty:
        return pd.DataFrame()

    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level=0)

    df.index = df.index.tz_convert('UTC') if df.index.tz else df.index.tz_localize('UTC')
    return df[['open', 'high', 'low', 'close', 'volume']]


def filter_regular_market_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Filters out pre-market and after-hours data, keeping only 09:30 to 16:00 Eastern Time."""
    if df.empty:
        return df

    # Temporarily switch to America/New_York to perfectly track ET market hours and daylight savings
    df_est = df.copy()
    df_est.index = df_est.index.tz_convert('America/New_York')

    # Isolate regular market sessions
    df_filtered = df_est.between_time('09:30', '16:00')

    # Restore original UTC structure for downstream calculations
    df_filtered.index = df_filtered.index.tz_convert('UTC')
    return df_filtered


# =====================================================================
# 2. THE CORE CONDUCTOR
# =====================================================================

def fetch_bars(
        symbol: str,
        timeframe: TimeFrame,
        start: str,
        end: str,
        include_extended: bool = True,
        include_splits: bool = False
) -> pd.DataFrame:
    """Orchestrates individual atomic blocks to deliver standard OHLCV data."""
    client = get_data_client()
    start_dt = parse_date(start)
    end_dt = parse_date(end)

    request_params = build_bars_request(symbol, timeframe, start_dt, end_dt, include_splits=include_splits)
    raw_response = client.get_stock_bars(request_params)

    df = format_bars_dataframe(raw_response.df, symbol)

    # Safely apply extended-hours stripping only to sub-daily frequencies (Minute/Hour)
    if not include_extended and timeframe.unit in [TimeFrameUnit.Minute, TimeFrameUnit.Hour]:
        df = filter_regular_market_hours(df)

    return df


# =====================================================================
# 3. HIGH-LEVEL TIMEFRAME PRESETS (Accepts **kwargs flags dynamically)
# =====================================================================

def fetch_5min_bars(symbol: str, start: str, end: str, **kwargs) -> pd.DataFrame:
    """Fetches granular 5-minute interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start, end, **kwargs)


def fetch_10min_bars(symbol: str, start: str, end: str, **kwargs) -> pd.DataFrame:
    """Fetches granular 10-minute interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame(10, TimeFrameUnit.Minute), start, end, **kwargs)


def fetch_hourly_bars(symbol: str, start: str, end: str, **kwargs) -> pd.DataFrame:
    """Fetches 1-hour interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame.Hour, start, end, **kwargs)


def fetch_daily_bars(symbol: str, start: str, end: str, **kwargs) -> pd.DataFrame:
    """Fetches standard 1-day interval OHLCV data."""
    # Note: include_extended has no visual impact on daily bars since they treat days as single units
    return fetch_bars(symbol, TimeFrame.Day, start, end, **kwargs)


# =====================================================================
# EXAMPLE USAGE
# =====================================================================
if __name__ == '__main__':
    TICKER = "NVDA"
    START_DATE = "2026-06-22"
    END_DATE = "2026-06-26"

    # Example 1: Regular market hours only + Adjusted for stock splits
    print(f"--- Fetching RTH Only & Split-Adjusted Data for {TICKER} ---")
    df_clean = fetch_5min_bars(TICKER, START_DATE, END_DATE, include_extended=False, include_splits=True)
    print(df_clean.head())

    # Example 2: Full session (Pre + Post market) + Raw Unadjusted price history
    print(f"\n--- Fetching Full Session & Raw Prices for {TICKER} ---")
    df_raw_ext = fetch_5min_bars(TICKER, START_DATE, END_DATE, include_extended=True, include_splits=False)
    print(df_raw_ext.head())