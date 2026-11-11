"""Step 4 — one table across all runs (v1 + v2 experiments) for the report.
Usage:  python finetune/compare_runs.py"""
import json
from pathlib import Path

import pandas as pd

RES = Path(__file__).resolve().parent / "results"
rows = []
v1 = RES / "metrics.json"  # the original v1 run lives at the top level of results/
if v1.exists():
    for k, r in json.loads(v1.read_text()).items():
        rows.append({"run": "v1_8cls_distilbert", **r})
for f in sorted(RES.glob("*/metrics.json")):
    for r in json.loads(f.read_text()).values():
        rows.append({"run": f.parent.name, **r})
df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv(RES / "all_runs.csv", index=False)
