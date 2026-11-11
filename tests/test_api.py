"""Fast tests: model calls are stubbed so this runs in seconds without downloads.
Run from repo root:  pytest -q"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import classifier, rag, sentiment, summarizer  # noqa: E402

client = TestClient(app)
TICKET = "VPN is down since the update and I have a client demo at 3pm, please help ASAP"


@pytest.fixture(autouse=True)
def stub_models(monkeypatch):
    monkeypatch.setattr(classifier, "is_finetuned_available", lambda: False)
    monkeypatch.setattr(classifier, "_zero_shot", lambda: lambda t, candidate_labels: {
        "labels": ["IT Support"] + candidate_labels[1:3], "scores": [0.8, 0.1, 0.05]})
    monkeypatch.setattr(sentiment, "_model", lambda: lambda t: [{"label": "negative", "score": 0.91}])
    monkeypatch.setattr(summarizer, "_model", lambda: lambda t, **k: [{"summary_text": "VPN down before demo."}])
    monkeypatch.setattr(rag, "retrieve", lambda q, k=None: [
        {"source": "SOP-001_VPN_Troubleshooting.md", "chunk_id": 0, "score": 0.71, "text": "Restart PanGPS service."}])
    monkeypatch.setattr(rag.llm, "available", lambda: False)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_classify_baseline():
    d = client.post("/api/v1/classify", json={"text": TICKET}).json()
    assert d["label"] == "IT Support" and d["mode"] == "zero-shot-baseline"


def test_sentiment_priority():
    d = client.post("/api/v1/sentiment", json={"text": TICKET}).json()
    assert d["urgency"] == "P1" and {"outage", "deadline"} <= set(d["urgency_signals"])


def test_security_always_p1():
    assert sentiment.priority("neutral", ["security"]) == "P1"
    assert sentiment.priority("positive", []) == "P3"


def test_short_ticket_not_summarised():
    d = client.post("/api/v1/summarize", json={"text": "Printer jammed"}).json()
    assert d["summary"] == "Printer jammed"


def test_chat_grounded_with_sources():
    d = client.post("/api/v1/chat", json={"question": "vpn drops"}).json()
    assert d["grounded"] and d["sources"][0]["source"].startswith("SOP-001")


def test_chat_refuses_without_context(monkeypatch):
    monkeypatch.setattr(rag, "retrieve", lambda q, k=None: [{"source": "x", "chunk_id": 0, "score": 0.05, "text": "x"}])
    d = client.post("/api/v1/chat", json={"question": "what is the canteen menu"}).json()
    assert not d["grounded"] and d["sources"] == []


def test_triage_pipeline():
    d = client.post("/api/v1/triage", json={"text": TICKET}).json()
    assert d["classification"]["label"] == "IT Support"
    assert d["sentiment"]["urgency"] == "P1"
    assert "IT Support" in d["draft_reply"]
    assert set(d["latency_ms"]) == {"classify", "sentiment", "summarize", "rag", "reply", "total"}


def test_ingest_rejects_bad_type():
    r = client.post("/api/v1/ingest", files=[("files", ("evil.exe", b"x"))])
    assert r.status_code == 400


def test_chunking_overlap_and_size():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(10))
    chunks = rag.chunk(text, size=500, overlap=80)
    assert len(chunks) > 1 and all(len(c) <= 500 + 80 + 400 for c in chunks)
    assert all(rag.chunk(p, 500, 80) for p in ["a" * 2000])
