FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    postgresql-client \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libcurl4-gnutls-dev \
    libhts-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared directory first (needed by all services)
COPY shared /app/shared

# Copy requirements
COPY services/genomic-analysis-service/requirements.txt .

# Install build dependencies first (needed for cyvcf2 and pysam)
# Add timeout and retry settings for network reliability
RUN pip install --no-cache-dir --timeout=300 --retries=3 --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --timeout=300 --retries=3 numpy "cython>=3.0.0"

# Install requirements except cyvcf2 first
RUN pip install --no-cache-dir --timeout=300 --retries=3 $(grep -v "^cyvcf2" requirements.txt | grep -v "^#" | grep -v "^$" | tr '\n' ' ') || \
    (echo "Retrying requirements installation..." && \
     sleep 5 && \
     pip install --no-cache-dir --timeout=300 --retries=3 $(grep -v "^cyvcf2" requirements.txt | grep -v "^#" | grep -v "^$" | tr '\n' ' '))

# Install cyvcf2 separately with explicit build from source
# This ensures Cython generates the .c file before compilation
RUN pip install --no-cache-dir --timeout=300 --retries=3 --no-binary cyvcf2 "cyvcf2>=0.30.0" || \
    (echo "Attempting alternative cyvcf2 installation..." && \
     sleep 5 && \
     pip install --no-cache-dir --timeout=300 --retries=3 "cyvcf2>=0.30.0")

# Copy application code
COPY services/genomic-analysis-service /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

