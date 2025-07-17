# analysis-service

Veri analizi, önişleme önerileri, model eğitimi ve rapor yönetimi için kapsamlı bir FastAPI mikroservisi.

## Temel Özellikler
- **Veri Analizi:** Yüklenen CSV/XLSX dosyalarını analiz eder, eksik değer, veri tipi ve dağılım istatistikleri sunar.
- **Önişleme Önerileri:** Otomatik önişleme adımları (eksik değer doldurma, kategorik kodlama vb.) önerir.
- **Model Eğitimi:** Eğitim, değerlendirme ve model kaydı için REST API sunar.
- **Rapor Yönetimi:** PDF rapor yükleme, listeleme ve silme işlemleri.
- **MinIO ile Entegrasyon:** Rapor ve model dosyalarını bulut tabanlı obje depolama ile yönetir.

## Klasör Yapısı
- `src/api/` : REST API uç noktaları (veri analizi, model yönetimi, rapor yönetimi)
- `src/data/` : Veri yükleme ve önişleme modülleri
- `src/models/` : Model eğitimi ve değerlendirme
- `src/services/` : Eğitim servisleri
- `src/storage/` : MinIO istemcisi
- `src/utils/` : Loglama ve yardımcı fonksiyonlar

## Örnek API Kullanımı
- **Veri Analizi:**
  - `POST /api/data/analyze` : Veri dosyasını yükleyin, analiz ve önişleme önerileri alın.
- **Model Eğitimi:**
  - `POST /api/model/train` : Model eğitimi başlatın.
- **Rapor Yükleme:**
  - `POST /api/upload-report` : PDF rapor yükleyin.

Tüm API uç noktaları ve detaylar için: [http://localhost:8000/docs](http://localhost:8000/docs)

## Kullanım
Servis, ML OpsHub platformunun veri analizi ve model eğitimi ihtiyaçlarını karşılar. Diğer UI ve backend servisleri tarafından otomatik olarak kullanılır. 