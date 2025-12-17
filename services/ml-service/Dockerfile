FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first (needed by all services)
COPY shared /app/shared

# Copy requirements
COPY services/ml-service/requirements.txt .
# Add timeout and retry for large downloads (PyTorch ~2GB)
RUN pip install --no-cache-dir --timeout=600 --retries=3 -r requirements.txt || \
    (echo "Retrying pip install after timeout..." && \
     sleep 10 && \
     pip install --no-cache-dir --timeout=600 --retries=3 -r requirements.txt)

# Copy application code
COPY services/ml-service /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

