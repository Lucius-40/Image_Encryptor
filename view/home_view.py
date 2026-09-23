import streamlit as st
import streamlit.components.v1 as components


def inject_custom_css(is_home=False):
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
        body:has(#landing-page) {
            background: #0B1120;
        }
        body:has(#landing-page) section[data-testid="stMain"] {
            background:
                radial-gradient(circle at 82% 18%, rgba(14, 165, 233, 0.18), transparent 28rem),
                linear-gradient(135deg, #0B1120 0%, #111827 58%, #172554 100%);
        }
        body:has(#landing-page) section[data-testid="stMain"] h1 {
            color: #F8FAFC;
            letter-spacing: 0.02em;
            text-shadow: 0 0 24px rgba(56, 189, 248, 0.25);
        }
        body:has(#landing-page) section[data-testid="stMain"] p {
            color: #CBD5E1;
        }
        body:has(#landing-page) .stButton>button {
            min-height: 3.35rem;
            font-size: 1.08rem;
            font-weight: 700;
            border: 1px solid #38BDF8 !important;
            background: rgba(15, 23, 42, 0.78) !important;
            color: #E0F2FE !important;
            box-shadow: 0 8px 24px rgba(2, 132, 199, 0.16);
        }
        body:has(#landing-page) .stButton>button:hover {
            border-color: #FBBF24 !important;
            color: #FEF3C7 !important;
            background: rgba(30, 41, 59, 0.92) !important;
            box-shadow: 0 10px 28px rgba(251, 191, 36, 0.16);
        }
        body:has(#landing-page) div[data-testid="stImage"] img {
            border-color: #334155;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stImage"] img,
        div[data-testid="stPlotlyChart"] {
            border: 1px solid #E2E8F0;
            border-radius: 6px;
        }
        .empty-watermark {
            min-height: 360px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 1.5rem 0;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            background:
                linear-gradient(135deg, rgba(248, 250, 252, 0.92), rgba(241, 245, 249, 0.72)),
                repeating-linear-gradient(135deg, transparent 0 22px, rgba(148, 163, 184, 0.06) 22px 23px);
            overflow: hidden;
            text-align: center;
        }
        .empty-watermark__title {
            color: rgba(30, 41, 59, 0.15);
            font-size: clamp(2.4rem, 7vw, 6rem);
            font-weight: 800;
            letter-spacing: 0.08em;
            line-height: 0.95;
            text-transform: uppercase;
            user-select: none;
        }
        .empty-watermark__hint {
            margin-top: 1.5rem;
            color: #64748B;
            font-size: 1rem;
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

