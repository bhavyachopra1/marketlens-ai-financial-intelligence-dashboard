"""Equal-weight portfolio calculations using aligned daily returns."""

from __future__ import annotations

import pandas as pd


def portfolio_returns(price_data: dict[str, pd.Series], weights: dict[str, float] | None = None) -> pd.Series:
    """Combine asset returns using normalized non-negative target weights."""
    valid = {name: series.dropna() for name, series in price_data.items() if series is not None and not series.dropna().empty}
    if not valid:
        return pd.Series(dtype=float, name="Portfolio return")
    returns = pd.concat({name: series.pct_change() for name, series in valid.items()}, axis=1).dropna(how="any")
    if returns.empty:
        return pd.Series(dtype=float, name="Portfolio return")
    if weights is None:
        normalized = pd.Series(1 / len(valid), index=list(valid))
    else:
        normalized = pd.Series({name: float(weights.get(name, 0)) for name in valid})
        if (normalized < 0).any() or normalized.sum() <= 0:
            raise ValueError("Portfolio weights must be non-negative and have a positive total.")
        normalized /= normalized.sum()
    result = returns.mul(normalized, axis=1).sum(axis=1)
    result.name = "Portfolio return"
    return result


def portfolio_growth(returns: pd.Series, initial_value: float = 10_000) -> pd.Series:
    """Convert periodic portfolio returns to a dollar-value growth series."""
    if initial_value <= 0:
        raise ValueError("Initial portfolio value must be greater than zero.")
    growth = initial_value * (1 + returns.fillna(0)).cumprod()
    growth.name = "Portfolio value"
    return growth
