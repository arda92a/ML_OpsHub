import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

BADGE_STYLE = """
    background-color: #f0f2f6;
    border-radius: 12px;
    padding: 18px 0 10px 0;
    margin-bottom: 10px;
    font-size: 1.3em;
    font-weight: bold;
    color: #333;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
"""

def show_data_analysis(backend_result, df: pd.DataFrame):
    """Tüm veri analizi sekmelerini ve yönlendirmesini yönetir."""
    data = backend_result.get("data_analysis", {})
    suggestions = backend_result.get("preprocessing_suggestions", [])

    tab_titles = [
        "Özet",
        "Eksik Değerler",
        "Benzersiz Değerler",
        "Önerilen Önişleme",
        "Histogramlar",
        "Boxplot",
        "Kategorik Grafikler",
        "Korelasyon Matrisi"
    ]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        show_summary_tab(data, df)
    with tabs[1]:
        show_missing_tab(data, df)
    with tabs[2]:
        show_unique_tab(data)
    with tabs[3]:
        show_suggestions_tab(suggestions)
    with tabs[4]:
        show_histograms_tab(data, df)
    with tabs[5]:
        show_boxplot_tab(data, df)
    with tabs[6]:
        show_categorical_tab(data, df)
    with tabs[7]:
        show_correlation_tab(df)


# --- Sekme Fonksiyonları ---
def show_summary_tab(data, df):
    """Veri özeti ve veri türü dağılımı sekmesi."""
    st.markdown("<h2 style='color:#1565c0; font-weight:800; margin-bottom:0.2em;'>Veri Özeti 📂</h2>", unsafe_allow_html=True)
    st.info("Veri setinizin temel istatistiksel özetini ve yapısını burada görebilirsiniz.")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div style="{BADGE_STYLE}">Satır<br>{data.get("shape", [0, 0])[0]}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div style="{BADGE_STYLE}">Sütun<br>{data.get("shape", [0, 0])[1]}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div style="{BADGE_STYLE}">Eksik Değerli Sütun<br>{sum([v > 0 for v in data.get("missing_values", {}).values()])}</div>', unsafe_allow_html=True)
    with st.expander("Sütunlar ve Tipleri", expanded=False):
        st.dataframe(pd.DataFrame({"Sütun": data.get("columns", []), "Tip": list(data.get("data_types", {}).values())}), use_container_width=True)
    show_dtype_pie(df)

def show_missing_tab(data, df):
    """Eksik değerler sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Eksik Değerler ❓</h2>", unsafe_allow_html=True)
    st.info("Veri setinizdeki eksik değerlerin dağılımını ve görselini inceleyin.")
    missing = data.get("missing_values", {})
    if any(v > 0 for v in missing.values()):
        with st.expander("Eksik Değer Tablosu", expanded=True):
            st.dataframe(pd.DataFrame(missing.items(), columns=["Sütun", "Eksik Adet"]), use_container_width=True)
        st.markdown("<h3 style='color:#2196f3; font-weight:700; margin-bottom:0.2em;'>Eksik Değer Isı Haritası</h3>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(min(12, 1+len(df.columns)*0.5), 2))
        sns.heatmap(df.isnull(), cbar=False, yticklabels=False, cmap="viridis", ax=ax)
        st.pyplot(fig)
    else:
        st.success("Eksik değer yok!")

def show_unique_tab(data):
    """Benzersiz değerler sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Benzersiz Değerler 🔢</h2>", unsafe_allow_html=True)
    st.info("Her sütunda kaç farklı değer olduğunu burada görebilirsiniz.")
    with st.expander("Benzersiz Değer Tablosu", expanded=False):
        unique = data.get("unique_values", {})
        st.dataframe(pd.DataFrame(unique.items(), columns=["Sütun", "Benzersiz Adet"]), use_container_width=True)

