"""Yahoo Finance data access, isolated behind a small, testable interface."""

from __future__ import annotations

import os
import time

import pandas as pd

REQUEST_TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 0.5


def _is_transient_connection_error(error: Exception) -> bool:
    """Identify network failures that may succeed on a brief retry."""
    message = str(error).lower()
    markers = (
        "proxy", "curl: (5)", "curl: (6)", "curl: (7)", "curl: (28)",
        "timed out", "timeout", "connectionerror", "failed to connect",
        "connection reset", "temporary failure",
    )
    return any(marker in message for marker in markers)


def _safe_connection_message(ticker: str, error: Exception) -> str:
    """Return actionable network guidance without echoing URLs or credentials."""
    message = str(error).lower()
    proxy_configured = any(os.getenv(name) for name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"))
    if "proxy" in message or (proxy_configured and "curl: (7)" in message):
        reason = (
            "Yahoo Finance could not be reached through the configured proxy. Check "
            "that your HTTP_PROXY/HTTPS_PROXY settings use an available, authorized "
            "proxy that permits Yahoo Finance"
        )
    elif any(marker in message for marker in ("timed out", "timeout", "curl: (28)")):
        reason = "the Yahoo Finance request timed out. Check your internet or proxy connection"
    else:
        reason = "a network connection to Yahoo Finance could not be established. Check your internet or proxy connection"
    return f"Could not retrieve {ticker}: {reason}, then try again."


def fetch_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch adjusted daily OHLCV history; raise readable errors for bad symbols."""
    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("Enter a ticker symbol, such as AAPL or MSFT.")
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is not installed. Install project requirements first.") from exc
    ticker_data = yf.Ticker(symbol)
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            data = ticker_data.history(
                period=period,
                auto_adjust=True,
                actions=False,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            break
        except Exception as exc:
            last_error = exc
            if not _is_transient_connection_error(exc) or attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(_safe_connection_message(symbol, exc)) from None
            time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
    else:  # Defensive fallback; normal paths either break or raise above.
        raise RuntimeError(_safe_connection_message(symbol, last_error or RuntimeError())) from None

    if data is None or data.empty or "Close" not in data:
        raise ValueError(f"No historical data was found for {symbol}. Check the ticker and try again.")
    data = data.copy()
    data.index = pd.to_datetime(data.index)
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
    data = data.dropna(subset=["Close"])
    if data.empty:
        raise ValueError(f"{symbol} returned no usable closing prices.")
    return data
