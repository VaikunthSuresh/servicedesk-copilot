"""Step 1 — build the fine-tuning dataset.

Source: Tobi-Bueck/customer-support-tickets (Hugging Face, CC BY-NC 4.0, non-commercial/academic use).
Keeps English tickets, the N most frequent queues, caps each class for balance, and makes a
stratified 80/10/10 split. Writes data/processed/{train,val,test}.csv and labels.json.

Usage:  python finetune/prepare_data.py --top-queues 8 --max-per-class 1500
"""
import argparse
import json
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split

OUT = Path(__file__).resolve().parents[1] / "data" / "processed"

p = argparse.ArgumentParser()
p.add_argument("--top-queues", type=int, default=8)
p.add_argument("--max-per-class", type=int, default=1500)
p.add_argument("--seed", type=int, default=42)
a = p.parse_args()

df = load_dataset("Tobi-Bueck/customer-support-tickets", split="train").to_pandas()
print("Raw rows:", len(df))
df = df[df["language"].str.lower() == "en"].copy()
df["text"] = (df["subject"].fillna("") + ". " + df["body"].fillna("")).str.strip(". ").str.strip()
df = df[df["text"].str.len() > 20].drop_duplicates("text")

top = df["queue"].value_counts().head(a.top_queues).index.tolist()
df = df[df["queue"].isin(top)]
df = df.groupby("queue", group_keys=False).apply(lambda g: g.sample(min(len(g), a.max_per_class), random_state=a.seed))
df = df[["text", "queue", "priority"]].rename(columns={"queue": "label"}).reset_index(drop=True)

train, tmp = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=a.seed)
val, test = train_test_split(tmp, test_size=0.5, stratify=tmp["label"], random_state=a.seed)

OUT.mkdir(parents=True, exist_ok=True)
for name, part in [("train", train), ("val", val), ("test", test)]:
    part.to_csv(OUT / f"{name}.csv", index=False)
(OUT / "labels.json").write_text(json.dumps(sorted(top), indent=2))

print("Labels:", sorted(top))
print("Class distribution (put this table in the report):")
print(df["label"].value_counts().to_string())
print(f"train={len(train)} val={len(val)} test={len(test)}")