def show_suggestions_tab(suggestions):
    """Önerilen önişleme sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Önerilen Önişleme Adımları 🛠️</h2>", unsafe_allow_html=True)
    st.info("Veri setiniz için önerilen önişleme adımlarını burada bulabilirsiniz.")
    for sug in suggestions:
        st.warning(sug)

def show_histograms_tab(data, df):
    """Sayısal sütunlar için histogram sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Sayısal Sütunlar - Histogramlar 📊</h2>", unsafe_allow_html=True)
    st.info("Sayısal sütunların dağılımını inceleyin. Birden fazla sütun seçebilirsiniz.")
    num_cols = data.get("numeric_columns", [])
    if num_cols:
        selected = st.multiselect("Histogramını görmek istediğiniz sütunlar", num_cols, default=num_cols[:3])
        n_cols = 3
        rows = (len(selected) + n_cols - 1) // n_cols
        for i in range(rows):
            cols = st.columns(n_cols)
            for j in range(n_cols):
                idx = i * n_cols + j
                if idx < len(selected):
                    col = selected[idx]
                    with cols[j]:
                        fig = px.histogram(
                            df, x=col, nbins=30, title=f"{col} Dağılımı",
                            template="plotly_white",
                            color_discrete_sequence=["#636EFA"],
                            opacity=0.85
                        )
                        fig.update_layout(
                            title_font_size=18,
                            xaxis_title=col,
                            yaxis_title="Adet",
                            font=dict(size=15),
                            margin=dict(l=20, r=20, t=40, b=20),
                            bargap=0.1
                        )
                        fig.update_traces(hovertemplate=f"{col}: %{{x}}<br>Adet: %{{y}}<extra></extra>")
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sayısal sütun yok.")

def show_boxplot_tab(data, df):
    """Sayısal sütunlar için boxplot sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Sayısal Sütunlar - Boxplot (Plotly) 📦</h2>", unsafe_allow_html=True)
    st.info("Sayısal sütunların dağılımını ve aykırı değerlerini boxplot ile inceleyin.")
    num_cols = data.get("numeric_columns", [])
    if num_cols:
        selected = st.multiselect("Boxplot görmek istediğiniz sütunlar", num_cols, default=num_cols[:3])
        fig = go.Figure()
        palette = px.colors.qualitative.Plotly
        for i, col in enumerate(selected):
            fig.add_trace(go.Box(
                y=df[col],
                name=col,
                boxmean='sd',
                marker_color=palette[i % len(palette)],
                boxpoints='all',
                jitter=0.5,
                pointpos=0,
                line=dict(width=2),
                fillcolor=palette[i % len(palette)],
                opacity=0.7
            ))
        fig.update_layout(
            boxmode='group',
            height=600,
            margin=dict(l=60, r=60, t=60, b=60),
            font=dict(size=18),
            template='plotly_white',
            title_text="Seçili Sütunlar için Boxplot",
            title_font_size=20
        )
        fig.update_traces(hovertemplate="Değer: %{y}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sayısal sütun yok.")

def show_categorical_tab(data, df):
    """Kategorik sütunlar için grafik sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Kategorik Sütunlar - Grafikler 🥧📊</h2>", unsafe_allow_html=True)
    st.info("Kategorik sütunların dağılımını pie veya bar chart ile inceleyin. Birden fazla sütun seçebilirsiniz.")
    cat_cols = data.get("categorical_columns", [])
    if cat_cols:
        selected = st.multiselect("Grafik görmek istediğiniz kategorik sütunlar", cat_cols, default=cat_cols[:4])
        chart_type = st.radio("Grafik Tipi", ["Pie Grafikler", "Bar Grafikler"], horizontal=True)
        palette = px.colors.qualitative.Pastel
        n_cols = 3
        for i in range(0, len(selected), n_cols):
            cols = st.columns(n_cols)
            for j, col in enumerate(selected[i:i+n_cols]):
                with cols[j]:
                    vc_full = df[col].value_counts()
                    n_classes = len(vc_full)
                    vc = vc_full.copy()
                    if chart_type == "Pie Grafikler":
                        max_pie_cats = 6
                        if len(vc) > max_pie_cats:
                            top_cats = vc.iloc[:max_pie_cats]
                            other_sum = vc.iloc[max_pie_cats:].sum()
                            vc = pd.concat([top_cats, pd.Series({'Diğer': other_sum})])
                        fig = px.pie(
                            values=vc.values, names=vc.index, title=f"{col} Pie Chart",
                            template="plotly_white",
                            color_discrete_sequence=palette,
                            hole=0.4
                        )
                        fig.update_traces(
                            textinfo='percent+label',
                            marker=dict(line=dict(color='#fff', width=2)),
                            hovertemplate=f"{col}: %{{label}}<br>Adet: %{{value}}<extra></extra>",
                        )
                        fig.update_layout(
                            showlegend=True,
                            legend_title_text=col,
                            font=dict(size=13),
                            margin=dict(l=10, r=120, t=40, b=10),
                            title_font_size=16,
                            height=400,
                            legend=dict(
                                orientation="v",
                                yanchor="middle",
                                y=0.5,
                                xanchor="left",
                                x=1.05,
                                font=dict(size=11)
                            ),
                            annotations=[dict(text=f"Toplam<br>{int(vc.sum())}", x=0.5, y=0.5, font_size=14, showarrow=False)]
                        )
                        if len(vc_full) > 8:
                            st.warning(f"{col} sütununda çok fazla kategori var. Pie chart yerine bar chart ile daha iyi analiz edebilirsiniz.")
                        st.plotly_chart(fig, use_container_width=True)
                    elif chart_type == "Bar Grafikler":
                        fig = px.bar(
                            x=vc_full.index, y=vc_full.values, labels={'x':col, 'y':'Adet'},
                            title=f"{col} Bar Chart",
                            template="plotly_white",
                            color=vc_full.index,
                            color_discrete_sequence=palette
                        )
                        fig.update_layout(
                            font=dict(size=15),
                            margin=dict(l=10, r=10, t=40, b=10),
                            title_font_size=18,
                            height=350
                        )
                        fig.update_traces(hovertemplate=f"{col}: %{{x}}<br>Adet: %{{y}}<extra></extra>")
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kategorik sütun yok.")

