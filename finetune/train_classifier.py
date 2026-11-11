"""Step 2 — fine-tune a transformer for ticket queue routing (v2).

v2 changes vs v1:
  * --base lets you pick the backbone (default roberta-base, 125M params; distilbert-base-uncased still works)
  * more epochs with early stopping on macro-F1 (v1 was still improving at epoch 3)
  * class-weighted loss, since the full data is imbalanced
  * fp16 on GPU (about 2x faster on a Colab T4)

Usage:  python finetune/train_classifier.py --run v2_8cls --base roberta-base --epochs 5 --lr 2e-5
Output: finetune/outputs/<run>/
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          EarlyStoppingCallback, Trainer, TrainingArguments)

ROOT = Path(__file__).resolve().parents[1]

p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
p.add_argument("--base", default="roberta-base")
p.add_argument("--epochs", type=float, default=5)
p.add_argument("--lr", type=float, default=2e-5)
p.add_argument("--batch", type=int, default=32)
p.add_argument("--max-len", type=int, default=256)
p.add_argument("--no-class-weights", action="store_true")
a = p.parse_args()

DATA = ROOT / "data" / "processed" / a.run
OUT = ROOT / "finetune" / "outputs" / a.run
labels = json.loads((DATA / "labels.json").read_text())
l2i = {l: i for i, l in enumerate(labels)}
tok = AutoTokenizer.from_pretrained(a.base)


def load(split):
    df = pd.read_csv(DATA / f"{split}.csv")
    ds = Dataset.from_dict({"text": df["text"].tolist(), "label": df["label"].map(l2i).tolist()})
    return ds.map(lambda b: tok(b["text"], truncation=True, max_length=a.max_len), batched=True), df


(train, train_df), (val, _) = load("train"), load("val")
model = AutoModelForSequenceClassification.from_pretrained(
    a.base, num_labels=len(labels), id2label=dict(enumerate(labels)), label2id=l2i)

weights = None
if not a.no_class_weights:
    y = train_df["label"].map(l2i).to_numpy()
    weights = torch.tensor(compute_class_weight("balanced", classes=np.arange(len(labels)), y=y), dtype=torch.float)
    print("Class weights:", dict(zip(labels, weights.round(decimals=2).tolist())))


class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        y = inputs.pop("labels")
        out = model(**inputs)
        w = weights.to(out.logits.device) if weights is not None else None
        loss = torch.nn.functional.cross_entropy(out.logits, y, weight=w)
        return (loss, out) if return_outputs else loss


def metrics(ev):
    preds = np.argmax(ev.predictions, axis=-1)
    return {"accuracy": accuracy_score(ev.label_ids, preds),
            "macro_f1": f1_score(ev.label_ids, preds, average="macro")}


args = TrainingArguments(
    output_dir=str(ROOT / "finetune" / "checkpoints" / a.run),
    num_train_epochs=a.epochs, learning_rate=a.lr, weight_decay=0.01, warmup_ratio=0.1,
    lr_scheduler_type="linear", per_device_train_batch_size=a.batch, per_device_eval_batch_size=a.batch * 2,
    eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
    metric_for_best_model="macro_f1", save_total_limit=1, logging_steps=50, report_to="none", seed=42,
    fp16=torch.cuda.is_available(),
)
trainer = WeightedTrainer(model=model, args=args, train_dataset=train, eval_dataset=val,
                          data_collator=DataCollatorWithPadding(tok), compute_metrics=metrics,
                          callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])
trainer.train()

OUT.mkdir(parents=True, exist_ok=True)
trainer.save_model(str(OUT))
tok.save_pretrained(str(OUT))
pd.DataFrame(trainer.state.log_history).to_csv(OUT / "training_log.csv", index=False)
(OUT / "run_config.json").write_text(json.dumps(vars(a), indent=2))
print("Validation:", trainer.evaluate())
print("Saved to", OUT)
