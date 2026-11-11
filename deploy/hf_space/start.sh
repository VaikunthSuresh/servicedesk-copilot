#!/usr/bin/env bash
# Starts API, loads the knowledge base, starts UI, then nginx in the foreground.
set -euo pipefail
cd /app

# Free Spaces storage is ephemeral: rebuild the vector store from data/kb on every boot.
python scripts/ingest_kb.py || echo "WARN: KB ingest failed (continuing)"

(cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1) &
API_URL=http://127.0.0.1:8000 streamlit run frontend/app.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true \
  --server.enableCORS false --server.enableXsrfProtection false --browser.gatherUsageStats false --client.toolbarMode minimal &

for i in $(seq 1 120); do
  python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>/dev/null && break
  sleep 1
done
echo "API up. Starting nginx on :7860"
exec nginx -c /app/deploy/nginx.conf -g 'daemon off;'
