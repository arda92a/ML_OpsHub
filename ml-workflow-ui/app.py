import streamlit as st
import pandas as pd
from ui.data_upload import upload_data
from ui.data_analysis import show_data_analysis
from ui.preprocessing import preprocessing_step
from ui.model_training import model_training_step

st.set_page_config(page_title="SmartEM Veri Analiz Platformu", layout="wide")
st.markdown("""
    <h1 style='color:#1565c0; font-size:2.5em; font-weight:900; margin-bottom:0.2em;'>Veri Analiz ve Modelleme Platformu</h1>
""", unsafe_allow_html=True)

backend_result, df = upload_data()
if backend_result is not None and df is not None:
    show_data_analysis(backend_result, df)
    st.markdown("---")
    preprocessing_step(df)
    if (
        ('preprocessed_data' in st.session_state and st.session_state['preprocessed_data'] is not None and
         'preprocessed_target' in st.session_state and st.session_state['preprocessed_target'] is not None)
        or
        ('processed_df' in st.session_state and st.session_state['processed_df'] is not None and
         'target_column' in st.session_state and st.session_state['target_column'] is not None)
    ):
        st.markdown("---")
        if 'preprocessed_data' in st.session_state and st.session_state['preprocessed_data'] is not None:
            model_training_step(
                st.session_state['preprocessed_data'],
                st.session_state['preprocessed_target'],
                original_file_name=st.session_state.get('original_file_name')
            )
        else:
            model_training_step(
                st.session_state['processed_df'],
                st.session_state['target_column'],
                original_file_name=st.session_state.get('original_file_name')
            ) 