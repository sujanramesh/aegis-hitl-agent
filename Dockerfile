FROM python:3.13-slim

# Prevent Python from writing .pyc files and force logs
# directly to stdout/stderr for container observability.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies separately so Docker can cache this layer.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source and operational knowledge.
COPY app ./app
COPY knowledge ./knowledge

# FastAPI listens on port 8000 inside the container.
EXPOSE 8000

# Public health endpoint used by Docker/AWS health checks.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]