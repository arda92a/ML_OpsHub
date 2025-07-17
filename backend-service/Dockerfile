FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY wait-for-mlflow.sh /wait-for-mlflow.sh

RUN chmod +x /wait-for-mlflow.sh

EXPOSE 8002

ENTRYPOINT ["/wait-for-mlflow.sh"]

CMD ["uvicorn", "src.api.ml_api_server:app", "--host", "0.0.0.0", "--port", "8002"] 