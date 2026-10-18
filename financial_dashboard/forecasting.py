"""A deliberately simple, explicitly experimental next-day price estimate."""

from __future__ import annotations

import numpy as np
import pandas as pd


def next_day_estimate(prices: pd.Series) -> tuple[float, float]:
    """Fit a small lagged-return linear model and return estimate and holdout MAE.

    This is a demonstration of a modelling workflow, not a trading signal.
    """
    clean = pd.to_numeric(prices, errors="coerce").dropna()
    if len(clean) < 45:
        raise ValueError("At least 45 daily prices are needed for this experiment.")
    try:
        from sklearn.linear_model import LinearRegression
    except ImportError as exc:
        raise RuntimeError("scikit-learn is not installed. Install project requirements first.") from exc
    returns = clean.pct_change().dropna().to_numpy()
    window = 5
    x = np.array([returns[i - window:i] for i in range(window, len(returns))])
    y = returns[window:]
    split = max(int(len(x) * 0.8), 1)
    if len(x) - split < 2:
        raise ValueError("There is not enough data to create a holdout evaluation.")
    model = LinearRegression().fit(x[:split], y[:split])
    mae = float(np.mean(np.abs(model.predict(x[split:]) - y[split:])))
    next_return = float(model.predict(returns[-window:].reshape(1, -1))[0])
    return float(clean.iloc[-1] * (1 + next_return)), mae
