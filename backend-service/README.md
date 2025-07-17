# backend-service

ML OpsHub servisleri arasında köprü görevi gören, MLflow ve analiz servisleriyle entegre API katmanı.

## Temel Özellikler
- **MLflow Entegrasyonu:** Model geçmişi, versiyon ve metrik sorgulama API'leri
- **Rapor ve Model Yönetimi:** Model ve rapor işlemleri için merkezi API
- **Loglama ve Hata Yönetimi:** Gelişmiş loglama ve hata yönetimi

## Klasör Yapısı
- `src/api/` : MLflow ve model yönetimi API uç noktaları
- `src/services/` : MLflow istemcisi ve servis entegrasyonları
- `src/utils/` : Loglama ve yardımcı fonksiyonlar
- `src/config/` : Servis konfigürasyonu

## Örnek API Kullanımı
- **Model Bilgisi:**
  - `GET /api/mlflow/models/{model_name}` : Modelin versiyon ve algoritma bilgisi
- **Model Metrikleri:**
  - `GET /api/mlflow/runs/{run_id}/metrics` : Modelin metriklerini alın

Tüm API uç noktaları ve detaylar için: [http://localhost:8002/docs](http://localhost:8002/docs)

## Kullanım
Servis, UI katmanları tarafından otomatik olarak kullanılır. ML OpsHub platformunun merkezi entegrasyon katmanıdır. 