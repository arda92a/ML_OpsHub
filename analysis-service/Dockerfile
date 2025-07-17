# ---------------- Dockerfile (analysis-service) ----------------
FROM python:3.11.9

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY . .

# PYTHONPATH ayarı
ENV PYTHONPATH=/app

