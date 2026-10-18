import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from financial_dashboard import market_data


def fake_yfinance(monkeypatch, history):
    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kwargs):
            return history(self, **kwargs)

    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=FakeTicker))


def test_fetch_history_passes_timeout_and_returns_data(monkeypatch):
    seen = {}

    def history(_ticker, **kwargs):
        seen.update(kwargs)
        return pd.DataFrame({"Close": [100, 101]}, index=pd.date_range("2024-01-01", periods=2))

    fake_yfinance(monkeypatch, history)
    result = market_data.fetch_history("aapl")

    assert result["Close"].tolist() == [100, 101]
    assert seen["timeout"] == market_data.REQUEST_TIMEOUT_SECONDS
    assert seen["auto_adjust"] is True


def test_fetch_history_retries_transient_connection_error(monkeypatch):
    calls = 0

    def history(_ticker, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("curl: (7) Failed to connect")
        return pd.DataFrame({"Close": [100]}, index=pd.date_range("2024-01-01", periods=1))

    fake_yfinance(monkeypatch, history)
    monkeypatch.setattr(market_data.time, "sleep", lambda _seconds: None)

    assert not market_data.fetch_history("AAPL").empty
    assert calls == 2


def test_fetch_history_reports_proxy_error_without_echoing_credentials(monkeypatch):
    def history(_ticker, **_kwargs):
        raise OSError("Failed through proxy http://user:secret-token@127.0.0.1:9")

    fake_yfinance(monkeypatch, history)
    monkeypatch.setattr(market_data.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError) as error:
        market_data.fetch_history("AAPL")

    assert "could not be reached through the configured proxy" in str(error.value)
    assert "secret-token" not in str(error.value)


def test_fetch_history_identifies_curl_connect_failure_with_proxy_env(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://user:secret-token@127.0.0.1:9")

    def history(_ticker, **_kwargs):
        raise OSError("curl: (7) Failed to connect")

    fake_yfinance(monkeypatch, history)
    monkeypatch.setattr(market_data.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError) as error:
        market_data.fetch_history("AAPL")

    assert "through the configured proxy" in str(error.value)
    assert "secret-token" not in str(error.value)


def test_fetch_history_rejects_empty_ticker():
    with pytest.raises(ValueError, match="Enter a ticker"):
        market_data.fetch_history("  ")
