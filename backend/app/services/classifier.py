"""Sub-task 1: Ticket queue classification (routing).

Owner: Member 2 (fine-tuning).
- If the fine-tuned DistilBERT exists -> use it (Section II "after").
- Otherwise -> zero-shot BART-MNLI baseline (Section II "before").
"""
from functools import lru_cache
from pathlib import Path

from ..config import settings


@lru_cache
def _finetuned():
    from transformers import pipeline
    return pipeline("text-classification", model=settings.classifier_model, top_k=3, truncation=True)


@lru_cache
def _zero_shot():
    from transformers import pipeline
    return pipeline("zero-shot-classification", model=settings.zero_shot_model)


def is_finetuned_available() -> bool:
    """Local folder with config.json, or a Hugging Face Hub id like 'your-user/distilbert-ticket-queue'."""
    m = settings.classifier_model
    if not m:
        return False
    if Path(m).is_absolute() or m.startswith("."):
        return (Path(m) / "config.json").exists()
    return True


def candidate_labels() -> list[str]:
    """Use the real dataset labels (written by prepare_data.py) if available."""
    from ..config import ROOT
    f = ROOT / "data" / "processed" / "labels.json"
    if f.exists():
        import json
        return json.loads(f.read_text())
    return settings.queue_labels


def classify(text: str) -> dict:
    if is_finetuned_available():
        preds = _finetuned()(text)
        preds = preds[0] if preds and isinstance(preds[0], list) else preds
        return {
            "label": preds[0]["label"],
            "score": round(float(preds[0]["score"]), 4),
            "model": f"{Path(settings.classifier_model).name} (fine-tuned)",
            "mode": "fine-tuned",
            "top_k": [{"label": p["label"], "score": round(float(p["score"]), 4)} for p in preds],
        }
    out = _zero_shot()(text, candidate_labels=candidate_labels())
    top = [{"label": l, "score": round(float(s), 4)} for l, s in zip(out["labels"][:3], out["scores"][:3])]
    return {
        "label": top[0]["label"],
        "score": top[0]["score"],
        "model": settings.zero_shot_model,
        "mode": "zero-shot-baseline",
        "top_k": top,
    }
