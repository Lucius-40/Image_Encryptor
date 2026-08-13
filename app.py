import streamlit as st
from view.encrypt_view import render_encrypt_tab
from view.decrypt_view import render_decrypt_tab
from view.analysis_view import render_analysis_tab
from view.color_view import render_color_tab

st.set_page_config(page_title="DRPE Image Encryptor", layout="wide", page_icon="🔐")

st.title("🔐 Lucius Khawa Encryptor")
st.write("Upload an image to Make it Erling Haaland")

# Initialize session state so keys don't vanish when the user clicks a button
if 'key1' not in st.session_state:
    st.session_state['key1'] = None
if 'key2' not in st.session_state:
    st.session_state['key2'] = None

# App Routing
tab1, tab2, tab3, tab4 = st.tabs(["Lock (Encrypt)", "Unlock (Decrypt)", "Analysis ", "Color (RGB)"])

with tab1:
    render_encrypt_tab()

with tab2:
    #st.info("Decryption view coming next.")
    render_decrypt_tab()

with tab3:
    render_analysis_tab()

with tab4:
    render_color_tab()