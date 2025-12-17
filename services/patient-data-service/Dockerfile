FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first (needed by all services)
COPY shared /app/shared

# Copy requirements and install Python dependencies
COPY services/patient-data-service/requirements.txt .
RUN pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt || \
    (echo "Retrying pip install after timeout..." && \
     sleep 5 && \
     pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt)

# Copy application code
COPY services/patient-data-service /app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

