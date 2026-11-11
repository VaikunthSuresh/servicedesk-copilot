"""Step 3 — before vs after evidence for Section II.

Compares, on the SAME held-out test set:
  BEFORE: zero-shot facebook/bart-large-mnli (no training)
  AFTER : fine-tuned DistilBERT
Writes finetune/results/{metrics.json, comparison.csv, confusion_matrix.png, *_report.txt}.

Usage:  python finetune/evaluate.py [--zero-shot-sample 500]
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
DATA = ROOT / "data" / "processed"
MODEL = ROOT / "finetune" / "outputs" / "distilbert-ticket-queue"
RES = ROOT / "finetune" / "results"
RES.mkdir(parents=True, exist_ok=True)

p = argparse.ArgumentParser()
p.add_argument("--zero-shot-sample", type=int, default=500, help="zero-shot is slow; evaluate on a stratified sample")
a = p.parse_args()

labels = json.loads((DATA / "labels.json").read_text())
test = pd.read_csv(DATA / "test.csv")
zs_test = test.groupby("label", group_keys=False).apply(
    lambda g: g.sample(min(len(g), max(1, a.zero_shot_sample // len(labels))), random_state=42))


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


zs = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device_map="auto")
_, before = run("before_zero_shot_bart_mnli",
                lambda X: [zs(x, candidate_labels=labels, truncation=True)["labels"][0] for x in X], zs_test)

ft = pipeline("text-classification", model=str(MODEL), truncation=True, device=0 if torch.cuda.is_available() else -1)
ft_preds, after = run("after_finetuned_distilbert", lambda X: [o["label"] for o in ft(X, batch_size=32)], test)

pd.DataFrame([before, after]).to_csv(RES / "comparison.csv", index=False)
(RES / "metrics.json").write_text(json.dumps({"before": before, "after": after}, indent=2))

fig, ax = plt.subplots(figsize=(10, 8))
ConfusionMatrixDisplay.from_predictions(test["label"], ft_preds, labels=labels, xticks_rotation=45, ax=ax, colorbar=False)
ax.set_title("Fine-tuned DistilBERT — test set confusion matrix")
fig.tight_layout()
fig.savefig(RES / "confusion_matrix.png", dpi=150)
print("\nBefore vs after:\n", pd.DataFrame([before, after]).to_string(index=False))
