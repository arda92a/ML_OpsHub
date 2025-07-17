import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def safe_float(val):
    try:
        if val is None or (isinstance(val, str) and val.lower() == "none"):
            return np.nan
        return float(val)
    except (TypeError, ValueError):
        return np.nan

def get_label(idx, orig_labels=None):
    try:
        int_idx = int(idx)
        if orig_labels and int_idx < len(orig_labels):
            return str(orig_labels[int_idx])
        else:
            return str(idx)
    except Exception:
        return str(idx)

def model_training_step(df: pd.DataFrame, target_column: str, original_file_name: str = None):
    st.markdown("""
        <h1 style='color:#1565c0; font-size:2.3em; font-weight:800; margin-bottom:0.2em;'>3. Adım: Model Eğitimi ve MLflow Kaydı</h1>
    """, unsafe_allow_html=True)
    st.write("Aşağıdaki ayarlarla model(ler) eğitmek için seçimlerinizi yapın.")

    # Veri kaynağı olarak session_state'teki önişlenmiş veriyi kullan
    if st.session_state.get('preprocessed_data') is not None:
        df = st.session_state['preprocessed_data']
        target_column = st.session_state.get('preprocessed_target', target_column)

    # Parametreler grid/kart yapısı
    col1, col2 = st.columns(2)
    with col1:
        test_size = st.number_input("📊 Test set oranı (0-1)", min_value=0.05, max_value=0.95, value=0.2, step=0.01, format="%0.2f", help="Verinin ne kadarı test için ayrılacak?")
        use_random_state = st.checkbox("Random State kullan", value=False, help="Rastgelelik için seed değeri kullanmak istiyorsanız işaretleyin.")
        random_state = ""
        if use_random_state:
            random_state = st.text_input("🎲 Random State", value="", help="Rastgelelik için seed değeri. Boş bırakılırsa rastgelelik sabitlenmez.")
        model_name = st.text_input("📝 Model adı (MLflow'da kaydedilecek)", value="my_model", help="MLflow'da modelin kaydedileceği isim.")
    with col2:
        problem_type = st.selectbox("🔍 Problem tipi", options=["classification", "regression"], help="Sınıflandırma mı regresyon mu?")
        # Model haritaları (kullanıcıya gösterilecek isimler ve backend kodları)
        CLASSIFICATION_MODELS = {
            "Random Forest": "random_forest",
            "Gradient Boosting": "gradient_boosting",
            "Logistic Regression": "logistic_regression",
            "Support Vector Machine": "svm",
            "K-Nearest Neighbors": "knn",
            "Decision Tree": "decision_tree",
            "XGBoost": "xgboost",
            "LightGBM": "lightgbm",
            "Extra Trees": "extra_trees"
        }
        REGRESSION_MODELS = {
            "Linear Regression": "linear_regression",
            "Ridge Regression": "ridge",
            "Lasso Regression": "lasso",
            "ElasticNet": "elasticnet",
            "Random Forest Regressor": "random_forest_regressor",
            "Gradient Boosting Regressor": "gradient_boosting_regressor",
            "Support Vector Regressor": "svr",
            "K-Nearest Neighbors Regressor": "knn_regressor",
            "Decision Tree Regressor": "decision_tree_regressor",
            "XGBoost Regressor": "xgboost_regressor",
            "LightGBM Regressor": "lightgbm_regressor",
            "Extra Trees Regressor": "extra_trees_regressor"
        }
        # Model seçeneklerini problem tipine göre dinamik oluştur
        if problem_type == "classification":
            model_options = list(CLASSIFICATION_MODELS.keys())
            model_map = CLASSIFICATION_MODELS
            default_models = ["Random Forest", "Gradient Boosting"]
        else:
            model_options = list(REGRESSION_MODELS.keys())
            model_map = REGRESSION_MODELS
            default_models = ["Linear Regression", "Ridge Regression"]
        # Multiselect için session_state key'i kullan (uyarı ve hata çıkmaması için)
        if 'model_labels' not in st.session_state or st.session_state.get('model_options_snapshot') != model_options:
            st.session_state['model_labels'] = default_models.copy()
            st.session_state['model_options_snapshot'] = model_options.copy()
        # Tüm modelleri seçme flag'i
        if st.session_state.get('select_all_models_flag'):
            st.session_state['model_labels'] = model_options.copy()
            st.session_state['select_all_models_flag'] = False
        model_select_col, all_models_col = st.columns([4,1])
        with model_select_col:
            model_labels = st.multiselect(
                "🤖 Eğitilecek model(ler)",
                options=model_options,
                help="Birden fazla model seçebilirsiniz.",
                key="model_labels"
            )
        with all_models_col:
            if st.button("Tüm Modelleri Seç"):
                st.session_state['select_all_models_flag'] = True
                st.rerun()
        model_labels = st.session_state['model_labels']
        model_types = [model_map[label] for label in model_labels]
        st.info(f"Seçili hedef sütun: {target_column}")

    # --- Ana metrik seçimi ---
    available_metrics = ["F1-Score", "Accuracy", "Precision", "Recall", "ROC-AUC"]
    default_metric = "F1-Score"
    metric_options = [m for m in available_metrics if m in ["F1-Score", "Accuracy", "Precision", "Recall", "ROC-AUC"]]
    selected_metric = st.selectbox(
        "En iyi modeli seçmek için ana metrik:",
        options=metric_options,
        index=metric_options.index(default_metric) if default_metric in metric_options else 0,
        help="En iyi modeli belirlemek için kullanılacak ana metrik."
    )

    # Model eğitimi sonrası sonuçları session_state'te sakla ve göster
    def show_model_results(result, model_name):
        st.success("Model(ler) başarıyla eğitildi ve MLflow'a kaydedildi!")
        results = result.get("results", [])
        # --- Backend model kodunu display name'e çeviren harita ---
        backend_to_display = {}
        backend_to_display.update({v: k for k, v in CLASSIFICATION_MODELS.items()})
        backend_to_display.update({v: k for k, v in REGRESSION_MODELS.items()})
        # --- En iyi modeli bul ---
        metric_map = {
            "F1-Score": "f1_score",
            "Accuracy": "accuracy",
            "Precision": "precision",
            "Recall": "recall",
            "ROC-AUC": "roc_auc"
        }
        metric_key = metric_map.get(selected_metric, "f1_score")
        best_idx, best_score = None, None
        for i, res in enumerate(results):
            if res.get("error"):
                continue
            m = res.get("metrics", {})
            score = m.get(metric_key)
            if score is not None:
                if best_score is None or score > best_score:
                    best_score = score
                    best_idx = i
        # Tab başlıklarını display name ile oluştur, en iyi modele 🏆 ekle
        tab_titles = ["Karşılaştırma"]
        for i, res in enumerate(results):
            if res.get("error"):
                continue
            display_name = backend_to_display.get(res.get("model_type", "Model"), res.get("model_type", "Model"))
            if i == best_idx:
                tab_titles.append(f"🏆 {display_name}")
            else:
                tab_titles.append(display_name)
        tabs = st.tabs(tab_titles)
        # --- Karşılaştırma Tabı ---
        with tabs[0]:
            # En iyi model kutusu
            if best_idx is not None:
                best_res = results[best_idx]
                best_name = backend_to_display.get(best_res.get("model_type", "Model"), best_res.get("model_type", "Model"))
                best_val = best_res.get("metrics", {}).get(metric_key, None)
                st.markdown(f"""
                    <div style='background:#e3f2fd;border-left:6px solid #1976d2;padding:16px 18px 10px 18px;margin-bottom:18px;border-radius:10px;display:flex;align-items:center;gap:18px;'>
                        <span style='font-size:2.1em;'>🏆</span>
                        <div>
                            <span style='font-size:1.2em;font-weight:700;color:#1565c0;'>En İyi Model: {best_name}</span><br>
                            <span style='font-size:1.1em;color:#1976d2;font-weight:600;'>{selected_metric}: {best_val:.4f}</span>
                        </div>
                        <div style='margin-left:auto;display:flex;gap:10px;'>
                            <a href='#" + best_name.replace(" ", "_") + "_download' style='background:#1976d2;color:white;padding:8px 18px;border-radius:6px;text-decoration:none;font-weight:600;font-size:1em;'>Modeli İndir</a>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            metrics_list = []
            for res in results:
                if res.get("error"):
                    continue
                m = res.get("metrics", {})
                m_flat = {
                    "Model": res.get("model_type"),
                    "Accuracy": safe_float(m.get("accuracy")),
                    "Precision": safe_float(m.get("precision")),
                    "Recall": safe_float(m.get("recall")),
                    "F1-Score": safe_float(m.get("f1_score")),
                    "ROC-AUC": safe_float(m.get("roc_auc")),
                }
                metrics_list.append(m_flat)
            if metrics_list:
                df_metrics = pd.DataFrame(metrics_list)
                float_cols = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
                styler = df_metrics.style
                for col in float_cols:
                    if col in df_metrics.columns:
                        styler = styler.format({col: "{:.4f}"}, na_rep="-")
                st.dataframe(styler, use_container_width=True)
                st.markdown("""
                    <h2 style='color:#1976d2; font-size:1.5em; font-weight:700; margin-top:1.2em;'>Model Metrik Karşılaştırma Grafiği</h2>
                """, unsafe_allow_html=True)
                metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC"]
                fig = go.Figure()
                for i, row in df_metrics.iterrows():
                    fig.add_trace(go.Bar(
                        x=metric_names,
                        y=[row[m] if not pd.isna(row[m]) else 0 for m in metric_names],
                        name=row["Model"],
                        text=[f"{row[m]:.3f}" if not pd.isna(row[m]) else "-" for m in metric_names],
                        textposition='auto',
                        marker=dict(line=dict(width=1), opacity=0.85)
                    ))
                fig.update_layout(
                    barmode='group',
                    template='plotly_white',
                    title="Tüm Modellerin Metrik Karşılaştırması",
                    xaxis_title="Metrik",
                    yaxis_title="Skor",
                    legend_title="Model",
                    font=dict(size=15),
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- Her Model için Detay Sekmeleri ---
        for idx, res in enumerate(results):
            if res.get("error"):
                continue
            m = res.get("metrics", {})
            model_type = res.get("model_type")
            mlflow_model_name = res.get("mlflow_model_name") or model_name
            model_version = res.get("model_version")
            class_labels = res.get("class_labels")
            display_name = backend_to_display.get(model_type, model_type)
            with tabs[idx+1]:
                # En iyi model sekmesinde bilgi kutusu
                if idx == best_idx:
                    st.info(f"🏆 Bu model {selected_metric} değerine göre en iyi sonucu verdi.")
                st.markdown(f"<h3 style='color:#1976d2; font-weight:700; margin-top:0.8em;'>{display_name} Modeli Detayları</h3>", unsafe_allow_html=True)
                if res.get("error"):
                    st.error(f"{res.get('model_type')} için hata: {res['error']}")
                if model_version is not None and mlflow_model_name is not None:
                    # Dosya ismini model_name ve model_type ile oluştur (sadece algoritma adı)
                    safe_model_name = mlflow_model_name.replace(" ", "_").replace("/", "_")
                    safe_model_type = (model_type or "model").replace(" ", "_").replace("/", "_")
                    zip_filename = f"{safe_model_name}_{safe_model_type}.zip"
                    st.markdown(f"<div style='display:flex;justify-content:flex-end;margin-bottom:10px;'>"
                                f"<a href='http://localhost:8002/api/mlflow/models/{mlflow_model_name}/version/{model_version}/download' "
                                f"download='{zip_filename}' "
                                f"style='background:#007bff;color:white;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:1.1em;'>"
                                f"⬇️ Modeli İndir (zip)"
                                f"</a></div>", unsafe_allow_html=True)
                elif mlflow_model_name is not None:
                    st.warning("Model dosyası henüz kaydedilmedi veya MLflow'da bulunamadı.")
                # Metrik kartları
                center_cols = st.columns([1, 2, 1])
                with center_cols[1]:
                    st.markdown("<div style='display:flex;gap:12px;margin-bottom:10px;justify-content:center;'>" +
                        f"<div style='background:#f0f2f6;padding:10px 18px;border-radius:8px;min-width:120px;text-align:center;color:#222;'><b>Accuracy</b><br><span style='font-size:1.2em;font-weight:600;color:#222'>{safe_float(m.get('accuracy')):.3f}</span></div>" +
                        f"<div style='background:#f0f2f6;padding:10px 18px;border-radius:8px;min-width:120px;text-align:center;color:#222;'><b>Precision</b><br><span style='font-size:1.2em;font-weight:600;color:#222'>{safe_float(m.get('precision')):.3f}</span></div>" +
                        f"<div style='background:#f0f2f6;padding:10px 18px;border-radius:8px;min-width:120px;text-align:center;color:#222;'><b>Recall</b><br><span style='font-size:1.2em;font-weight:600;color:#222'>{safe_float(m.get('recall')):.3f}</span></div>" +
                        f"<div style='background:#f0f2f6;padding:10px 18px;border-radius:8px;min-width:120px;text-align:center;color:#222;'><b>F1-Score</b><br><span style='font-size:1.2em;font-weight:600;color:#222'>{safe_float(m.get('f1_score')):.3f}</span></div>" +
                        f"<div style='background:#f0f2f6;padding:10px 18px;border-radius:8px;min-width:120px;text-align:center;color:#222;'><b>ROC-AUC</b><br><span style='font-size:1.2em;font-weight:600;color:#222'>{safe_float(m.get('roc_auc')):.3f}</span></div>" +
                        "</div>", unsafe_allow_html=True)
                # Confusion Matrix
                if m.get("confusion_matrix") is not None:
                    cm = np.array(m["confusion_matrix"])
                    n_classes = cm.shape[0]
                    # Orijinal class label'ları session_state'ten al
                    orig_labels = st.session_state.get('original_class_labels')
                    if orig_labels and len(orig_labels) == n_classes:
                        labels = [get_label(i, orig_labels) for i in range(n_classes)]
                    else:
                        labels = [str(i) for i in range(n_classes)]
                    size = max(500, 100 * n_classes)
                    fig_cm = go.Figure(data=go.Heatmap(
                        z=cm,
                        x=labels,
                        y=labels,
                        colorscale='Blues',
                        showscale=True,
                        hoverongaps=False,
                        text=cm,
                        texttemplate="<b>%{text}</b>",
                        colorbar=dict(title="Adet")
                    ))
                    fig_cm.update_layout(
                        title="Confusion Matrix",
                        xaxis_title="Tahmin",
                        yaxis_title="Gerçek",
                        font=dict(size=16, family="Segoe UI,Arial,sans-serif"),
                        width=size,
                        height=size,
                        margin=dict(l=40, r=40, t=60, b=40),
                        xaxis=dict(
                            scaleanchor="y",
                            scaleratio=1,
                            constrain='domain',
                            tickmode='array',
                            tickvals=labels,
                            ticktext=labels
                        ),
                        yaxis=dict(
                            scaleanchor="x",
                            scaleratio=1,
                            constrain='domain',
                            tickmode='array',
                            tickvals=labels,
                            ticktext=labels
                        )
                    )
                    fig_cm.update_xaxes(tickfont=dict(size=16))
                    fig_cm.update_yaxes(tickfont=dict(size=16))
                    st.plotly_chart(fig_cm, use_container_width=True)
                # Classification Report
                if m.get("classification_report") is not None:
                    st.markdown("""
                        <h4 style='color:#2196f3; font-weight:700; margin-top:0.8em;'>Classification Report</h4>
                    """, unsafe_allow_html=True)
                    # Parse classification report string to DataFrame
                    cr = m["classification_report"]
                    import re
                    if isinstance(cr, dict):
                        cr_df = pd.DataFrame(cr).T
                    else:
                        lines = [l for l in cr.split('\n') if l.strip()]
                        header = re.split(r'\s{2,}', lines[0].strip())
                        data = [re.split(r'\s{2,}', l.strip()) for l in lines[1:] if len(re.split(r'\s{2,}', l.strip())) == len(header)]
                        cr_df = pd.DataFrame(data, columns=header)
                        cr_df.set_index(cr_df.columns[0], inplace=True)
                    # Sadece sayısal kolonları float'a çevir
                    for col in cr_df.columns:
                        try:
                            cr_df[col] = cr_df[col].astype(float)
                        except Exception:
                            pass
                    # Sadece sınıf satırlarını al (accuracy, macro avg, weighted avg hariç)
                    class_rows = [idx for idx in cr_df.index if idx not in ["accuracy", "macro avg", "weighted avg"]]
                    # Orijinal class label'ları session_state'ten al
                    orig_labels = st.session_state.get('original_class_labels')
                    if class_rows:
                        plot_df = cr_df.loc[class_rows, [c for c in ["precision", "recall", "f1-score"] if c in cr_df.columns]]
                        # indexleri orijinal label'a çevir
                        plot_df.index = [get_label(idx, orig_labels) for idx in plot_df.index]
                        fig = go.Figure()
                        for metric in plot_df.columns:
                            fig.add_trace(go.Bar(
                                x=plot_df.index,
                                y=plot_df[metric],
                                name=metric.capitalize(),
                                text=[f"{v:.3f}" for v in plot_df[metric]],
                                textposition="auto"
                            ))
                        fig.update_layout(
                            barmode="group",
                            title="Sınıf Bazında Precision / Recall / F1-Score",
                            xaxis_title="Sınıf",
                            yaxis_title="Skor",
                            legend_title="Metrik",
                            font=dict(size=15),
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20)
                        )
                        st.plotly_chart(fig, use_container_width=True)

    # --- Model eğitimi butonu ---
    # Problem tipi ve hedef sütun uyumluluğu kontrolü
    target_is_numeric = pd.api.types.is_numeric_dtype(df[target_column])
    n_unique = df[target_column].nunique()
    classification_problem = (problem_type == "classification")
    regression_problem = (problem_type == "regression")
    classification_like = target_is_numeric and n_unique <= 20  # ör: 20'den az unique değer
    regression_like = target_is_numeric and n_unique > 20
    categorical_like = not target_is_numeric or df[target_column].dtype == object
    allow_train = True
    if classification_problem and regression_like:
        st.warning(f"Seçili hedef sütun sürekli bir değişken (ör. sayısal ve çok fazla farklı değer içeriyor). Lütfen sınıflandırma için kategorik bir sütun seçin veya problem tipini 'regression' olarak değiştirin.")
        allow_train = False
    if regression_problem and (categorical_like or (target_is_numeric and n_unique <= 10)):
        st.warning(f"Seçili hedef sütun kategorik görünüyor (az sayıda farklı değer veya metin). Lütfen regresyon için sürekli bir sütun seçin veya problem tipini 'classification' olarak değiştirin.")
        allow_train = False
    if st.button("Model(leri) Eğit ve MLflow'a Kaydet"):
        if not allow_train:
            st.stop()
        csv_buffer = df.to_csv(index=False).encode("utf-8")
        file_name = original_file_name if original_file_name else "data.csv"
        files = {"data_file": (file_name, csv_buffer, "text/csv")}
        data = {
            "model_name": model_name,
            "model_type": model_types,
            "test_size": str(test_size),
            "target_column": target_column,
            "problem_type": problem_type,
            "data_file_name": file_name
        }
        if use_random_state and random_state.strip() != "":
            data["random_state"] = random_state.strip()
        with st.spinner("Model(ler) eğitiliyor, lütfen bekleyin..."):
            response = requests.post(
                "http://analysis-service:8000/api/models/train-model",
                files=files,
                data=data
            )
        if response.status_code == 200:
            result = response.json()
            st.session_state['last_model_results'] = (result, model_name)
            show_model_results(result, model_name)
        else:
            st.error(f"Backend hata döndürdü: {response.text}")
    # --- Sonuçları session_state'ten göster ---
    elif st.session_state.get('last_model_results'):
        result, model_name = st.session_state['last_model_results']
        show_model_results(result, model_name)

# Dosya yükleme adımında:
# uploaded_file = st.file_uploader(...)
# if uploaded_file is not None:
#     df = pd.read_csv(uploaded_file)
#     st.session_state['original_file_name'] = uploaded_file.name
#     ...
#
# Model eğitim adımında:
# model_training_step(df, target_column, original_file_name=st.session_state.get('original_file_name'))
#
# model_training_step fonksiyonu zaten original_file_name parametresini kullanıyor. 
