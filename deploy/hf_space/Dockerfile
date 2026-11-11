# Single-container image for Hugging Face Spaces (Docker SDK).
# nginx :7860  ->  /            Streamlit UI (:8501)
#              ->  /docs /api   FastAPI     (:8000)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends nginx && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user      # Spaces run containers as uid 1000
WORKDIR /app
ENV PYTHONUNBUFFERED=1 HF_HOME=/app/.hf-cache PATH=/home/user/.local/bin:$PATH

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY backend/requirements.txt backend-req.txt
COPY frontend/requirements.txt frontend-req.txt
RUN pip install --no-cache-dir -r backend-req.txt -r frontend-req.txt

COPY --chown=user backend/app backend/app
COPY --chown=user frontend/app.py frontend/app.py
COPY --chown=user data/kb data/kb
COPY --chown=user data/rag_eval.json data/rag_eval.json
COPY --chown=user scripts scripts
COPY --chown=user deploy/hf_space/nginx.conf deploy/hf_space/start.sh deploy/
RUN mkdir -p /app/data/chroma /app/data/uploads /app/.hf-cache /app/finetune/outputs && chown -R user /app

USER user
# Bake model weights into the image so the first request is fast (set WARMUP=0 to skip).
ARG WARMUP=1
RUN if [ "$WARMUP" = "1" ]; then python scripts/warmup.py; fi

EXPOSE 7860
CMD ["bash", "deploy/start.sh"]
