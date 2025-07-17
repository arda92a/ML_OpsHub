import streamlit as st
import pandas as pd
import requests

def upload_data():
    st.markdown("""
        <div style='display:flex;align-items:center;gap:16px;margin-bottom:10px;'>
            <span style='font-size:2.2em;color:#1976d2;'>📤</span>
            <span style='font-size:1.6em;font-weight:bold;color:#1565c0;'>1. Adım: Veri Yükleme</span>
        </div>
        <div style='background:#F5FAFF;border-radius:12px;padding:18px 20px 10px 20px;margin-bottom:18px;box-shadow:0 2px 8px rgba(21,101,192,0.06);font-size:1.1em;color:#222;border:1px solid #1976d2;'>
            <span style='font-weight:500;'>Analiz ve modelleme için <b>CSV veya XLSX formatında</b> veri dosyanızı yükleyin.</span><br>
            <span style='color:#1976d2;font-weight:500;'>Veriniz güvenli bir şekilde işlenecektir.</span>
        </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Veri dosyanızı seçin (CSV veya XLSX)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            st.markdown("""
                <div style='background:#F5FAFF;border-radius:10px;padding:12px 18px;margin-bottom:10px;border:1px solid #1976d2;color:#1976d2;'>
                    <span style='font-size:1.2em;font-weight:500;'>✅ Veri başarıyla yüklendi!</span>
                </div>
            """, unsafe_allow_html=True)
            st.session_state['original_file_name'] = uploaded_file.name
            # Content type belirle
            if uploaded_file.name.endswith('.csv'):
                content_type = "text/csv"
            elif uploaded_file.name.endswith('.xlsx'):
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                content_type = "application/octet-stream"
            files = {"file": (uploaded_file.name, uploaded_file, content_type)}
            response = requests.post(
                "http://analysis-service:8000/api/data/analyze",
                files=files
            )
            if response.status_code == 200:
                result = response.json()
                st.success("Veri başarıyla analiz edildi!")
                st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>Veri Önizlemesi (ilk 10 satır):</span>", unsafe_allow_html=True)
                uploaded_file.seek(0)
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                else:
                    st.error("Sadece CSV veya XLSX dosyaları destekleniyor.")
                    return None, None
                target_col = df.columns[-1] if len(df.columns) > 0 else None
                if target_col:
                    st.session_state['original_class_labels'] = list(map(str, df[target_col].unique()))
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                return result, df
            else:
                st.error(f"Backend hata döndürdü: {response.text}")
                return None, None
        except Exception as e:
            st.error(f"Veri gönderilirken hata oluştu: {e}")
            return None, None
    else:
        st.info("Lütfen analiz için bir CSV veya XLSX dosyası yükleyin.")
        return None, None 