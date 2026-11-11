# Team Plan — equal 25% split

## Ownership

| Member | Technical block | Report section | Video segment |
|---|---|---|---|
| **Vaikunth** | Architecture, FastAPI backend, `/triage` pipeline, Docker, cloud deployment | I: architecture + API design | Intro, architecture, Swagger/API demo |
| **Member 2** | Fine-tuning: `prepare_data.py`, Colab training, `evaluate.py`, before/after analysis | II (complete) | Fine-tuning results |
| **Member 3** | RAG: KB curation, chunking/embedding choices, prompt, `eval_rag.py`, grounding/refusal tests | III (complete) | Chatbot + sources demo |
| **Member 4** | Sentiment/urgency + summarisation services, Streamlit UI, report assembly | I: sub-tasks + UI | UI walkthrough, video editing |
| **Everyone** | Own **Part IV** (Anchor/Apply/Analyse/Reflect) using own workplace's anonymised docs | IV (individual) | — |

## Phases

| Phase | Done when | Owner |
|---|---|---|
| **P0 Setup** ✅ | Repo scaffold, API contract (`schemas.py`), stubs, tests pass | Vaikunth |
| **P1 Build (parallel)** | Fine-tuned model saved · KB ≥ 5 docs ingested · UI shows all tabs · LLM key wired | M2 · M3 · M4 · V |
| **P2 Integrate + deploy** | `docker compose up` works on a clean machine; public URL (HF Spaces / Render / EC2) | Vaikunth |
| **P3 Evaluate** | `finetune/results/comparison.csv`, confusion matrix, `rag_eval.json`, triage latency table | M2, M3 |
| **P4 Situated learning** | Each member's Part IV drafted, with their own screenshots | All |
| **P5 Report + video** | `<groupid>.pdf` with contribution table; 8–10 min video on Drive, link shared with "anyone with link" | M4 + all |

## Report checklist (per section)

- **I:** domain + problem statement; sub-task table with models and why (LLM vs SLM); architecture diagram; Swagger screenshot; UI screenshots of `/triage` on 3 sample tickets; latency table.
- **II:** dataset source/licence, class distribution, preprocessing; hyper-parameters; training curves; **before vs after** table (accuracy, macro-F1, latency); confusion matrix; error analysis (2–3 misrouted tickets and why).
- **III:** documents used; chunk size/overlap and embedding model rationale; prompt; hit-rate@4/MRR; 3 screenshots of grounded answers with sources and 1 of a correct refusal.
- **IV (each member):** Anchor = their org's service desk pain point · Apply = app run on their own anonymised SOPs (screenshots) · Analyse = what worked, what failed, risks (privacy, hallucination, cost) · Reflect = what they'd change before production.
- **Contribution table:** name, ID, blocks owned, 25%.

## Datasets

| Use | Dataset | Notes |
|---|---|---|
| Fine-tuning (chosen) | `Tobi-Bueck/customer-support-tickets` (HF) | ~28k English tickets, labelled `queue`, `priority`, `type`; CC BY-NC 4.0 |
| Alternative | `Noise144/ticket_classification_IT_EN` (HF) | 1,800 synthetic IT tickets, 18 classes (EN/IT), small, trains fast |
| RAG | `data/kb/*.md` (synthetic SOPs) + each member's anonymised workplace docs | Never upload confidential documents to a public deployment |
