"""Step 2 — fine-tune DistilBERT (SLM, 66M params) for ticket queue routing.

Runs in ~15-25 min on a free Colab T4 GPU with the defaults.
Usage:  python finetune/train_classifier.py --epochs 3 --lr 5e-5
Output: finetune/outputs/distilbert-ticket-queue/  (picked up automatically by the API)
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          EarlyStoppingCallback, Trainer, TrainingArguments)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "finetune" / "outputs" / "distilbert-ticket-queue"

p = argparse.ArgumentParser()
p.add_argument("--base", default="distilbert-base-uncased")
p.add_argument("--epochs", type=float, default=3)
p.add_argument("--lr", type=float, default=5e-5)
p.add_argument("--batch", type=int, default=16)
p.add_argument("--max-len", type=int, default=256)
a = p.parse_args()

labels = json.loads((DATA / "labels.json").read_text())
l2i = {l: i for i, l in enumerate(labels)}
tok = AutoTokenizer.from_pretrained(a.base)


def load(split):
    df = pd.read_csv(DATA / f"{split}.csv")
    ds = Dataset.from_dict({"text": df["text"].tolist(), "label": df["label"].map(l2i).tolist()})
    return ds.map(lambda b: tok(b["text"], truncation=True, max_length=a.max_len), batched=True)


train, val = load("train"), load("val")
model = AutoModelForSequenceClassification.from_pretrained(
    a.base, num_labels=len(labels), id2label=dict(enumerate(labels)), label2id=l2i)


def metrics(ev):
    preds = np.argmax(ev.predictions, axis=-1)
    return {"accuracy": accuracy_score(ev.label_ids, preds),
            "macro_f1": f1_score(ev.label_ids, preds, average="macro")}


args = TrainingArguments(
    output_dir=str(ROOT / "finetune" / "checkpoints"),
    num_train_epochs=a.epochs, learning_rate=a.lr, weight_decay=0.01, warmup_ratio=0.1,
    per_device_train_batch_size=a.batch, per_device_eval_batch_size=a.batch * 2,
    eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
    metric_for_best_model="macro_f1", save_total_limit=1, logging_steps=50, report_to="none", seed=42,
)
trainer = Trainer(model=model, args=args, train_dataset=train, eval_dataset=val,
                  data_collator=DataCollatorWithPadding(tok), compute_metrics=metrics,
                  callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])
trainer.train()

OUT.mkdir(parents=True, exist_ok=True)
trainer.save_model(str(OUT))
tok.save_pretrained(str(OUT))
pd.DataFrame(trainer.state.log_history).to_csv(OUT / "training_log.csv", index=False)
print("Validation:", trainer.evaluate())
print("Saved to", OUT)
