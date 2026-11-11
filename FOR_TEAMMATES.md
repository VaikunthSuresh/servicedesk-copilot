# Running the IT Service Desk Copilot (for teammates)

The code lives in our private GitHub repository. The fine-tuned routing model (~500 MB) is too large for git,
so it is attached to the repository's **Releases** page (https://github.com/VaikunthSuresh/servicedesk-copilot/releases/tag/v1.0) as `router-model-v2.zip`. Without it the app still runs,
using a slower, less accurate zero-shot router.

## Setup (about 15 minutes, needs Python 3.10–3.12)

1. Clone the repo, then download `router-model-v2.zip` from the repo's **Releases** page into the folder
   that CONTAINS `servicedesk-copilot/` and unzip it there (it adds `finetune/outputs/v2_6cls_merged/`):
   ```bash
   git clone https://github.com/VaikunthSuresh/servicedesk-copilot.git
   unzip router-model-v2.zip            # run next to the servicedesk-copilot folder, not inside it
   ```
   Later updates: `git pull` inside the folder.
2. Create a virtual environment and install:
   ```bash
   cd servicedesk-copilot
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt -r frontend/requirements.txt
   ```
3. Add **your own** LLM key:
   ```bash
   cp backend/.env.example backend/.env   # Windows: copy backend\.env.example backend\.env
   ```
   Open `backend/.env` and paste your key after `LLM_API_KEY=`.
   No OpenAI key? Use Groq's free tier, or Ollama locally — examples are in the file.
4. Load the knowledge base (first run downloads ~1.5 GB of models):
   ```bash
   python scripts/ingest_kb.py
   ```
5. Start the app in two terminals (venv activated in both):
   ```bash
   cd backend && uvicorn app.main:app --port 8000     # terminal 1
   streamlit run frontend/app.py                      # terminal 2, from the project folder
   ```
   UI: http://localhost:8501 · API docs: http://localhost:8000/docs
   Check http://localhost:8000/health shows `"classifier_mode": "fine-tuned"`.

## For your Section IV
Follow the **"Section IV template (teammates)"** tab in the report. Put your synthetic workplace documents in
`data/workplace/<your-name>/` and upload them in the app's **Knowledge base** tab.

Never put real company documents, real tickets or your API key in this folder if you share it onward.
