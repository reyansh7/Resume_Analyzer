# Production Dockerfile for Render (no GPU, Gemini handles LLM)
# Uses CPU-only PyTorch — image is ~800MB vs ~6GB for CUDA variant

FROM python:3.11-slim

WORKDIR /app

# System deps for scikit-learn, spacy, sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  build-essential \
  libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# Install CPU-only Python deps
COPY requirements.prod.txt ./
RUN pip install --upgrade pip setuptools wheel \
  && pip install --no-cache-dir -r requirements.prod.txt \
  && python -m spacy download en_core_web_sm

# Copy application code
COPY app ./app

# Copy saved models (resume classifier)
COPY saved_models ./saved_models

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

EXPOSE 8000

# Non-root user
RUN useradd -m -u 1001 python_user && chown -R python_user:python_user /app
USER python_user

# Disable HF LLM — Gemini handles everything
ENV USE_HF_LLM=false \
  USE_OLLAMA_ENHANCEMENTS=false \
  PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
