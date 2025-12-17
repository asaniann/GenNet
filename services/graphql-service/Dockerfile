FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy shared directory first (needed by all services)
COPY shared /app/shared

# Copy requirements
COPY services/graphql-service/requirements.txt .
RUN pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt || \
    (echo "Retrying pip install after timeout..." && \
     sleep 5 && \
     pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt)

# Copy application code
COPY services/graphql-service /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

