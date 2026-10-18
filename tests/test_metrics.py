import math

import pandas as pd
import pytest

from financial_dashboard.metrics import (
    annualized_volatility,
    cumulative_returns,
    daily_returns,
    maximum_drawdown,
    summarize_prices,
)
from financial_dashboard.portfolio import portfolio_growth, portfolio_returns


def test_daily_and_cumulative_returns():
    prices = pd.Series([100, 110, 99], index=pd.date_range("2024-01-01", periods=3))
    assert daily_returns(prices).tolist() == pytest.approx([0.1, -0.1])
    assert cumulative_returns(prices).tolist() == pytest.approx([0, 0.1, -0.01])


def test_volatility_and_drawdown():
    prices = pd.Series([100, 120, 90, 110])
    assert annualized_volatility(prices) > 0
    assert maximum_drawdown(prices) == pytest.approx(-0.25)
    assert math.isnan(annualized_volatility(pd.Series([100, 101])))


def test_summary_handles_empty_series():
    assert math.isnan(summarize_prices(pd.Series(dtype=float))["latest_price"])
    assert math.isnan(maximum_drawdown(pd.Series(dtype=float)))


def test_equal_weight_portfolio_growth():
    dates = pd.date_range("2024-01-01", periods=3)
    assets = {"A": pd.Series([100, 110, 110], index=dates),
              "B": pd.Series([100, 100, 110], index=dates)}
    result = portfolio_returns(assets)
    assert result.tolist() == pytest.approx([0.05, 0.05])
    assert portfolio_growth(result, 100).iloc[-1] == pytest.approx(110.25)
