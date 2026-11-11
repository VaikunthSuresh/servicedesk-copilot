"""Request/response contracts for every endpoint. These are the API contract the whole team builds against."""
from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    text: str = Field(..., min_length=3, examples=["VPN keeps disconnecting every 10 minutes since this morning's update. I have a client demo at 3pm!"])


class ClassifyOut(BaseModel):
    label: str
    score: float
    model: str
    mode: str = Field(..., description="'fine-tuned' or 'zero-shot-baseline'")
    top_k: list[dict]


class SentimentOut(BaseModel):
    sentiment: str
    score: float
    urgency: str = Field(..., description="P1 / P2 / P3 derived from sentiment + urgency keywords")
    urgency_signals: list[str]
    model: str


class SummarizeOut(BaseModel):
    summary: str
    model: str


class ChatIn(BaseModel):
    question: str = Field(..., min_length=3, examples=["How do I fix VPN disconnects on GlobalProtect?"])
    top_k: int | None = None


class Source(BaseModel):
    source: str
    chunk_id: int
    score: float
    text: str


class ChatOut(BaseModel):
    answer: str
    sources: list[Source]
    model: str
    grounded: bool = Field(..., description="False if no relevant context was found")


class IngestOut(BaseModel):
    files: list[str]
    chunks_added: int
    total_chunks: int


class TriageOut(BaseModel):
    """Unified pipeline: all sub-tasks chained towards one goal (faster ticket resolution)."""
    classification: ClassifyOut
    sentiment: SentimentOut
    summary: SummarizeOut
    suggested_resolution: ChatOut
    draft_reply: str
    latency_ms: dict[str, float]
