FROM python:3.11-slim

WORKDIR /app

# System deps needed by torch/transformers wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend

# Pre-download the model at build time so the container starts instantly
# and never has a slow/failing first request.
RUN python backend/prefetch_model.py

# Hugging Face Spaces expects the app on port 7860; other hosts (Render,
# Railway) inject their own $PORT and this falls back to 7860 if unset.
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "gunicorn --chdir backend --bind 0.0.0.0:${PORT} --workers 1 --timeout 120 app:app"]
