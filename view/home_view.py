from pathlib import Path

import streamlit as st


def get_intro_video_path():
    base_dir = Path(__file__).resolve().parents[1]
    gif_path = base_dir / "assets" / "side.gif"
    if gif_path.exists():
        return str(gif_path)

    video_path = base_dir / "assets" / "intro_animation.mp4"
    return str(video_path) if video_path.exists() else None


def inject_custom_css():
    st.markdown("""
        <style>
        /* 1. Hide the default Streamlit top menu and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}

        header {background: transparent !important;}
        /* 2. App-wide shell and layered panel look */
        .stApp {
            background: radial-gradient(circle at top left, rgba(57,255,20,0.08), transparent 40%),
                        linear-gradient(135deg, #030805 0%, #07150d 100%);
        }

        .block-container {
            background: rgba(5, 12, 9, 0.76);
            border: 1px solid rgba(57, 255, 20, 0.35);
            border-radius: 24px;
            padding: 2rem !important;
            margin-top: 1.5rem;
            box-shadow: 0 0 30px rgba(57, 255, 20, 0.08), inset 0 0 18px rgba(57, 255, 20, 0.04);
            backdrop-filter: blur(6px);
        }

        /* 3. Global Font Override and Glow */
        html, body, [class*="css"] {
            font-family: 'Courier New', Courier, monospace !important;
        }
        h1, h2, h3 {
            text-shadow: 0px 0px 8px rgba(57, 255, 20, 0.6);
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        /* 4. Terminal Style Buttons */
        .stButton>button {
            height: 96px;
            width: 100%;
            font-size: 20px !important;
            font-weight: bold;
            border-radius: 0px !important;
            border: 2px dashed #39FF14 !important;
            background-color: rgba(10, 20, 13, 0.7) !important;
            color: #39FF14 !important;
            transition: all 0.2s ease;
            text-transform: lowercase;
            box-shadow: inset 0 0 10px rgba(57,255,20,0.04);
        }

        .stButton>button:hover {
            background-color: #39FF14 !important;
            color: #050505 !important;
            border: 2px solid #39FF14 !important;
            box-shadow: 0px 0px 15px rgba(57, 255, 20, 0.8);
        }

        .stTextInput>div>div>input {
            border: 1px dashed #39FF14 !important;
            background-color: transparent !important;
            color: #39FF14 !important;
            border-radius: 0px !important;
        }

        /* 5. Subtle right-side motion accent */
        div[data-testid="stImage"] {
            margin: 1.2rem auto 0 auto !important;
            opacity: 0.38;
            filter: saturate(0.8) brightness(1.12);
        }
        div[data-testid="stImage"] img {
            max-width: none !important;
            width: auto !important;
            height: auto !important;
            border-radius: 12px;
            box-shadow: none;
        }
        div[data-testid="stVideo"] {
            margin: 1rem auto 0 auto !important;
            opacity: 0.32;
            filter: saturate(0.8) brightness(1.15);
            pointer-events: none;
        }
        div[data-testid="stVideo"] video {
            width: auto !important;
            max-width: none !important;
            max-height: none !important;
            border-radius: 12px;
            box-shadow: none;
        }
        div[data-testid="stVideo"] video::-webkit-media-controls-panel,
        div[data-testid="stVideo"] video::-webkit-media-controls-play-button,
        div[data-testid="stVideo"] video::-webkit-media-controls-current-time-display,
        div[data-testid="stVideo"] video::-webkit-media-controls-time-remaining-display,
        div[data-testid="stVideo"] video::-webkit-media-controls-mute-button,
        div[data-testid="stVideo"] video::-webkit-media-controls-volume-slider,
        div[data-testid="stVideo"] video::-webkit-media-controls-fullscreen-button {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
def render_intro_video():
    media_path = get_intro_video_path()
    if media_path:
        if media_path.lower().endswith('.gif'):
            st.image(media_path, use_container_width=True)
        else:
            st.video(media_path, autoplay=True, loop=True, muted=True)
    else:
        st.info("🎥 Place 'side.gif' or 'intro_animation.mp4' in the project's 'assets' folder to see the animation here.")


def render_home_page(navigate_callback):
    inject_custom_css()

    left_col, right_col = st.columns([1.8, 1.1])

    with left_col:
        st.markdown("<h1 style='margin-bottom: 1rem;'>Double Random Phase Encoding</h1>", unsafe_allow_html=True)

        st.caption("/// IMAGE PROCESSING")
        if st.button("./encrypt_signal.sh", use_container_width=True):
            navigate_callback('encrypt')
        if st.button("./decrypt_signal.sh", use_container_width=True):
            navigate_callback('decrypt')
        if st.button("./run_analysis.sh", use_container_width=True):
            navigate_callback('analysis')
            
        st.caption("/// AUDIO PROCESSING")
        if st.button("./encrypt_audio.sh", use_container_width=True):
            navigate_callback('audio_encrypt')
        if st.button("./decrypt_audio.sh", use_container_width=True):
            navigate_callback('audio_decrypt')

        st.caption("/// EXPERIMENTAL")
        if st.button("sudo enable_rgb", use_container_width=True):
            navigate_callback('color')

    with right_col:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        render_intro_video()