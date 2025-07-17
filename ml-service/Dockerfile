# ---------------- Dockerfile (ml-service) ----------------
FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY ./src ./src
COPY wait-for-mlflow.sh /wait-for-mlflow.sh
RUN chmod +x /wait-for-mlflow.sh

# PYTHONPATH ayarı
ENV PYTHONPATH=/app/src

# Port'u expose et
EXPOSE 8001

# Başlangıç komutu
ENTRYPOINT ["/wait-for-mlflow.sh"]
CMD ["uvicorn", "api.ml_api_server:app", "--host", "0.0.0.0", "--port", "8001"]