"""Bulk-load every document in data/kb into the vector store.
Usage (from repo root):  python scripts/ingest_kb.py [folder]
Each member can point this at their own anonymised workplace documents for Part IV."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import rag  # noqa: E402

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "kb"
for f in sorted(folder.iterdir()):
    if f.suffix.lower() in {".pdf", ".docx", ".md", ".txt"}:
        print(f"{f.name}: {rag.ingest_file(f)} chunks")
print("Total chunks in store:", rag.count())
