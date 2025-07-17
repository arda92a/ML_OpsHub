#!/bin/sh
# mlflow servisi hazır olana kadar bekle
until curl -sSf http://mlflow:5000 > /dev/null; do
  echo "[wait-for-mlflow] mlflow:5000 bekleniyor..."
  sleep 2
done
exec "$@" 