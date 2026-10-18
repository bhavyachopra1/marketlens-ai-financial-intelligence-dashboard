"""Streamlit entry point for the AI Financial Intelligence Dashboard."""

from __future__ import annotations

import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from financial_dashboard.ai_summary import summarize
from financial_dashboard.forecasting import next_day_estimate
from financial_dashboard.market_data import fetch_history
from financial_dashboard.metrics import cumulative_returns, summarize_prices
from financial_dashboard.portfolio import portfolio_growth, portfolio_returns


st.set_page_config(page_title="MarketLens | Financial Intelligence", page_icon="📈", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
.stApp { background: #f5f7fb; color: #172033; }
[data-testid="stSidebar"] { background: #101a2d; }
[data-testid="stSidebar"] * { color: #e8eef8 !important; }
h1,h2,h3 { font-family: Manrope, sans-serif; letter-spacing: -0.035em; }
.hero { padding: 1.35rem 1.55rem; border-radius: 18px; background: linear-gradient(120deg,#12243f,#1b4562); color: white; margin-bottom: 1.1rem; }
.hero p { color: #c7d7e6; margin-bottom: 0; }
.stMetric { background: white; border: 1px solid #e8edf4; padding: 14px 16px; border-radius: 14px; box-shadow: 0 3px 14px #15274308; }
.stTabs [data-baseweb="tab-list"] { gap: 18px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=900, show_spinner=False)
def load_prices(symbol: str, period: str) -> pd.DataFrame:
    return fetch_history(symbol, period)


def show_error(error: Exception) -> None:
    st.error(str(error))


st.markdown("<div class='hero'><h1>MarketLens</h1><p>Clear, interactive context for historical market data and portfolio risk.</p></div>", unsafe_allow_html=True)
with st.sidebar:
    st.markdown("## Workspace")
    ticker = st.text_input("Primary ticker", "AAPL", help="Try a US-listed symbol such as AAPL, MSFT, or NVDA.").strip().upper()
    period_label = st.selectbox("History window", ["6 months", "1 year", "2 years", "5 years"], index=1)
    period = {"6 months": "6mo", "1 year": "1y", "2 years": "2y", "5 years": "5y"}[period_label]
    st.caption("Data source: Yahoo Finance via yfinance. Quotes may be delayed or incomplete.")

try:
    history = load_prices(ticker, period)
except Exception as exc:
    show_error(exc)
    st.info("Enter a valid ticker and try again. Data providers can also be temporarily unavailable.")
    st.stop()

prices = history["Close"].dropna()
metrics = summarize_prices(prices)

top = st.columns(4)
top[0].metric("Latest close", f"${metrics['latest_price']:,.2f}")
top[1].metric("Period return", f"{metrics['period_return']:.1%}")
top[2].metric("Annualized volatility", f"{metrics['annualized_volatility']:.1%}" if pd.notna(metrics["annualized_volatility"]) else "—")
top[3].metric("Maximum drawdown", f"{metrics['maximum_drawdown']:.1%}" if pd.notna(metrics["maximum_drawdown"]) else "—")

price_tab, compare_tab, portfolio_tab, forecast_tab = st.tabs(["Overview", "Compare", "Portfolio lab", "Forecast experiment"])
with price_tab:
    left, right = st.columns([1.6, 1])
    with left:
        st.subheader(f"{ticker} · adjusted closing price")
        fig = px.area(history, y="Close", labels={"Close": "Price (USD)", "Date": "Date"}, template="plotly_white")
        fig.update_traces(line_color="#168b85", fillcolor="rgba(22,139,133,.12)")
        fig.update_layout(height=380, margin=dict(l=10,r=10,t=20,b=10), hovermode="x unified")
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Growth of $1")
        growth = cumulative_returns(prices)
        growth_fig = px.line(growth, labels={"value": "Return", "Date": "Date"}, template="plotly_white")
        growth_fig.update_traces(line_color="#4169d8")
        growth_fig.update_layout(height=380, margin=dict(l=10,r=10,t=20,b=10), yaxis_tickformat=".0%")
        st.plotly_chart(growth_fig, width="stretch")
    st.caption("Returns and risk statistics summarize the selected historical window. Volatility is sample daily standard deviation annualized with 252 trading days.")
    if st.button("Generate AI educational summary", disabled=not os.getenv("OPENAI_API_KEY")):
        with st.spinner("Preparing a short metrics summary…"):
            try:
                summary = summarize(ticker, metrics)
                st.info(summary or "Set OPENAI_API_KEY to enable this optional feature.")
            except Exception as exc:
                show_error(exc)
    if not os.getenv("OPENAI_API_KEY"):
        st.caption("Optional AI summary is hidden until OPENAI_API_KEY is configured. The rest of the dashboard works without an API key.")

with compare_tab:
    st.subheader("Compare normalized performance")
    symbols_text = st.text_input("Tickers (comma separated)", f"{ticker}, SPY")
    symbols = list(dict.fromkeys(s.strip().upper() for s in symbols_text.split(",") if s.strip()))
    series_map = {}
    failures = []
    for symbol in symbols[:8]:
        try:
            series_map[symbol] = load_prices(symbol, period)["Close"]
        except Exception as exc:
            failures.append(f"{symbol}: {exc}")
    for failure in failures:
        st.warning(failure)
    if series_map:
        normalized = pd.concat({s: cumulative_returns(p) for s, p in series_map.items()}, axis=1)
        compare_fig = px.line(normalized, template="plotly_white", labels={"value": "Return", "Date": "Date", "variable": "Ticker"})
        compare_fig.update_layout(height=450, hovermode="x unified", yaxis_tickformat=".0%")
        st.plotly_chart(compare_fig, width="stretch")
        st.caption("Each line starts at zero on its first available observation; benchmark defaults to SPY. Historical comparison is not a forecast.")
    else:
        st.info("Add at least one valid ticker to compare.")

with portfolio_tab:
    st.subheader("Build a weighted portfolio")
    portfolio_text = st.text_input("Portfolio tickers (comma separated)", f"{ticker}, MSFT, NVDA", key="portfolio_symbols")
    initial_value = st.number_input("Starting value ($)", min_value=100.0, value=10_000.0, step=500.0)
    portfolio_symbols = list(dict.fromkeys(s.strip().upper() for s in portfolio_text.split(",") if s.strip()))[:8]
    weight_columns = st.columns(max(1, len(portfolio_symbols)))
    default_weight = 100 // max(1, len(portfolio_symbols))
    portfolio_weights = {
        symbol: weight_columns[index].number_input(
            f"{symbol} weight (%)", min_value=0, max_value=100,
            value=default_weight, step=5, key=f"weight_{symbol}",
        )
        for index, symbol in enumerate(portfolio_symbols)
    }
    weight_total = sum(portfolio_weights.values())
    st.caption(f"Selected weights total {weight_total}%. They are normalized automatically when calculating the portfolio.")
    portfolio_data = {}
    for symbol in portfolio_symbols:
        try:
            portfolio_data[symbol] = load_prices(symbol, period)["Close"]
        except Exception as exc:
            st.warning(f"Skipped {symbol}: {exc}")
    if portfolio_data:
        returns = portfolio_returns(portfolio_data, portfolio_weights)
        value = portfolio_growth(returns, initial_value)
        port_cols = st.columns(3)
        port_cols[0].metric("Ending value", f"${value.iloc[-1]:,.2f}")
        port_cols[1].metric("Portfolio return", f"{value.iloc[-1] / initial_value - 1:.1%}")
        port_cols[2].metric("Assets included", str(len(portfolio_data)))
        pfig = px.line(value, labels={"value": "Portfolio value ($)", "Date": "Date"}, template="plotly_white")
        pfig.update_traces(line_color="#168b85")
        pfig.update_layout(height=380, hovermode="x unified")
        st.plotly_chart(pfig, width="stretch")
        st.caption("This illustration rebalances daily to the selected weights and omits fees, taxes, slippage, and cash flows.")
    else:
        st.info("Enter one or more valid tickers to calculate a portfolio illustration.")

with forecast_tab:
    st.subheader("Experimental next-day estimate")
    st.warning("This is a small linear-regression experiment using five recent daily returns. It is not reliable investment guidance, and should not be used to make trades. Markets are noisy; the displayed holdout error is historical and does not predict future accuracy.")
    if st.button("Run forecast experiment"):
        try:
            estimate, mae = next_day_estimate(prices)
            st.metric("Experimental next-session estimate", f"${estimate:,.2f}")
            st.write(f"Historical holdout mean absolute return error: **{mae:.2%}**")
        except Exception as exc:
            show_error(exc)
    st.caption("Scikit-learn model; chronological 80/20 split. No tuning, external features, or confidence interval is used.")

st.divider()
st.caption("Educational use only. This dashboard is not investment, tax, or legal advice. Historical performance does not guarantee future results. Verify data independently before relying on it.")
