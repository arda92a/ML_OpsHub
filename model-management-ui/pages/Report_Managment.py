import streamlit as st
import requests
import re
import concurrent.futures

def show_report_upload():
    st.write("Only PDF files can be uploaded. Please enter the name of the dataset/project the report belongs to.")
    with st.form("report_upload_form"):
        dataset_name = st.text_input("Dataset/Project Name", help="The dataset or project name the report belongs to.")
        report_name = st.text_input("Report Name", help="The name of the report you will upload (without extension).")
        uploaded_file = st.file_uploader("Select PDF Report", type=["pdf"])
        submit = st.form_submit_button("🚀 Upload", use_container_width=True)
    
    if submit:
        if not dataset_name or not report_name or not uploaded_file:
            st.warning("⚠️ Please fill in all fields and select a PDF file.")
            return None
        
        with st.spinner("📤 Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            data = {"report_name": report_name, "dataset_name": dataset_name}
            try:
                response = requests.post(
                    "http://analysis-service:8000/api/upload-report",
                    files=files,
                    data=data,
                    timeout=30
                )
                if response.status_code == 200:
                    st.success("✅ Report uploaded successfully!")
                    st.session_state["report_uploaded"] = dataset_name
                    # Clear cache so the new report appears
                    cache_key = f'report_cache_{dataset_name}'
                    cache_content_key = f'report_content_cache_{dataset_name}'
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                    if cache_content_key in st.session_state:
                        del st.session_state[cache_content_key]
                    # Refresh the page
                    st.rerun()
                else:
                    st.error(f"❌ Upload failed: {response.text}")
            except Exception as e:
                st.error(f"🚫 An error occurred: {e}")
    return None

# Sayfa konfigürasyonu
st.set_page_config(page_title="MinIO Report Management", page_icon="��", layout="wide")

# CSS stilleri
st.markdown("""
    <style>
    /* Ana container stilleri */
    .main-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 2rem;
    }
    
    /* Başlık stilleri */
    .main-title {
        color: #2c3e50;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 3.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Kart stilleri */
    .upload-card, .reports-card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Form butonları */
    .stButton > button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Aksiyon butonları */
    .action-btn-delete {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a52 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 10px rgba(255, 107, 107, 0.3) !important;
        width: 100% !important;
    }
    
    .action-btn-download {
        background: linear-gradient(45deg, #4ecdc4 0%, #44a08d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 10px rgba(78, 205, 196, 0.3) !important;
        width: 100% !important;
    }
    
    .action-btn-delete:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4) !important;
    }
    
    .action-btn-download:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 15px rgba(78, 205, 196, 0.4) !important;
    }
    
    /* Rapor kartları */
    .stContainer[style*="border: 1px solid"] {
        background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%) !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
        border: 1px solid #e9ecef !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stContainer[style*="border: 1px solid"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.12) !important;
    }
    
    /* Seçim kutuları */
    .stCheckbox > label {
        font-weight: 600 !important;
        color: #2c3e50 !important;
    }
    
    /* Toplu aksiyon butonları */
    .bulk-action-delete button {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a52 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3) !important;
        width: 100% !important;
    }
    
    .bulk-action-download button {
        background: linear-gradient(45deg, #4ecdc4 0%, #44a08d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3) !important;
        width: 100% !important;
    }
    
    .bulk-action-delete button:hover,
    .bulk-action-download button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
    }
    
    /* Selectbox stilleri */
    .stSelectbox > div > div {
        background: white !important;
        border-radius: 10px !important;
        border: 2px solid #e9ecef !important;
        transition: all 0.3s ease !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Selectbox ve text input yazı rengi düzeltme */
    .stSelectbox > div > div,
    .stTextInput > div > div {
        color: #2c3e50 !important;
    }
    .stSelectbox .css-1wa3eu0-placeholder,
    .stSelectbox .st-c6,
    .stSelectbox .st-dg,
    .stSelectbox .st-bx {
        color: #2c3e50 !important;
    }
    
    /* İndirme butonları */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #4ecdc4 0%, #44a08d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        font-size: 0.85rem !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(78, 205, 196, 0.3) !important;
    }
    
    /* Disabled butonlar */
    .stButton > button:disabled {
        background: #dee2e6 !important;
        color: #6c757d !important;
        cursor: not-allowed !important;
        transform: none !important;
    }
    
    /* Başlık ikonları */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        color: #fff !important;
        font-weight: 700;
        font-size: 2.2rem !important;
        letter-spacing: 0.5px;
        text-shadow: 1px 1px 8px rgba(0,0,0,0.12);
    }
    
    /* Animasyonlar */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .upload-card, .reports-card {
            padding: 1rem;
        }
    }
    /* Selectbox arka planını defaulta döndür */
    .stSelectbox > div > div {
        background: inherit !important;
    }
    /* Seçili değerin yazı rengi beyaz */
    .stSelectbox > div > div > div[data-baseweb="select"] > div {
        color: #fff !important;
        font-weight: 700 !important;
    }
    /* Selectbox içindeki yazı (seçili değer ve placeholder) beyaz olsun */
    .stSelectbox > div > div,
    .stSelectbox .css-1wa3eu0-placeholder,
    .stSelectbox .st-c6,
    .stSelectbox .st-dg,
    .stSelectbox .st-bx {
        color: #fff !important;
    }
    .stButton > button,
    .stButton > button *,
    .stDownloadButton > button,
    .stDownloadButton > button * {
        font-size: 0.8rem !important;
    }
    .stButton > button {
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

col_upload, col_reports = st.columns([1, 2], gap="large")

# --- RAPOR YÜKLEME ---
with col_upload:
    #st.markdown('<div class="upload-card fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📤 Upload New Report</div>', unsafe_allow_html=True)
    show_report_upload()
    st.markdown('</div>', unsafe_allow_html=True)

# --- RAPOR GÖRÜNTÜLEME ---
with col_reports:
    #st.markdown('<div class="reports-card fade-in">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📋 Uploaded Reports</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#fff;font-size:1.1rem;margin-bottom:1.5rem;">In this section, you can view, download, or delete the reports you have uploaded.</div>', unsafe_allow_html=True)
    
    try:
        resp = requests.get("http://analysis-service:8000/api/list-datasets", timeout=10)
        datasets = resp.json().get("datasets", [])
    except Exception as e:
        st.error(f"🚫 Datasets could not be retrieved: {e}")
        datasets = []

    if not datasets:
        st.info("📂 No dataset/project found. Please upload a report first.")
    else:
        dataset = st.selectbox("🗂️ Select Dataset/Project", datasets)
        if dataset:
            cache_key = f'report_cache_{dataset}'
            cache_content_key = f'report_content_cache_{dataset}'
            
            # Cache kontrol ve yükleme
            if cache_key not in st.session_state:
                with st.spinner('🔄 Reports are loading...'):
                    try:
                        resp = requests.get(f"http://analysis-service:8000/api/list-reports/{dataset}", timeout=10)
                        reports = resp.json().get("reports", [])
                        
                        def fetch_content(report):
                            m = re.match(r"(.+)_v(\d+)\.pdf", report)
                            if not m:
                                return (report, None, None, None)
                            report_name, version = m.group(1), int(m.group(2))
                            data = {"name": report_name, "version": version, "dataset_name": dataset}
                            try:
                                download_resp = requests.post(
                                    "http://analysis-service:8000/api/download-report",
                                    json=data,
                                    timeout=30
                                )
                                if download_resp.status_code == 200:
                                    return (report, report_name, version, download_resp.content)
                                else:
                                    return (report, report_name, version, None)
                            except Exception:
                                return (report, report_name, version, None)
                        
                        report_contents = []
                        if reports:
                            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                                results = list(executor.map(fetch_content, reports))
                                report_contents = results
                        
                        st.session_state[cache_key] = reports
                        st.session_state[cache_content_key] = report_contents
                    except Exception as e:
                        st.error(f"🚫 Reports could not be retrieved: {e}")
                        st.session_state[cache_key] = []
                        st.session_state[cache_content_key] = []
            else:
                reports = st.session_state[cache_key]
                report_contents = st.session_state[cache_content_key]

            if not reports:
                st.info("📄 There are no reports for this dataset.")
            else:
                selected_reports = []
                
                # Toplu aksiyon butonları
                action_cols = st.columns([1, 1])
                with action_cols[0]:
                    st.markdown('<div class="bulk-action-delete">', unsafe_allow_html=True)
                    delete_all = st.button("🗑️ Delete Selected Reports", key="delete_selected", 
                                         help="Delete selected reports in bulk")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with action_cols[1]:
                    st.markdown('<div class="bulk-action-download">', unsafe_allow_html=True)
                    multi_download = st.button("📦 Download Selected Reports (ZIP)", key="multi_download", 
                                             help="Download selected reports as a single zip file")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                
                # Rapor kartları
                num_cols = 3
                rows = [report_contents[i:i+num_cols] for i in range(0, len(report_contents), num_cols)]
                
                for row in rows:
                    cols = st.columns(num_cols)
                    for idx in range(num_cols):
                        if idx < len(row):
                            report, report_name, version, file_content = row[idx]
                            if report_name is None:
                                with cols[idx]:
                                    st.error("⚠️ Invalid report name format!")
                                continue
                            
                            # Session state kontrolü
                            if f"select_{report}" not in st.session_state:
                                st.session_state[f"select_{report}"] = False
                            
                            with cols[idx]:
                                with st.container(border=True):
                                    # Üst kısım - seçim ve başlık
                                    top_cols = st.columns([1, 4])
                                    with top_cols[0]:
                                        checked = st.checkbox(" ", key=f"select_{report}", label_visibility="collapsed")
                                        if checked:
                                            selected_reports.append((report, report_name, version))
                                    
                                    with top_cols[1]:
                                        st.markdown(f"**📄 {report_name[:15] + ('...' if len(report_name) > 15 else '')}** (_v{version}_)" )
                                       
                                    
                                    #st.markdown("---")
                                    
                                    # Aksiyon butonları
                                    btn_cols = st.columns(2)
                                    with btn_cols[0]:
                                        if file_content:
                                            st.download_button(
                                                label="📥 DOWNLOAD",
                                                data=file_content,
                                                file_name=f"{report_name}_v{version}.zip",
                                                mime="application/zip",
                                                key=f"download_{report}",
                                                use_container_width=True
                                            )
                                        else:
                                            st.button("❌ ERROR", key=f"fail_{report}", 
                                                    disabled=True, use_container_width=True)
                                    
                                    with btn_cols[1]:
                                        delete_btn = st.button("🗑️ DELETE", key=f"delete_{report}", 
                                                             use_container_width=True)
                                        if delete_btn:
                                            delete_data = {
                                                "name": report_name, 
                                                "version": version, 
                                                "dataset_name": dataset
                                            }
                                            try:
                                                del_resp = requests.post(
                                                    "http://analysis-service:8000/api/delete-report",
                                                    json=delete_data,
                                                    timeout=15
                                                )
                                                if del_resp.status_code == 200:
                                                    # Cache'i temizle
                                                    if cache_key in st.session_state:
                                                        del st.session_state[cache_key]
                                                    if cache_content_key in st.session_state:
                                                        del st.session_state[cache_content_key]
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ Delete failed: {del_resp.text}")
                                            except Exception as e:
                                                st.error(f"🚫 Delete error: {e}")
                
                # Toplu işlemler
                if delete_all and selected_reports:
                    success_count = 0
                    with st.spinner("🗑️ Deleting selected reports..."):
                        for report, report_name, version in selected_reports:
                            delete_data = {
                                "name": report_name, 
                                "version": version, 
                                "dataset_name": dataset
                            }
                            try:
                                del_resp = requests.post(
                                    "http://analysis-service:8000/api/delete-report",
                                    json=delete_data,
                                    timeout=15
                                )
                                if del_resp.status_code == 200:
                                    success_count += 1
                            except Exception:
                                pass
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count} report(s) deleted successfully!", icon="🗑️")
                        # Cache'i temizle
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        if cache_content_key in st.session_state:
                            del st.session_state[cache_content_key]
                        st.rerun()
                
                if multi_download and selected_reports:
                    report_payload = [
                        {"name": name, "version": version, "dataset_name": dataset}
                        for _, name, version in selected_reports
                    ]
                    try:
                        with st.spinner("📦 ZIP file is preparing..."):
                            resp = requests.post(
                                "http://analysis-service:8000/api/download-multi-reports",
                                json={"reports": report_payload},
                                timeout=60
                            )
                            if resp.status_code == 200:
                                st.download_button(
                                    label="📥 DOWNLOAD ZIP",
                                    data=resp.content,
                                    file_name=f"{dataset}_reports.zip",
                                    mime="application/zip",
                                    key="multi_zip_download",
                                    use_container_width=True
                                )
                                st.success("✅ ZIP file is ready!")
                            else:
                                st.error("❌ ZIP file could not be retrieved.")
                    except Exception as e:
                        st.error(f" ZIP download error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)