"""Section III: RAG endpoints — ingest workplace documents and chat over them."""
import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import ROOT
from ..schemas import ChatIn, ChatOut, IngestOut
from ..services import rag

router = APIRouter(prefix="/api/v1", tags=["knowledge"])
UPLOAD_DIR = ROOT / "data" / "uploads"
ALLOWED = {".pdf", ".docx", ".md", ".txt"}


@router.post("/ingest", response_model=IngestOut, summary="Upload SOPs/KB docs into the vector store")
async def ingest(files: list[UploadFile] = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    added, names = 0, []
    for f in files:
        name = Path(f.filename or "").name
        if Path(name).suffix.lower() not in ALLOWED:
            raise HTTPException(400, f"{name}: only {sorted(ALLOWED)} are supported")
        dest = UPLOAD_DIR / name
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        added += rag.ingest_file(dest)
        names.append(name)
    return {"files": names, "chunks_added": added, "total_chunks": rag.count()}


@router.post("/chat", response_model=ChatOut, summary="Ask the knowledge base (grounded, with sources)")
def chat(q: ChatIn):
    return rag.answer(q.question, q.top_k)
