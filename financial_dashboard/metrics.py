"""Transparent return and risk calculations built on pandas and NumPy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def daily_returns(prices: pd.Series) -> pd.Series:
    """Compute simple daily returns, dropping the first undefined observation."""
    clean = pd.to_numeric(prices, errors="coerce").dropna()
    return clean.pct_change().dropna().rename("Daily return")


def cumulative_returns(prices: pd.Series) -> pd.Series:
    """Return a wealth index normalized to 1 at the first available price."""
    clean = pd.to_numeric(prices, errors="coerce").dropna()
    if clean.empty or clean.iloc[0] == 0:
        return pd.Series(dtype=float, index=clean.index, name="Cumulative return")
    return (clean / clean.iloc[0] - 1).rename("Cumulative return")


def annualized_volatility(prices: pd.Series, periods_per_year: int = 252) -> float:
    """Annualize the standard deviation of daily simple returns."""
    returns = daily_returns(prices)
    if len(returns) < 2:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def maximum_drawdown(prices: pd.Series) -> float:
    """Return the most negative peak-to-trough decline (e.g. -0.25 means -25%)."""
    clean = pd.to_numeric(prices, errors="coerce").dropna()
    if clean.empty:
        return float("nan")
    running_peak = clean.cummax()
    drawdowns = clean / running_peak - 1
    return float(drawdowns.min())


def summarize_prices(prices: pd.Series) -> dict[str, float]:
    """Build a compact set of descriptive, historical metrics."""
    clean = pd.to_numeric(prices, errors="coerce").dropna()
    if clean.empty:
        return {"latest_price": float("nan"), "period_return": float("nan"),
                "annualized_volatility": float("nan"), "maximum_drawdown": float("nan")}
    period_return = float(clean.iloc[-1] / clean.iloc[0] - 1) if clean.iloc[0] else float("nan")
    return {
        "latest_price": float(clean.iloc[-1]),
        "period_return": period_return,
        "annualized_volatility": annualized_volatility(clean),
        "maximum_drawdown": maximum_drawdown(clean),
    }
