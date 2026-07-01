import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# =====================================================================
# 1. CORE ATOMIC BLOCKS (Single-Responsibility Functions)
# =====================================================================

def create_chart_canvas(has_volume: bool = False) -> go.Figure:
    """Initializes a blank Plotly figure, allocating rows if volume is required."""
    if has_volume:
        # Creates a 2-row layout splitting space 80% grid / 20% volume
        return make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.8, 0.2]
        )
    return go.Figure()


def add_candlestick_trace(fig: go.Figure, df: pd.DataFrame, name: str, row: int = 1, col: int = 1) -> go.Figure:
    """Appends a standard OHLC Candlestick layer to a specific grid coordinate."""
    candlestick = go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=name
    )
    fig.add_trace(candlestick, row=row, col=col)
    return fig


def add_volume_trace(fig: go.Figure, df: pd.DataFrame, row: int = 2, col: int = 1) -> go.Figure:
    """Appends a Bar chart layer representing trading volume to a specific grid coordinate."""
    colors = ['green' if close >= open_val else 'red' for open_val, close in zip(df['open'], df['close'])]

    volume_bars = go.Bar(
        x=df.index,
        y=df['volume'],
        name='Volume',
        marker=dict(color=colors),  # Fixed: Replaced raw array assignment with standard marker dict
        opacity=0.8
    )
    fig.add_trace(volume_bars, row=row, col=col)
    return fig


def apply_custom_layout(fig: go.Figure, title: str, show_slider: bool = False,
                        template: str = 'plotly_white') -> go.Figure:
    """Applies universal styling definitions, titles, templates, and axes cleanups."""
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=show_slider,
        template=template,
        hovermode='x unified'
    )

    # Fixed: Replaced protected property check with a clean public API key inspection,
    # and corrected the target method name to update_yaxes()
    if 'yaxis2' in fig.layout:
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig


# =====================================================================
# 2. THE CORE CONDUCTORS (Assembling the blocks)
# =====================================================================

def plot_price_only(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Assembles blocks to generate a clean, standalone candlestick chart."""
    fig = create_chart_canvas(has_volume=False)
    fig = add_candlestick_trace(fig, df, name=symbol)
    fig = apply_custom_layout(fig, title=f'{symbol} - Price Chart')
    return fig


def plot_price_with_volume(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Assembles blocks to generate a professional multi-panel Price + Volume chart."""
    fig = create_chart_canvas(has_volume=True)
    fig = add_candlestick_trace(fig, df, name=symbol, row=1, col=1)
    fig = add_volume_trace(fig, df, row=2, col=1)
    fig = apply_custom_layout(fig, title=f'{symbol} - Price & Volume')
    return fig


# =====================================================================
# EXAMPLE USAGE (Interacting with your data frames)
# =====================================================================
if __name__ == '__main__':
    import numpy as np

    from stock_util import fetch_daily_bars, fetch_5min_bars

    TICKER = "NVDA"
    START_DATE = "2025-06-22"
    END_DATE = "2026-06-26"

    # Example 1: Regular market hours only + Adjusted for stock splits
    print(f"--- Fetching RTH Only & Split-Adjusted Data for {TICKER} ---")
    df_clean = fetch_daily_bars(TICKER, START_DATE, END_DATE, include_splits=True)
    # 2. Assembling lego pieces for a full layout
    print("Generating dual-panel layout...")
    chart = plot_price_with_volume(df_clean, "NVDA")

    # 3. Execution/Rendering block
    chart.show()