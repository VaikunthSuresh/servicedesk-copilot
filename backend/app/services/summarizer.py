"""Sub-task 3: Ticket summarisation for agents.

Owner: Member 4.
Short tickets (< 40 words) are returned as-is: summarising them adds latency, not value.
"""
from functools import lru_cache

from ..config import settings


@lru_cache
def _model():
    from transformers import pipeline
    return pipeline("summarization", model=settings.summarizer_model)


def summarize(text: str) -> dict:
    words = len(text.split())
    if words < 40:
        return {"summary": text.strip(), "model": "passthrough (ticket already short)"}
    max_len = min(80, max(25, words // 2))
    out = _model()(text, max_length=max_len, min_length=min(15, max_len - 5), do_sample=False, truncation=True)
    return {"summary": out[0]["summary_text"].strip(), "model": settings.summarizer_model}
