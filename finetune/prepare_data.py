"""Step 1 — build the fine-tuning dataset (v2).

Source: Tobi-Bueck/customer-support-tickets (Hugging Face, CC BY-NC 4.0, academic use).
v2 changes vs v1:
  * no 1,500-per-class cap by default (use all English tickets of the top queues)
  * exact-duplicate texts removed, and texts that appear with CONFLICTING labels dropped
    (the HF repo bundles several dataset versions, so the same ticket can carry different queues)
  * optional --merge: combine the four queues that are semantically near-identical
    (IT Support + Technical Support, Customer Service + Product Support)
  * every run writes to its own folder: data/processed/<run>/

Usage:  python finetune/prepare_data.py --run v2_8cls
        python finetune/prepare_data.py --run v2_6cls_merged --merge
"""
import argparse
import json
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
MERGE = {
    "IT Support": "Technical & IT Support",
    "Technical Support": "Technical & IT Support",
    "Customer Service": "Customer & Product Support",
    "Product Support": "Customer & Product Support",
}

p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
p.add_argument("--top-queues", type=int, default=8)
p.add_argument("--max-per-class", type=int, default=0, help="0 = no cap")
p.add_argument("--merge", action="store_true")
p.add_argument("--seed", type=int, default=42)
a = p.parse_args()
OUT = ROOT / "data" / "processed" / a.run

df = load_dataset("Tobi-Bueck/customer-support-tickets", split="train").to_pandas()
print("Raw rows:", len(df))
df = df[df["language"].str.lower() == "en"].copy()
df["text"] = (df["subject"].fillna("") + ". " + df["body"].fillna("")).str.strip(". ").str.strip()
df["text"] = df["text"].str.replace(r"\s+", " ", regex=True)
df = df[df["text"].str.len() > 20]
print("English rows:", len(df))

top = df["queue"].value_counts().head(a.top_queues).index.tolist()
df = df[df["queue"].isin(top)].copy()
if a.merge:
    df["queue"] = df["queue"].replace(MERGE)

# Drop texts that occur with more than one label (label noise), then exact duplicates.
n_labels = df.groupby("text")["queue"].nunique()
conflicting = n_labels[n_labels > 1].index
before = len(df)
df = df[~df["text"].isin(conflicting)].drop_duplicates("text")
print(f"Removed {before - len(df)} duplicate/conflicting rows ({len(conflicting)} texts had conflicting labels)")

if a.max_per_class:
    df = df.groupby("queue", group_keys=False)[df.columns.tolist()].apply(
        lambda g: g.sample(min(len(g), a.max_per_class), random_state=a.seed))
df = df[["text", "queue", "priority"]].rename(columns={"queue": "label"}).reset_index(drop=True)

train, tmp = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=a.seed)
val, test = train_test_split(tmp, test_size=0.5, stratify=tmp["label"], random_state=a.seed)

OUT.mkdir(parents=True, exist_ok=True)
for name, part in [("train", train), ("val", val), ("test", test)]:
    part.to_csv(OUT / f"{name}.csv", index=False)
labels = sorted(df["label"].unique())
(OUT / "labels.json").write_text(json.dumps(labels, indent=2))

print("Labels:", labels)
print("Class distribution (put this table in the report):")
print(df["label"].value_counts().to_string())
print(f"train={len(train)} val={len(val)} test={len(test)}  ->  {OUT}")
