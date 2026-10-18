# MarketLens — AI Financial Intelligence Dashboard

A beginner-friendly Streamlit dashboard for exploring market history, comparing stocks with a benchmark, and illustrating portfolio risk. It uses Yahoo Finance history through `yfinance`, interactive Plotly charts, and a deliberately small scikit-learn forecasting experiment.

> **Educational use only.** This project is not investment, tax, or legal advice. Historical results do not predict future performance. It does not place trades.

## Features

- Search a ticker and view adjusted historical prices.
- Review period return, daily returns, annualized volatility, and maximum drawdown.
- Compare up to eight tickers, with SPY as the default benchmark.
- Explore a weighted portfolio illustration with configurable asset allocations and starting value. Entered weights are normalized to 100% for the calculation.
- Run an explicitly experimental next-day linear regression estimate.
- Optionally generate a neutral metrics summary when `OPENAI_API_KEY` is configured.
- Handle unknown symbols, missing history, and data-provider errors with readable messages.

## Requirements and setup

Python 3.10 or newer is recommended. From this project directory, create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the packages after reviewing and approving this command:

```bash
python -m pip install -r requirements.txt
```

Start the app:

```powershell
run_marketlens.cmd
```

On Windows, `run_marketlens.cmd` uses the project virtual environment and clears only the known unavailable `http://127.0.0.1:9` proxy values for the app process. It does not change Windows or VS Code settings, touch other proxy endpoints, or alter TLS verification. On macOS/Linux, run `streamlit run app.py`. Streamlit prints a local URL, usually `http://localhost:8501`. Press Ctrl+C in the terminal to stop it.

Run the calculation tests:

```bash
python -m pytest -q -p no:cacheprovider tests
```

## Optional AI summary

The dashboard does not need an API key for its other features. To enable its optional OpenAI summary, set the key in your shell before launching Streamlit. Never paste a real key into source code or commit it.

```powershell
$env:OPENAI_API_KEY = "your-key"
# Optional model override:
$env:OPENAI_MODEL = "gpt-4.1-mini"
run_marketlens.cmd
```

On Windows, use `run_marketlens.cmd` after setting the key to keep the same project-local proxy handling.

On macOS/Linux, use `export OPENAI_API_KEY="your-key"` before `streamlit run app.py`. The key is read from the environment and ignored `.env`/Streamlit secrets files are listed in `.gitignore`.

## Project structure

```text
app.py                         Streamlit pages, controls, and chart presentation
financial_dashboard/
  ai_summary.py                Optional API-backed educational summary
  forecasting.py               Experimental scikit-learn estimate
  market_data.py               Yahoo Finance data retrieval and validation
  metrics.py                   Return, volatility, and drawdown calculations
  portfolio.py                 Equal-weight portfolio calculations
tests/test_metrics.py          Tests for calculations and edge cases
requirements.txt               Python package dependencies
```

## How the pieces fit together

The Streamlit file handles user input and display. It asks `market_data.py` for prices, then passes closing-price series to `metrics.py` and `portfolio.py`. `forecasting.py` runs only when you press its button. `ai_summary.py` runs only when an API key is configured and you ask for a summary. This separation keeps the math easier to read and test without opening the web page.

## Limitations

Yahoo Finance data can be delayed, incomplete, or temporarily unavailable. Metrics use adjusted closing prices and a 252-session year assumption. The portfolio example rebalances daily to selected target weights and excludes costs, taxes, and cash flows. The forecasting experiment is intentionally basic and has no demonstrated predictive reliability.
