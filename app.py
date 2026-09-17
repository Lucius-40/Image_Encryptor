import streamlit as st

# 1. Page Config MUST be first!
st.set_page_config(page_title="Optical Encryption Engine", layout="wide", initial_sidebar_state="expanded")

# Import Views
from view.home_view import inject_custom_css, render_hide_gif
from view.encrypt_view import render_encrypt_tab
from view.decrypt_view import render_decrypt_tab
from view.analysis_view import render_analysis_tab
from view.color_view import render_color_tab
from view.steganography_embed_view import render_steganography_embed_tab
from view.steganography_extract_view import render_steganography_extract_tab
from view.audio_encrypt_view import render_audio_encrypt
from view.audio_decrypt_view import render_audio_decrypt

## read the current url

url_domain = st.query_params.get("domain", "home")

if url_domain == "home" and st.session_state.get('domain') != 'home':
    st.session_state['domain'] = 'home'

if 'domain' not in st.session_state:
    st.session_state['domain'] = url_domain
if 'active_page' not in st.session_state:
    st.session_state['active_page'] = None



# 3. Navigation Callbacks
def set_domain(new_domain):
    st.session_state['domain'] = new_domain
    
    # Write the new domain to the browser URL so history is tracked
    if new_domain == 'home':
        st.query_params.clear()
    else:
        st.query_params["domain"] = new_domain
        
    # Auto-route to the first page of the selected workspace
    if new_domain == 'image':
        st.session_state['active_page'] = 'encrypt'
    elif new_domain == 'audio':
        st.session_state['active_page'] = 'audio_encrypt'
    else:
        st.session_state['active_page'] = None


def set_page(new_page):
    st.session_state['active_page'] = new_page
   
def set_page(new_page):
    st.session_state['active_page'] = new_page
   

# Apply the global light theme styling.
inject_custom_css()

# Start page
if st.session_state['domain'] == 'home':
    left_col, right_col = st.columns([1.8, 1.1])

    with left_col:
        st.markdown("<h1 style='margin-bottom: 1rem;'>Double Random Phase Encoding</h1>", unsafe_allow_html=True)
        st.write("Image and audio encryption tools for exploring double random phase encoding.")

        st.markdown("<br><br>", unsafe_allow_html=True)

        st.button("Open image tools", use_container_width=True, on_click=set_domain, args=('image',))

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        st.button("Open audio tools", use_container_width=True, on_click=set_domain, args=('audio',))

    with right_col:
        render_hide_gif()

# Workspace
else:
    st.sidebar.button("Back to start", on_click=set_domain, args=('home',), use_container_width=True)
    st.sidebar.divider()
    
    # --- IMAGE WORKSPACE ---
    if st.session_state['domain'] == 'image':
        st.sidebar.subheader("Image tools")
        st.sidebar.button("1. Encrypt", on_click=set_page, args=('encrypt',), use_container_width=True)
        st.sidebar.button("2. Decrypt", on_click=set_page, args=('decrypt',), use_container_width=True)
        st.sidebar.button("3. Analyze", on_click=set_page, args=('analysis',), use_container_width=True)
        st.sidebar.button("4. RGB Color", on_click=set_page, args=('color',), use_container_width=True)
        st.sidebar.button("5. Hide Cipher", on_click=set_page, args=('steg_embed',), use_container_width=True)
        st.sidebar.button("6. Extract Cipher", on_click=set_page, args=('steg_extract',), use_container_width=True)
        
        # Router
        if st.session_state['active_page'] == 'encrypt':
            render_encrypt_tab()
        elif st.session_state['active_page'] == 'decrypt':
            render_decrypt_tab()
        elif st.session_state['active_page'] == 'analysis':
            render_analysis_tab()
        elif st.session_state['active_page'] == 'color':
            render_color_tab()
        elif st.session_state['active_page'] == 'steg_embed':
            render_steganography_embed_tab()
        elif st.session_state['active_page'] == 'steg_extract':
            render_steganography_extract_tab()
            
    # --- AUDIO WORKSPACE ---
    elif st.session_state['domain'] == 'audio':
        st.sidebar.subheader("Audio tools")
        st.sidebar.button("1. Encrypt Audio", on_click=set_page, args=('audio_encrypt',), use_container_width=True)
        st.sidebar.button("2. Decrypt Audio", on_click=set_page, args=('audio_decrypt',), use_container_width=True)
        
        # Router
        if st.session_state['active_page'] == 'audio_encrypt':
            render_audio_encrypt()
        elif st.session_state['active_page'] == 'audio_decrypt':
            render_audio_decrypt()