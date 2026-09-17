import streamlit as st
import streamlit.components.v1 as components


def inject_custom_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        .stButton>button {
            width: 100%;
            border: 1px solid #E2E8F0 !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            min-height: 2.75rem;
        }
        .stButton>button:hover {
            border-color: #2563EB !important;
            color: #2563EB !important;
        }
        div[data-testid="stImage"] img,
        div[data-testid="stPlotlyChart"] {
            border: 1px solid #E2E8F0;
            border-radius: 6px;
        }
        </style>
    """, unsafe_allow_html=True)


def render_hide_gif():
    components.html(
        '''
        <div class="tenor-gif-embed" data-postid="2197628697126723655"
             data-share-method="host" data-aspect-ratio="1" data-width="100%">
            <a href="https://tenor.com/view/hide-hides-hiding-ded-hide-me-gif-2197628697126723655">Hide Hides GIF</a>
            from <a href="https://tenor.com/search/hide-gifs">Hide GIFs</a>
        </div>
        <script type="text/javascript" async src="https://tenor.com/embed.js"></script>
        ''',
        height=360,
    )


def render_home_page(navigate_callback):
    inject_custom_css()

    st.markdown("<h1 style='margin-bottom: 1rem;'>Double Random Phase Encoding</h1>", unsafe_allow_html=True)

    st.subheader("Image processing")
    if st.button("Encrypt image", use_container_width=True):
        navigate_callback('encrypt')
    if st.button("Decrypt image", use_container_width=True):
        navigate_callback('decrypt')
    if st.button("Analyze encryption", use_container_width=True):
        navigate_callback('analysis')

    st.subheader("Audio processing")
    if st.button("Encrypt audio", use_container_width=True):
        navigate_callback('audio_encrypt')
    if st.button("Decrypt audio", use_container_width=True):
        navigate_callback('audio_decrypt')

    st.subheader("Color tools")
    if st.button("RGB color encryption", use_container_width=True):
        navigate_callback('color')