def show_correlation_tab(df):
    """Korelasyon matrisi sekmesi."""
    st.markdown("<h2 style='color:#1976d2; font-weight:700; margin-bottom:0.2em;'>Korelasyon Matrisi 🔗</h2>", unsafe_allow_html=True)
    st.info("Sayısal sütunlar arasındaki korelasyonları inceleyin.")
    show_correlation_heatmap(df)

# --- Yardımcı Fonksiyonlar ---
def show_dtype_pie(df):
    dtype_map = {
        'int64': 'Sayısal',
        'float64': 'Sayısal',
        'object': 'Kategorik',
        'bool': 'Boolean',
        'category': 'Kategorik',
        'datetime64[ns]': 'Tarihsel',
    }
    mapped = df.dtypes.apply(lambda x: dtype_map.get(str(x), str(x)))
    counts = mapped.value_counts()
    fig = px.pie(values=counts.values, names=counts.index, title="Veri Türü Dağılımı")
    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#fff', width=2)))
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=350, title_font_size=18)
    st.plotly_chart(fig, use_container_width=True)

def show_correlation_heatmap(df):
    num_df = df.select_dtypes(include=['number'])
    if num_df.shape[1] < 2:
        st.info("Korelasyon matrisi için en az iki sayısal sütun olmalı.")
        return
    corr = num_df.corr()
    n = corr.shape[0]
    size = min(max(120 * n, 400), 800)
    fig = px.imshow(corr, text_auto=True, aspect="auto", title="Korelasyon Matrisi")
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        width=size,
        height=size,
        title_font_size=18
    )
    left, center, right = st.columns([1,2,1])
    with center:
        st.plotly_chart(fig, use_container_width=False)
    