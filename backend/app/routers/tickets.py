"""Ticket understanding endpoints (Section I sub-tasks) + the unified /triage pipeline."""
import time

from fastapi import APIRouter

from ..schemas import ClassifyOut, SentimentOut, SummarizeOut, TicketIn, TriageOut
from ..services import classifier, rag, reply, sentiment, summarizer

router = APIRouter(prefix="/api/v1", tags=["tickets"])


@router.post("/classify", response_model=ClassifyOut, summary="Route ticket to a support queue")
def classify(t: TicketIn):
    return classifier.classify(t.text)


@router.post("/sentiment", response_model=SentimentOut, summary="Sentiment + P1/P2/P3 urgency")
def sentiment_(t: TicketIn):
    return sentiment.analyse(t.text)


@router.post("/summarize", response_model=SummarizeOut, summary="Summarise long tickets for agents")
def summarize(t: TicketIn):
    return summarizer.summarize(t.text)


@router.post("/triage", response_model=TriageOut, summary="Full pipeline: classify -> prioritise -> summarise -> RAG -> reply")
def triage(t: TicketIn):
    lat = {}

    def timed(name, fn, *a):
        s = time.perf_counter()
        out = fn(*a)
        lat[name] = round((time.perf_counter() - s) * 1000, 1)
        return out

    cls = timed("classify", classifier.classify, t.text)
    sen = timed("sentiment", sentiment.analyse, t.text)
    summ = timed("summarize", summarizer.summarize, t.text)
    res = timed("rag", rag.answer, summ["summary"])
    draft = timed("reply", reply.draft, t.text, cls["label"], sen["urgency"], res["answer"])
    lat["total"] = round(sum(lat.values()), 1)
    return {
        "classification": cls, "sentiment": sen, "summary": summ,
        "suggested_resolution": res, "draft_reply": draft, "latency_ms": lat,
    }
