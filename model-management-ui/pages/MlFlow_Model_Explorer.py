# MlFlow Model Explorer
# page_icon: "⬇️"

import streamlit as st
import requests
import concurrent.futures
import json
import re
from typing import Dict, List, Any

BACKEND_URL = "http://backend-service:8002/api/mlflow"

st.title("MlFlow Model Explorer")

st.markdown("""
Easily browse and download your trained models from the MlFlow Model Explorer.
Select the problem type and model name to filter the available models.
""")

# --- Model Filter ---
col1, col2 = st.columns(2)
with col1:
    problem_type = st.selectbox("Problem Type", ["classification", "regression"], key="download_problem_type")
with col2:
    model_name_filter = st.text_input("Model Name (optional)", key="download_model_name")

def parse_metrics_string(metrics_str: str) -> Dict[str, float]:
    """Parse metrics string to dictionary"""
    try:
        
        # Try direct JSON parse first
        try:
            return json.loads(metrics_str)
        except json.JSONDecodeError:
            pass
        
        # Pattern: "key":value"nextkey" -> "key":value,"nextkey"
        fixed_json = re.sub(r'":([0-9.]+)"([a-zA-Z_]+)"', r'":\1,"\2"', metrics_str)
        
        # Remove trailing comma if exists
        fixed_json = re.sub(r',"}$', '}', fixed_json)
        
        st.write(f"Debug - Fixed JSON: {fixed_json}")
        
        try:
            parsed = json.loads(fixed_json)
            st.write(f"Debug - Successfully parsed: {parsed}")
            return parsed
        except json.JSONDecodeError:
            pass
        
        # Fallback: regex extraction
        metrics = {}
        pattern = r'"([a-zA-Z_]+)":([0-9.]+)'
        matches = re.findall(pattern, metrics_str)
        st.write(f"Debug - Regex matches: {matches}")
        
        for key, value in matches:
            try:
                metrics[key] = float(value)
            except ValueError:
                metrics[key] = value
        
        st.write(f"Debug - Final parsed metrics: {metrics}")
        return metrics
        
    except Exception as e:
        st.error(f"Error parsing metrics: {e}")
        return {}

def fetch_model_versions_and_metrics(model_name: str) -> Dict[str, Any]:
    """Fetch versions and metrics for a single model"""
    try:
        # Fetch versions
        vresp = requests.get(f"{BACKEND_URL}/models/{model_name}", timeout=10)
        if vresp.status_code != 200:
            return {"name": model_name, "versions": [], "error": f"Failed to fetch versions: {vresp.text}"}
        
        model_info = vresp.json().get("data", {})
        versions = model_info.get("versions", [])
        algorithm_type = model_info.get("algorithm_type", None)
        
        # Fetch metrics for each version
        for version in versions:
            if isinstance(version, str):
                version = {"version": version}
            
            run_id = version.get("run_id")
            if run_id:
                try:
                    mresp = requests.get(f"{BACKEND_URL}/runs/{run_id}/metrics", timeout=10)
                    if mresp.status_code == 200:
                        metrics_data = mresp.json().get("data", {})
                        raw_metrics = metrics_data.get("metrics", {})
                        
                        st.write(f"Debug - Raw metrics data type: {type(raw_metrics)}")
                        st.write(f"Debug - Raw metrics data: {raw_metrics}")
                        
                        if isinstance(raw_metrics, str):
                            version["metrics"] = parse_metrics_string(raw_metrics)
                        elif isinstance(raw_metrics, dict):
                            version["metrics"] = raw_metrics
                        else:
                            version["metrics"] = {}
                    else:
                        version["metrics"] = {}
                except Exception as e:
                    st.error(f"Error fetching metrics for {run_id}: {e}")
                    version["metrics"] = {}
            else:
                version["metrics"] = {}
        
        return {"name": model_name, "problem_type": model_info.get("problem_type", None), "algorithm_type": algorithm_type, "versions": versions, "error": None}
    
    except Exception as e:
        return {"name": model_name, "versions": [], "error": str(e)}

def fetch_all_models_data(models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fetch all models data concurrently"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_model = {
            executor.submit(fetch_model_versions_and_metrics, model.get("name", "")): model 
            for model in models
        }
        
        enriched_models = []
        for future in concurrent.futures.as_completed(future_to_model):
            original_model = future_to_model[future]
            try:
                result = future.result()
                enriched_model = {**original_model, **result}
                enriched_models.append(enriched_model)
            except Exception as e:
                error_model = {**original_model, "versions": [], "error": str(e)}
                enriched_models.append(error_model)
    
    return enriched_models

