"""Central configuration. Every value can be overridden with an environment variable
(or a .env file in the backend folder)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Absolute path so backend/.env is found whether you run from repo root, backend/, or scripts/.
    model_config = SettingsConfigDict(env_file=ROOT / "backend" / ".env", extra="ignore")

    # --- Sub-task models (Hugging Face model ids or local paths) ---
    # Fine-tuned DistilBERT output from finetune/train_classifier.py.
    # If the folder does not exist yet, the API falls back to the zero-shot baseline.
    # Best available fine-tuned router: v2 (RoBERTa, 6 groups) if present, else v1 (DistilBERT).
    # Override with CLASSIFIER_MODEL (a local folder or a Hugging Face Hub id).
    classifier_model: str = str(next(
        (p for p in (ROOT / "finetune" / "outputs" / "v2_6cls_merged",
                     ROOT / "finetune" / "outputs" / "distilbert-ticket-queue") if (p / "config.json").exists()),
        ROOT / "finetune" / "outputs" / "v2_6cls_merged"))
    zero_shot_model: str = "facebook/bart-large-mnli"
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    summarizer_model: str = "sshleifer/distilbart-cnn-12-6"

    # --- RAG ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_dir: str = str(ROOT / "data" / "chroma")
    collection_name: str = "servicedesk_kb"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4

    # --- LLM (any OpenAI-compatible endpoint: OpenAI, Groq, Together, Ollama, vLLM, Azure) ---
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2

    # Labels used by the zero-shot baseline (keep in sync with the fine-tuning labels)
    queue_labels: list[str] = [
        "Technical Support",
        "Product Support",
        "Customer Service",
        "IT Support",
        "Billing and Payments",
        "Returns and Exchanges",
        "Service Outages and Maintenance",
        "Sales and Pre-Sales",
        "Human Resources",
        "General Inquiry",
    ]


settings = Settings()
