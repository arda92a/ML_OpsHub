import streamlit as st
import pandas as pd
import requests
import json

def preprocessing_step(df: pd.DataFrame):
    st.markdown("""
        <h1 style='color:#1565c0; font-size:2.1em; font-weight:800; margin-bottom:0.2em;'>2. Adım: Veri Önişleme</h1>
    """, unsafe_allow_html=True)
    st.write("Yüklediğiniz veri üzerinde önişleme adımlarını seçin ve uygulayın.")

    col1, col2 = st.columns(2)
    with col1:
        drop_cols = st.multiselect("🗑️ Kaldırılacak sütunlar", options=list(df.columns), help="Veri setinden çıkarmak istediğiniz sütunları seçin.")
        df_proc = df.drop(columns=drop_cols) if drop_cols else df.copy()
        imputation_method = st.selectbox(
            "🧩 Eksik değer doldurma", options=["median", "mean", "most_frequent", "knn"],
            help="Eksik değerleri doldurmak için kullanılacak yöntemi seçin."
        )
        scaling_method = st.selectbox(
            "📏 Ölçekleme yöntemi", options=["standard", "minmax", "robust", "none"],
            help="Sayısal değişkenler için ölçekleme yöntemi."
        )
        encoding_method = st.selectbox(
            "🔤 Encoding yöntemi", options=["auto", "onehot", "label"],
            help="Kategorik değişkenler için encoding yöntemi."
        )
    with col2:
        target_column = st.selectbox("🎯 Hedef sütun", options=list(df_proc.columns), help="Modelde tahmin edilecek hedef değişken.")
        st.session_state['target_column'] = target_column
        st.session_state['original_class_labels'] = list(map(str, df_proc[target_column].unique()))

    with st.expander("Gelişmiş Ayarlar", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            handle_outliers = st.checkbox("🚨 Aykırı değer işle (IQR/Z-score)", help="Aykırı değerleri tespit edip işlemek için seçin.")
            outlier_method = st.selectbox("Aykırı değer yöntemi", options=["iqr", "zscore"], disabled=not handle_outliers, help="Aykırı değerleri tespit etme yöntemi.")
            feature_selection = st.checkbox("🧠 Öznitelik seçimi uygula", help="En iyi öznitelikleri otomatik seçmek için işaretleyin.")
            n_features = st.number_input("Seçilecek öznitelik sayısı (auto için 0 girin)", min_value=0, max_value=len(df_proc.columns), value=0, step=1, disabled=not feature_selection, help="Kaç öznitelik seçileceğini belirtin.")
        with c2:
            pca_apply = st.checkbox("📊 PCA uygula", help="Boyut indirgeme için PCA uygula.")
            pca_components = st.number_input("PCA bileşen sayısı (auto için 0 girin)", min_value=0, max_value=len(df_proc.columns), value=0, step=1, disabled=not pca_apply, help="Kaç PCA bileşeni kullanılacağını belirtin.")

    config = {
        "imputation_method": imputation_method,
        "scaling_method": scaling_method if scaling_method != "none" else None,
        "encoding_method": encoding_method,
        "handle_outliers": handle_outliers if 'handle_outliers' in locals() else False,
        "outlier_method": outlier_method if 'outlier_method' in locals() and handle_outliers else None,
        "feature_selection": feature_selection if 'feature_selection' in locals() else False,
        "n_features": None if 'n_features' not in locals() or n_features == 0 else n_features,
        "pca_components": None if 'pca_apply' not in locals() or not pca_apply or pca_components == 0 else pca_components
    }

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn = st.columns([2,1,2])
    with c_btn[1]:
        apply = st.button("Önişlemeyi Uygula")

    if apply:
        csv_buffer = df_proc.to_csv(index=False).encode("utf-8")
        files = {"file": ("data.csv", csv_buffer, "text/csv")}
        data = {
            "config": json.dumps(config),
            "target_column": target_column
        }
        with st.spinner("Önişleme uygulanıyor, lütfen bekleyin..."):
            response = requests.post(
                "http://analysis-service:8000/api/data/preprocess",
                files=files,
                data=data
            )
        if response.status_code == 200:
            result = response.json()
            st.session_state['preprocessing_steps'] = result["preprocessing_info"]["preprocessing_steps"]
            st.success("Önişleme başarıyla tamamlandı!")
            with st.container():
                st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>Uygulanan adımlar:</span>", unsafe_allow_html=True)
                steps = result["preprocessing_info"]["preprocessing_steps"]
                shown_steps = set()
                for step in steps:
                    if step not in shown_steps:
                        st.info(step)
                        shown_steps.add(step)
                st.markdown("<br>", unsafe_allow_html=True)
                grid_col1, grid_col2 = st.columns([4,1])
                with grid_col1:
                    st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>İşlenmiş veri:</span>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(result["processed_data"]), use_container_width=True)
                with grid_col2:
                    st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>Hedef değişken:</span>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame({"y_train": result["y_train"]}), use_container_width=True)
            processed_df = pd.DataFrame(result["processed_data"])
            processed_df[target_column] = result["y_train"]
            st.session_state['preprocessed_data'] = processed_df
            st.session_state['preprocessed_target'] = target_column
            return None
        else:
            st.error(f"Backend hata döndürdü: {response.text}")

    # Önişleme sonuçlarını her zaman göster
    if st.session_state.get('preprocessed_data') is not None:
        processed_df = st.session_state['preprocessed_data']
        target_column = st.session_state.get('preprocessed_target', None)
        st.success("Önişleme başarıyla tamamlandı!")
        with st.container():
            st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>Uygulanan adımlar:</span>", unsafe_allow_html=True)
            steps = st.session_state.get('preprocessing_steps', [])
            shown_steps = set()
            for step in steps:
                if step not in shown_steps:
                    st.info(step)
                    shown_steps.add(step)
            st.markdown("<br>", unsafe_allow_html=True)
            grid_col1, grid_col2 = st.columns([4,1])
            with grid_col1:
                st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>İşlenmiş veri:</span>", unsafe_allow_html=True)
                st.dataframe(processed_df, use_container_width=True)
            with grid_col2:
                st.markdown("<span style='font-size:1.1em;font-weight:700;color:#1976d2;'>Hedef değişken:</span>", unsafe_allow_html=True)
                if target_column:
                    st.dataframe(pd.DataFrame({target_column: processed_df[target_column]}), use_container_width=True) 