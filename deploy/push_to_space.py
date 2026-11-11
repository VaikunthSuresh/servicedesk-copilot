"""Create (or update) the Hugging Face Space and upload the app.

Usage:
  pip install huggingface_hub
  huggingface-cli login                      # token with WRITE scope
  python deploy/push_to_space.py <hf-username>/servicedesk-copilot [--private]

Then set secrets in the Space: Settings -> Variables and secrets -> LLM_API_KEY (+ LLM_BASE_URL, LLM_MODEL).
"""
import argparse
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("space_id")
p.add_argument("--private", action="store_true")
a = p.parse_args()

api = HfApi()
api.create_repo(a.space_id, repo_type="space", space_sdk="docker", private=a.private, exist_ok=True)

with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    for d in ["backend/app", "frontend", "scripts", "data/kb", "deploy/hf_space"]:
        shutil.copytree(ROOT / d, t / d, ignore=shutil.ignore_patterns("__pycache__", "Dockerfile"))
    for f in ["backend/requirements.txt", "data/rag_eval.json"]:
        shutil.copy(ROOT / f, t / f)
    shutil.copy(ROOT / "deploy/hf_space/Dockerfile", t / "Dockerfile")   # Space builds from root Dockerfile
    shutil.copy(ROOT / "deploy/hf_space/README.md", t / "README.md")     # Space card + config header
    api.upload_folder(folder_path=str(t), repo_id=a.space_id, repo_type="space",
                      commit_message="Deploy IT Service Desk Copilot")

print(f"Pushed. Build logs: https://huggingface.co/spaces/{a.space_id}  (first build ~10-15 min)")
