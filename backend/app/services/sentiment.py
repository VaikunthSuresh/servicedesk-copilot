"""Sub-task 2: Sentiment + urgency detection (prioritisation).

Owner: Member 4.
Sentiment comes from a RoBERTa model; urgency combines that with keyword signals
so the priority is explainable to an agent.
"""
import re
from functools import lru_cache

from ..config import settings

URGENCY_PATTERNS = {
    "outage": r"\b(down|outage|not working|unable to|(can'?t|cannot) (log ?in|access|connect)|locked out|crash(ed|ing)?)\b",
    "deadline": r"\b(urgent|asap|immediately|today|deadline|demo|client|meeting|by \d{1,2}\s?(am|pm))\b",
    "scope": r"\b(everyone|whole team|all users|entire|production|prod|multiple users)\b",
    "security": r"\b(phish(ing)?|hacked|breach|malware|virus|ransomware|suspicious)\b",
}


@lru_cache
def _model():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model=settings.sentiment_model, truncation=True)


def urgency_signals(text: str) -> list[str]:
    t = text.lower()
    return [name for name, pat in URGENCY_PATTERNS.items() if re.search(pat, t)]


def priority(sentiment: str, signals: list[str]) -> str:
    score = len(signals) + (1 if sentiment == "negative" else 0)
    if "security" in signals or score >= 3:
        return "P1"
    if score >= 1:
        return "P2"
    return "P3"


def analyse(text: str) -> dict:
    pred = _model()(text)[0]
    label = pred["label"].lower()
    label = {"label_0": "negative", "label_1": "neutral", "label_2": "positive"}.get(label, label)
    sig = urgency_signals(text)
    return {
        "sentiment": label,
        "score": round(float(pred["score"]), 4),
        "urgency": priority(label, sig),
        "urgency_signals": sig,
        "model": settings.sentiment_model,
    }
