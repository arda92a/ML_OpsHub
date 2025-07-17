import streamlit as st

st.set_page_config(page_title="SmartEM UI", layout="wide")

# Başlık ve hoşgeldin
st.markdown("""
<div style='text-align:center; margin-top: 2rem;'>
    <h1 style='font-size:2.8rem; color:#1565c0; font-weight:800; margin-bottom:0.5em;'>Welcome to <span style='color:#764ba2;'>SmartEM</span> Platform 🚀</h1>
    <p style='font-size:1.3rem; color:#607d8b; max-width:700px; margin:auto; font-weight:500;'>
        SmartEM is an integrated platform for managing, analyzing, and reporting your machine learning models and data science projects. Easily upload, track, and download models, manage your reports, and monitor your ML workflow—all in one place.
    </p>
</div>
""", unsafe_allow_html=True)

# Bölüm kartları
st.markdown("""
<div style='display:flex; justify-content:center; gap:2.5rem; margin-top:2.5rem; flex-wrap:wrap;'>
    <div style='background:linear-gradient(135deg,#e3f2fd 0%,#f3e7fa 100%); border-radius:18px; box-shadow:0 4px 18px rgba(118,75,162,0.08); padding:2.2rem 2rem; min-width:320px; max-width:370px; margin-bottom:1.5rem;'>
        <h2 style='color:#1565c0; font-size:1.4rem; margin-bottom:0.7em;'>
            <span style='font-size:1.7rem;'>⬇️</span> MlFlow Model Explorer
        </h2>
        <p style='color:#333; font-size:1.08rem;'>
            Browse, filter, and download your trained ML models. View model versions, metrics, and algorithm details in a modern dashboard.
        </p>
    </div>
    <div style='background:linear-gradient(135deg,#f3e7fa 0%,#e3f2fd 100%); border-radius:18px; box-shadow:0 4px 18px rgba(118,75,162,0.08); padding:2.2rem 2rem; min-width:320px; max-width:370px; margin-bottom:1.5rem;'>
        <h2 style='color:#764ba2; font-size:1.4rem; margin-bottom:0.7em;'>
            <span style='font-size:1.7rem;'>📤</span> Model Management
        </h2>
        <p style='color:#333; font-size:1.08rem;'>
            Upload new models to MLflow, specify their type and metrics, and keep your model registry organized and up-to-date.
        </p>
    </div>
    <div style='background:linear-gradient(135deg,#e3f2fd 0%,#f3e7fa 100%); border-radius:18px; box-shadow:0 4px 18px rgba(118,75,162,0.08); padding:2.2rem 2rem; min-width:320px; max-width:370px; margin-bottom:1.5rem;'>
        <h2 style='color:#1565c0; font-size:1.4rem; margin-bottom:0.7em;'>
            <span style='font-size:1.7rem;'>📑</span> Report Management
        </h2>
        <p style='color:#333; font-size:1.08rem;'>
            Upload, view, and manage your project reports (PDF). Download or delete reports with a single click in a visually rich interface.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Ekstra: Kullanıcıya rehberlik
st.markdown("""
<div style='margin:2.5rem auto 0; max-width:800px; background:#fffbe7; border-radius:14px; padding:1.5rem 2rem; box-shadow:0 2px 10px rgba(255,193,7,0.08);'>
    <h3 style='color:#ff9800; font-size:1.15rem; margin-bottom:0.7em;'>How to use SmartEM?</h3>
    <ul style='font-size:1.08rem; color:#444; line-height:1.7;'>
        <li><b>MlFlow Model Explorer:</b> Go to the <i>MlFlow Model Explorer</i> page to explore and download your models, view their metrics and algorithm types.</li>
        <li><b>Model Management:</b> Use the <i>Model Management</i> page to upload new models, set their type, and add evaluation metrics.</li>
        <li><b>Report Management:</b> Manage your project reports, upload new ones, and keep your documentation organized.</li>
    </ul>
    <div style='margin-top:1.2em; color:#888;'>Tip: Use the sidebar to navigate between sections.</div>
</div>
""", unsafe_allow_html=True)

# Hafif animasyon (isteğe bağlı, varsa eklenti)
try:
    from streamlit_extras.let_it_rain import rain
    LET_IT_RAIN_AVAILABLE = True
except ImportError:
    LET_IT_RAIN_AVAILABLE = False

if LET_IT_RAIN_AVAILABLE:
    try:
        rain(emoji="💡", font_size=24, falling_speed=5, animation_length="short")
    except Exception:
        pass