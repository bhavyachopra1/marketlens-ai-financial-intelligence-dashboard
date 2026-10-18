"""Optional OpenAI summary. The application works without credentials."""

from __future__ import annotations

import os


def summarize(ticker: str, metrics: dict[str, float]) -> str | None:
    """Generate a short descriptive summary only when an API key is configured."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=("Write a brief, neutral educational description of these historical metrics for "
                   f"{ticker}. State that past performance does not predict future results. "
                   f"Do not recommend buying or selling. Metrics: {metrics}"),
        )
        return response.output_text
    except Exception as exc:
        raise RuntimeError(f"The optional AI summary could not be generated: {exc}") from exc
