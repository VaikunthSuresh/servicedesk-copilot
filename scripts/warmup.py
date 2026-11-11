"""Download all model weights once (used at Docker build time, or run locally before a demo)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import classifier, rag, sentiment, summarizer  # noqa: E402

TICKET = "VPN keeps disconnecting since the update and I have a client demo at 3pm. " * 3
print("classifier:", classifier.classify(TICKET)["mode"])
print("sentiment:", sentiment.analyse(TICKET)["urgency"])
print("summarizer:", summarizer.summarize(TICKET)["model"])
print("embedder dims:", len(rag.embed(["warmup"])[0]))
