"""Section III evidence: retrieval hit-rate@k and MRR on a labelled question set, plus sample answers.
Usage (after ingest_kb.py):  python scripts/eval_rag.py
Add your own questions to data/rag_eval.json (question -> expected source file)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import rag  # noqa: E402

qs = json.loads((ROOT / "data" / "rag_eval.json").read_text())
hits, rr, rows = 0, 0.0, []
for q in qs:
    srcs = [h["source"] for h in rag.retrieve(q["question"], k=4)]
    rank = srcs.index(q["expected_source"]) + 1 if q["expected_source"] in srcs else 0
    hits += rank > 0
    rr += 1 / rank if rank else 0
    rows.append((q["question"][:60], q["expected_source"], rank or "miss"))
for r in rows:
    print(f"{r[2]!s:>5}  {r[1]:<45} {r[0]}")
print(f"\nHit-rate@4 = {hits/len(qs):.2%}   MRR = {rr/len(qs):.3f}   (n={len(qs)})")
out = ROOT / "finetune" / "results"
out.mkdir(parents=True, exist_ok=True)
(out / "rag_eval.json").write_text(json.dumps({"hit_rate@4": hits / len(qs), "mrr": rr / len(qs), "n": len(qs)}, indent=2))
