"""IT Service Desk Copilot — FastAPI entrypoint.

Run:  uvicorn app.main:app --reload --port 8000   (from the backend/ folder)
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import knowledge, tickets
from .services import classifier, llm

app = FastAPI(
    title="IT Service Desk Copilot API",
    version="0.1.0",
    description="Customer Service – Enterprise IT Service Desk. NLP sub-tasks (classification, "
                "sentiment/urgency, summarisation, RAG Q&A, reply drafting) chained to reduce ticket resolution time.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(tickets.router)
app.include_router(knowledge.router)


@app.get("/health", tags=["ops"])
def health():
    return {
        "status": "ok",
        "classifier_mode": "fine-tuned" if classifier.is_finetuned_available() else "zero-shot-baseline",
        "llm_configured": llm.available(),
        "llm_model": settings.llm_model,
    }
