"""Section III evidence — evaluates the RAG chatbot in two stages.

1. Retrieval (always, no LLM needed): for answerable questions, does the right document come back?
   -> hit@1, hit@4, MRR, overall and per question type (direct / distractor).
2. End-to-end answers (--answers, needs the LLM key): runs the real chatbot on every question, then
   uses the LLM as a judge:
   -> key-fact accuracy (does the answer contain the expected fact?)
   -> faithfulness 1-5 (is every claim supported by the retrieved context?)
   -> citation rate (does the answer cite [n] sources?)
   -> refusal rate on out-of-scope questions (does it decline instead of inventing an answer?)

Usage (after scripts/ingest_kb.py):
  python scripts/eval_rag.py            # retrieval only
  python scripts/eval_rag.py --answers  # retrieval + end-to-end with LLM judge (~80 small gpt-4o-mini calls)
Outputs: finetune/results/rag/{rag_eval.json, rag_answers.csv}
"""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import llm, rag  # noqa: E402

JUDGE = """You grade an IT service desk chatbot. Return ONLY JSON: {"correct": 0 or 1, "faithful": 1-5}.
correct = 1 if the ANSWER states the EXPECTED FACT (wording may differ), else 0.
faithful = 5 if every claim in the ANSWER is supported by the CONTEXT, 1 if it is mostly unsupported."""
# A refusal = the answer OPENS by declining. Good answers often end with "escalate if this doesn't help",
# so matching "escalate" anywhere (as v1 of this script did) wrongly counted correct answers as refusals.
REFUSAL = re.compile(r"^\s*(i )?(couldn'?t|could not|cannot|can'?t) find", re.I)

p = argparse.ArgumentParser()
p.add_argument("--answers", action="store_true")
p.add_argument("--k", type=int, default=4)
a = p.parse_args()

qs = json.loads((ROOT / "data" / "rag_eval.json").read_text())
OUT = ROOT / "finetune" / "results" / "rag"
OUT.mkdir(parents=True, exist_ok=True)


def pct(x):
    return f"{x:.1%}"


# ---------- 1. retrieval ----------
ret = []
for q in qs:
    if q["type"] == "out_of_scope":
        top = rag.retrieve(q["question"], k=1)
        ret.append({**q, "rank": None, "top_score": top[0]["score"] if top else 0.0})
        continue
    hits = rag.retrieve(q["question"], k=a.k)
    srcs = [h["source"] for h in hits]
    rank = next((i + 1 for i, s in enumerate(srcs) if s in q["expected_sources"]), 0)
    ret.append({**q, "rank": rank, "top_score": hits[0]["score"] if hits else 0.0, "top_source": srcs[0] if srcs else ""})


def retrieval_stats(rows):
    n = len(rows)
    return {"n": n, "hit@1": sum(r["rank"] == 1 for r in rows) / n,
            f"hit@{a.k}": sum(r["rank"] > 0 for r in rows) / n,
            "mrr": sum(1 / r["rank"] for r in rows if r["rank"]) / n}


answerable = [r for r in ret if r["type"] != "out_of_scope"]
summary = {"retrieval": {"all_answerable": retrieval_stats(answerable)}}
for t in ["direct", "distractor"]:
    rows = [r for r in answerable if r["type"] == t]
    if rows:
        summary["retrieval"][t] = retrieval_stats(rows)

print("Retrieval misses / non-top-1:")
for r in answerable:
    if r["rank"] != 1:
        print(f"  rank={r['rank'] or 'miss':>4}  got={r['top_source']:<48} {r['question'][:60]}")
oos = [r for r in ret if r["type"] == "out_of_scope"]
print("\nTop similarity: answerable mean %.2f | out-of-scope mean %.2f (threshold %.2f)" % (
    sum(r["top_score"] for r in answerable) / len(answerable),
    sum(r["top_score"] for r in oos) / max(1, len(oos)), rag.MIN_RELEVANCE))
summary["similarity"] = {"answerable_mean_top": round(sum(r["top_score"] for r in answerable) / len(answerable), 3),
                         "out_of_scope_mean_top": round(sum(r["top_score"] for r in oos) / max(1, len(oos)), 3),
                         "threshold": rag.MIN_RELEVANCE}

# ---------- 2. end-to-end ----------
if a.answers:
    if not llm.available():
        sys.exit("LLM not configured: set LLM_API_KEY in backend/.env")
    rows = []
    for q in qs:
        t0 = time.perf_counter()
        res = rag.answer(q["question"], a.k)
        ms = (time.perf_counter() - t0) * 1000
        ans = res["answer"]
        row = {"type": q["type"], "question": q["question"], "answer": ans, "latency_ms": round(ms),
               "sources": "; ".join(s["source"] for s in res["sources"]),
               "cited": int(bool(re.search(r"\[\d\]", ans))), "refused": int((not res["grounded"]) or bool(REFUSAL.match(ans)))}
        if q["type"] != "out_of_scope":
            ctx = "\n\n".join(s["text"] for s in res["sources"]) or "(no context)"
            raw = llm.chat(JUDGE, f"EXPECTED FACT: {q['key_fact']}\n\nCONTEXT:\n{ctx}\n\nANSWER:\n{ans}", max_tokens=30)
            m = re.search(r"\{.*\}", raw, re.S)
            j = json.loads(m.group(0)) if m else {"correct": 0, "faithful": 1}
            row.update(correct=int(j.get("correct", 0)), faithful=int(j.get("faithful", 1)))
        rows.append(row)
        print(f"  {row['type'][:5]:<5} {('ok' if row.get('correct', row['refused']) else 'XX'):<3} {q['question'][:70]}")

    ans_rows = [r for r in rows if r["type"] != "out_of_scope"]
    oos_rows = [r for r in rows if r["type"] == "out_of_scope"]
    summary["end_to_end"] = {
        "model": rag.settings.llm_model,
        "key_fact_accuracy": sum(r["correct"] for r in ans_rows) / len(ans_rows),
        "faithfulness_mean_1_to_5": sum(r["faithful"] for r in ans_rows) / len(ans_rows),
        "citation_rate": sum(r["cited"] for r in ans_rows) / len(ans_rows),
        "false_refusals_on_answerable": sum(r["refused"] for r in ans_rows) / len(ans_rows),
        "out_of_scope_refusal_rate": sum(r["refused"] for r in oos_rows) / max(1, len(oos_rows)),
        "mean_latency_ms": sum(r["latency_ms"] for r in rows) / len(rows),
    }
    with open(OUT / "rag_answers.csv", "w", newline="") as f:
        fields = ["type", "question", "answer", "sources", "cited", "refused", "correct", "faithful", "latency_ms"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

(OUT / "rag_eval.json").write_text(json.dumps(summary, indent=2))
print("\n" + json.dumps(summary, indent=2, default=lambda x: round(x, 3)))
print(f"\nSaved to {OUT}")
