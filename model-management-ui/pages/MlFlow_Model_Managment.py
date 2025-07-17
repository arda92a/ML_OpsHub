import streamlit as st
import requests
import json

# Başarı mesajı flag'i kontrolü
if st.session_state.get('model_uploaded_success', False):
    st.success("✅ Model uploaded successfully! 🎉")
    del st.session_state['model_uploaded_success']

st.title("MLflow Model Management")
st.markdown("""
<style>
.mlflow-upload-title {
    font-size: 1.2em;
    font-weight: 600;
    color: #fff;
    margin-bottom: 1em;
    background: none;
    padding: 0;
    border-radius: 0;
    display: block;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="mlflow-upload-title">📦 Upload New Model</div>', unsafe_allow_html=True)
form_cols = st.columns([1,1])
with form_cols[0]:
    model_file = st.file_uploader("📁 Model File (.pkl, .joblib)", type=["pkl", "joblib"], key="mlflow_model_file")
    dataset_name = st.text_input("🗂️ Dataset/Project Name", key="mlflow_dataset_name")
    model_name = st.text_input("🏷️ Model Name", key="mlflow_model_name")
with form_cols[1]:
    problem_type = st.selectbox("🧩 Problem Type", ["classification", "regression"], key="mlflow_problem_type")
    CLASSIFICATION_MODELS = [
        "Random Forest", "Gradient Boosting", "Logistic Regression", "Support Vector Machine", "K-Nearest Neighbors", "Decision Tree", "XGBoost", "LightGBM", "Extra Trees"
    ]
    REGRESSION_MODELS = [
        "Linear Regression", "Ridge Regression", "Lasso Regression", "ElasticNet", "Random Forest Regressor", "Gradient Boosting Regressor", "Support Vector Regressor", "K-Nearest Neighbors Regressor", "Decision Tree Regressor", "XGBoost Regressor", "LightGBM Regressor", "Extra Trees Regressor"
    ]
    if problem_type == "classification":
        model_options = CLASSIFICATION_MODELS
    else:
        model_options = REGRESSION_MODELS
    model_type = st.selectbox("🤖 Model Type", model_options, key="mlflow_model_type")
# Metric sending option
send_metrics = st.checkbox("Send metrics", value=True, key="mlflow_send_metrics")

if send_metrics:
    st.markdown('<div style="margin-bottom:0.5em;font-weight:500;">📊 Model Metrics</div>', unsafe_allow_html=True)
    metric_grid = st.columns(4)
    with metric_grid[0]:
        accuracy = st.number_input("Accuracy", min_value=0.0, max_value=1.0, step=0.0001, format="%0.4f", key="mlflow_acc")
    with metric_grid[1]:
        precision = st.number_input("Precision", min_value=0.0, max_value=1.0, step=0.0001, format="%0.4f", key="mlflow_prec")
    with metric_grid[2]:
        recall = st.number_input("Recall", min_value=0.0, max_value=1.0, step=0.0001, format="%0.4f", key="mlflow_rec")
    with metric_grid[3]:
        f1 = st.number_input("F1", min_value=0.0, max_value=1.0, step=0.0001, format="%0.4f", key="mlflow_f1")
if 'model_uploading' not in st.session_state:
    st.session_state['model_uploading'] = False
submit = st.button("🚀 Upload Model to MLflow", key="mlflow_model_upload_btn")
if submit:
    if not model_file or not model_name or not model_type or not problem_type or not dataset_name:
        st.error("Please enter the model file, model name, model type, problem type, and dataset name.")
    else:
        st.session_state['model_uploading'] = True
if st.session_state.get('model_uploading', False):
    with st.spinner('🔄 Uploading model, please wait...'):
        try:
            files = {"file": (model_file.name, model_file.getvalue())}
            data = {
                "model_name": model_name,
                "model_type": model_type,
                "problem_type": problem_type,
                "data_file_name": dataset_name
            }
            if send_metrics:
                metrics = {}
                if accuracy > 0: metrics["accuracy"] = accuracy
                if precision > 0: metrics["precision"] = precision
                if recall > 0: metrics["recall"] = recall
                if f1 > 0: metrics["f1_score"] = f1
                # Send metrics under evaluation_metrics key
                data["metrics"] = json.dumps({"evaluation_metrics": metrics})
            resp = requests.post(
                "http://ml-service:8001/api/mlflow/submit-model",
                files=files,
                data=data,
                timeout=60
            )
            if resp.status_code == 200:
                cache_key = f'report_cache_{dataset_name}'
                cache_content_key = f'report_content_cache_{dataset_name}'
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                if cache_content_key in st.session_state:
                    del st.session_state[cache_content_key]
                st.session_state['model_uploaded_success'] = True
                st.session_state['model_uploading'] = False
                st.rerun()
            else:
                st.error(f"Upload failed: {resp.text}")
        except Exception as e:
            st.error(f"Upload error: {e}")
        st.session_state['model_uploading'] = False 