def display_metrics(metrics: Dict[str, Any], color: str = "#1565c0"):
    """Display metrics as badges in 2-column grid, 5. metrik varsa en altta tek başına geniş badge olarak göster"""
    if not metrics:
        st.markdown("<div style='color:#888;text-align:center;padding:8px;'>No metrics available</div>", unsafe_allow_html=True)
        return
    main_metrics = [
        ("accuracy", "🎯"),
        ("precision", "🎯"),
        ("recall", "🔄"),
        ("f1_score", "📊"),
        ("roc_auc", "📈")
    ]
    available_metrics = [(k, emoji) for k, emoji in main_metrics if k in metrics]
    n = len(available_metrics)
    if n:
        # İlk 4 metrik için 2x2 grid
        grid_metrics = available_metrics[:4]
        metric_rows = [grid_metrics[i:i+2] for i in range(0, len(grid_metrics), 2)]
        for row in metric_rows:
            cols = st.columns(2)
            for idx, (k, emoji) in enumerate(row):
                metric_value = metrics[k]
                if isinstance(metric_value, (int, float)):
                    metric_value = f"{float(metric_value):.3f}"
                with cols[idx]:
                    st.markdown(
                        f"<div style='background:{color};color:#fff;padding:4px 8px;border-radius:6px;display:inline-block;margin:2px 4px;width:100%;text-align:center;'>"
                        f"{emoji} <b>{k.replace('_',' ').title()}:</b> {metric_value}</div>",
                        unsafe_allow_html=True
                    )
        # 5. metrik varsa, en alta geniş badge
        if n == 5:
            k, emoji = available_metrics[4]
            metric_value = metrics[k]
            if isinstance(metric_value, (int, float)):
                metric_value = f"{float(metric_value):.3f}"
            st.markdown(
                f"<div style='background:{color};color:#fff;padding:4px 8px;border-radius:6px;display:block;margin:2px 4px;width:100%;text-align:center;font-weight:bold;'>"
                f"{emoji} <b>{k.replace('_',' ').title()}:</b> {metric_value}</div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown("<div style='color:#888;text-align:center;padding:8px;'>No standard metrics available</div>", unsafe_allow_html=True)

def create_download_button(model_name: str, version_num: str, key_suffix: str = ""):
    """Create download button for a model version"""
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"⬇️ Download v{version_num}", key=f"download_{model_name}_{version_num}{key_suffix}"):
            with st.spinner("Downloading model..."):
                try:
                    dl_url = f"{BACKEND_URL}/models/{model_name}/version/{version_num}/download"
                    dl_resp = requests.get(dl_url, timeout=60)
                    if dl_resp.status_code == 200:
                        with col2:
                            st.download_button(
                                label="Download ZIP",
                                data=dl_resp.content,
                                file_name=f"{model_name}_v{version_num}.zip",
                                mime="application/zip",
                                key=f"dlbtn_{model_name}_{version_num}{key_suffix}"
                            )
                    else:
                        st.error(f"Download failed: {dl_resp.text}")
                except Exception as e:
                    st.error(f"Download error: {e}")

# --- Fetch Model List ---
with st.spinner("📥 Fetching available models from MLflow..."):
    try:
        resp = requests.get(f"{BACKEND_URL}/models", timeout=20)
        if resp.status_code == 200:
            models_data = resp.json().get("data", {})
            models = []
            for mtype, mlist in models_data.items():
                for m in mlist:
                    if isinstance(m, str):
                        m = {"name": m}
                    m["problem_type"] = mtype
                    models.append(m)
        else:
            st.error(f"Failed to fetch models: {resp.text}")
            models = []
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        models = []

# --- Filter Models ---
filtered_models = []
for m in models:
    if m.get("problem_type") != problem_type:
        continue
    
    if model_name_filter:
        model_name = m.get("name", "")
        if model_name_filter not in model_name:
            continue
    
    filtered_models.append(m)

if not filtered_models:
    if model_name_filter:
        st.info(f"No models found matching '{model_name_filter}' in {problem_type} category.")
        available_models = [m.get("name", "") for m in models if m.get("problem_type") == problem_type]
        if available_models:
            st.write(f"Available {problem_type} models:", ", ".join(available_models))
    else:
        st.info(f"No {problem_type} models found.")
