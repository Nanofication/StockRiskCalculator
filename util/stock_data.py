import os
from datetime import datetime
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
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


def build_bars_request(symbol: str, timeframe: TimeFrame, start_dt: datetime, end_dt: datetime) -> StockBarsRequest:
    """Constructs the configuration payload for the data request."""
    return StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=timeframe,
        start=start_dt,
        end=end_dt,
        adjustment='raw',
        feed='sip',
        limit=10000
    )


def format_bars_dataframe(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Cleans multi-indexes, standardizes timezones, and drops unnecessary metadata."""
    if df.empty:
        return pd.DataFrame()

    # Flatten multi-index layout if symbol querying creates one
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level=0)

    # Standardize timeframes to explicit UTC
    df.index = df.index.tz_convert('UTC') if df.index.tz else df.index.tz_localize('UTC')

    # Return strictly the requested OHLCV dataset
    return df[['open', 'high', 'low', 'close', 'volume']]


# =====================================================================
# 2. THE CORE CONDUCTOR
# =====================================================================

def fetch_bars(symbol: str, timeframe: TimeFrame, start: str, end: str) -> pd.DataFrame:
    """Orchestrates individual atomic blocks to deliver standard OHLCV data."""
    client = get_data_client()
    start_dt = parse_date(start)
    end_dt = parse_date(end)

    request_params = build_bars_request(symbol, timeframe, start_dt, end_dt)
    raw_response = client.get_stock_bars(request_params)

    return format_bars_dataframe(raw_response.df, symbol)


# =====================================================================
# 3. HIGH-LEVEL TIMEFRAME PRESETS
# =====================================================================

def fetch_5min_bars(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetches granular 5-minute interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame(5, TimeFrameUnit.Minute), start, end)


def fetch_10min_bars(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetches granular 10-minute interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame(10, TimeFrameUnit.Minute), start, end)


def fetch_hourly_bars(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetches 1-hour interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame.Hour, start, end)


def fetch_daily_bars(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetches standard 1-day interval OHLCV data."""
    return fetch_bars(symbol, TimeFrame.Day, start, end)


# =====================================================================
# EXAMPLE USAGE
# =====================================================================
if __name__ == '__main__':
    # Quick sanity test run
    TICKER = "AAPL"
    START_DATE = "2026-06-01"
    END_DATE = "2026-06-15"

    print(f"--- Testing 5 Minute Fetch for {TICKER} ---")
    df_5min = fetch_5min_bars(TICKER, START_DATE, END_DATE)
    print(df_5min.head())

    print(f"\n--- Testing Daily Fetch for {TICKER} ---")
    df_daily = fetch_daily_bars(TICKER, START_DATE, END_DATE)
    print(df_daily.head())