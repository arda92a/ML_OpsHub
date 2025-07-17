# ml-service

MLflow tabanlı model yönetimi, izleme ve model kaydı için mikroservis.

## Temel Özellikler
- **Model Kaydı:** Eğitimli modelleri MLflow ile kaydeder ve versiyonlar.
- **Model İzleme:** Model metriklerini, parametrelerini ve geçmişini izler.
- **REST API:** Model yükleme, sorgulama ve metrik erişimi için API sunar.
- **MLflow UI:** Web arayüzü ile model geçmişini ve detaylarını görselleştirir.

## Klasör Yapısı
- `src/api/` : Model kaydı, metrik sorgulama ve sağlık kontrolü API'leri
- `src/services/` : MLflow istemcisi ve model işlemleri
- `src/utils/` : Loglama ve yardımcı fonksiyonlar
- `src/config/` : Servis konfigürasyonu

## Örnek API Kullanımı
- **Model Kaydı:**
  - `POST /api/mlflow/submit-model` : Model dosyasını ve metriklerini yükleyin.
- **Model Metrikleri:**
  - `GET /api/mlflow/runs/{run_id}/metrics` : Modelin metriklerini alın.

Tüm API uç noktaları ve detaylar için: [http://localhost:8001/docs](http://localhost:8001/docs)

## Kullanım
Servis, model-management-ui ve backend-service tarafından otomatik olarak kullanılır. MLflow arayüzü: [http://localhost:5000](http://localhost:5000) 