else:
    # --- Fetch All Model Details ---
    with st.spinner(f"🔄 Loading detailed information for {len(filtered_models)} models..."):
        enriched_models = fetch_all_models_data(filtered_models)
    
    st.success(f"✅ Successfully loaded {len(enriched_models)} models!")
    
    st.subheader("Available Models")
    grid_cols = st.columns(4)
    
    for idx, model in enumerate(enriched_models):
        with grid_cols[idx % 4]:
            with st.container(border=True):
                # Model header
                algorithm_type = model.get('algorithm_type', '-')
                problem_type_str = model.get('problem_type', '-')
                if algorithm_type and algorithm_type != '-':
                    type_display = f"{problem_type_str} / {algorithm_type}"
                else:
                    type_display = problem_type_str
                st.markdown(f"<div style='font-size:1.2em;font-weight:700;margin-bottom:0.2em;'>🤖 <span style='color:#1565c0'>{model.get('name', '-')}", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:1em;margin-bottom:0.5em;'>🔖 <b>Type:</b> {problem_type_str}</div>", unsafe_allow_html=True)
                
                # Check for errors
                if model.get("error"):
                    st.error(f"Error loading model: {model['error']}")
                    continue
                
                versions = model.get("versions", [])
                
                if not versions:
                    st.info("No versions found for this model.")
                else:
                    # Show first 2 versions
                    versions_to_show = versions[:2] if len(versions) > 2 else versions
                    remaining_versions = versions[2:] if len(versions) > 2 else []
                    
                    # Display first 2 versions
                    for v in versions_to_show:
                        if isinstance(v, str):
                            v = {"version": v}
                        vnum = v.get("version", "-")
                        
                        st.markdown(f"<div style='background:#e3f2fd;color:#1565c0;padding:8px;border-radius:8px;margin-bottom:8px;border:1px solid #1565c0;'><b>🗂️ Version: {vnum}</b></div>", unsafe_allow_html=True)
                        
                        # Display metrics
                        metrics = v.get("metrics", {})
                        if "metrics" in metrics and isinstance(metrics["metrics"], dict):
                            metrics = metrics["metrics"]
                        display_metrics(metrics)
                        
                        # Versiyonun algorithm_type'ı (model_type)
                        algorithm_type_v = None
                        if isinstance(metrics, dict):
                            params = metrics.get("params", {})
                            if isinstance(params, dict):
                                algorithm_type_v = params.get("model_type", None)
                        if algorithm_type_v:
                            st.markdown(f"<div style='font-size:0.95em;color:#333;margin-bottom:2px;'><b>Algorithm:</b> {algorithm_type_v}</div>", unsafe_allow_html=True)
                        
                        # Download button
                        create_download_button(model.get('name', ''), vnum)
                        
                        st.markdown("<hr style='margin:10px 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
                    
                    # Show remaining versions in expander
                    if remaining_versions:
                        with st.expander(f"Show {len(remaining_versions)} more versions"):
                            for v in remaining_versions:
                                if isinstance(v, str):
                                    v = {"version": v}
                                vnum = v.get("version", "-")
                                
                                st.markdown(f"<div style='background:#e3f2fd;color:#1565c0;padding:8px;border-radius:8px;margin-bottom:8px;border:1px solid #1565c0;'><b>🗂️ Version: {vnum}</b></div>", unsafe_allow_html=True)
                                
                                # Display metrics
                                metrics = v.get("metrics", {})
                                if "metrics" in metrics and isinstance(metrics["metrics"], dict):
                                    metrics = metrics["metrics"]
                                display_metrics(metrics, "#0d47a1")
                                
                                # Versiyonun algorithm_type'ı (model_type)
                                algorithm_type_v = None
                                if isinstance(metrics, dict):
                                    params = metrics.get("params", {})
                                    if isinstance(params, dict):
                                        algorithm_type_v = params.get("model_type", None)
                                if algorithm_type_v:
                                    st.markdown(f"<div style='font-size:0.95em;color:#333;margin-bottom:2px;'><b>Algorithm:</b> {algorithm_type_v}</div>", unsafe_allow_html=True)
                                
                                # Download button
                                create_download_button(model.get('name', ''), vnum, "_exp")
                                
                                st.markdown("<hr style='margin:10px 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)