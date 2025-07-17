# ml-workflow-ui

Veri yükleme, analiz, önişleme ve model eğitimi için uçtan uca iş akışı sunan Streamlit tabanlı arayüz.

## Temel Özellikler
- **Veri Yükleme:** CSV/XLSX dosyalarını yükleyin, backend ile analiz ettirin.
- **Veri Analizi:** Otomatik özet, eksik değer, benzersiz değer, histogram, boxplot, kategorik grafik ve korelasyon analizi sekmeleri.
- **Önişleme:** Eksik değer doldurma, kategorik kodlama gibi önişleme adımlarını yönetin.
- **Model Eğitimi:** Farklı algoritmalarla model eğitin, sonuçları ve metrikleri görselleştirin.
- **Kapsamlı Görselleştirme:** Plotly, Matplotlib ve Seaborn ile zengin veri görselleştirmeleri.

## Modüller
- `ui/data_upload.py` : Dosya yükleme ve backend ile analiz entegrasyonu
- `ui/data_analysis.py` : Veri analizi ve görselleştirme sekmeleri
- `ui/preprocessing.py` : Önişleme adımları
- `ui/model_training.py` : Model eğitimi ve sonuç görselleştirme
- `app.py` : Ana uygulama akışı

## Kullanım
Arayüze erişim: [http://localhost:8501](http://localhost:8501)

> ML OpsHub platformunun uçtan uca veri bilimi iş akışı panelidir. 