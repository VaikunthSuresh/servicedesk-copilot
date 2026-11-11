"""Step 3 — before vs after evidence for Section II (v2: per-run folders).

  BEFORE: zero-shot facebook/bart-large-mnli (no training), stratified sample of the test set
  AFTER : the fine-tuned model of this run, full test set
Writes finetune/results/<run>/{metrics.json, comparison.csv, confusion_matrix.png, *_report.txt}

Usage:  python finetune/evaluate.py --run v2_8cls [--zero-shot-sample 400] [--skip-zero-shot]
"""
import argparse
import json
import time
from pathlib import Path

import matplotlib
import pandas as pd
import torch
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, f1_score
from transformers import pipeline

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
p.add_argument("--zero-shot-sample", type=int, default=400)
p.add_argument("--skip-zero-shot", action="store_true")
a = p.parse_args()

DATA = ROOT / "data" / "processed" / a.run
MODEL = ROOT / "finetune" / "outputs" / a.run
RES = ROOT / "finetune" / "results" / a.run
RES.mkdir(parents=True, exist_ok=True)
DEVICE = 0 if torch.cuda.is_available() else -1

labels = json.loads((DATA / "labels.json").read_text())
test = pd.read_csv(DATA / "test.csv")


def run(name, preds_fn, df):
    t = time.perf_counter()
    preds = preds_fn(df["text"].tolist())
    ms = (time.perf_counter() - t) * 1000 / len(df)
    rep = classification_report(df["label"], preds, labels=labels, zero_division=0)
    (RES / f"{name}_report.txt").write_text(rep)
    print(f"\n=== {name} ===\n{rep}")
    return preds, {"model": name, "n_test": len(df), "accuracy": round(accuracy_score(df["label"], preds), 4),
                   "macro_f1": round(f1_score(df["label"], preds, average="macro"), 4),
                   "weighted_f1": round(f1_score(df["label"], preds, average="weighted"), 4),
                   "latency_ms_per_ticket": round(ms, 1)}


rows = []
if not a.skip_zero_shot:
    per = max(1, a.zero_shot_sample // len(labels))
    zs_test = test.groupby("label", group_keys=False)[test.columns.tolist()].apply(
        lambda g: g.sample(min(len(g), per), random_state=42))
    zs = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=DEVICE)
    _, before = run("before_zero_shot_bart_mnli",
                    lambda X: [zs(x, candidate_labels=labels, truncation=True)["labels"][0] for x in X], zs_test)
    rows.append(before)

cfg = json.loads((MODEL / "run_config.json").read_text()) if (MODEL / "run_config.json").exists() else {}
name = f"after_finetuned_{cfg.get('base', 'model').split('/')[-1]}"
ft = pipeline("text-classification", model=str(MODEL), truncation=True, device=DEVICE)
ft_preds, after = run(name, lambda X: [o["label"] for o in ft(X, batch_size=32)], test)
rows.append(after)

pd.DataFrame(rows).to_csv(RES / "comparison.csv", index=False)
(RES / "metrics.json").write_text(json.dumps({r["model"]: r for r in rows}, indent=2))

fig, ax = plt.subplots(figsize=(10, 8))
ConfusionMatrixDisplay.from_predictions(test["label"], ft_preds, labels=labels, normalize="true",
                                        values_format=".2f", xticks_rotation=45, ax=ax, colorbar=False)
ax.set_title(f"{name} — test set confusion matrix (row-normalised) — run {a.run}")
fig.tight_layout()
fig.savefig(RES / "confusion_matrix.png", dpi=150)
print("\n", pd.DataFrame(rows).to_string(index=False))
