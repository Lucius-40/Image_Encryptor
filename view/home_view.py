import base64
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
import streamlit.components.v1 as components


ASSETS_DIR = Path(__file__).resolve().parent.parent / "app_assets"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def inject_custom_css(is_home=False):
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        .stButton>button {
            width: 100%;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            min-height: 2.75rem;
            transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease, transform 160ms ease, box-shadow 160ms ease;
        }
        .stButton>button:hover {
            border-color: #000000 !important;
            background-color: #000000 !important;
            color: #FFFFFF !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.16);
            transform: translateY(-1px);
        }
        .stButton>button:active {
            background-color: #262626 !important;
            color: #FFFFFF !important;
            transform: translateY(0);
            box-shadow: none;
        }
        .stButton>button:hover p,
        .stButton>button:hover span,
        .stButton>button:active p,
        .stButton>button:active span {
            color: #FFFFFF !important;
        }
        body:has(#landing-page) {
            background: #000000;
        }
        body:has(#landing-page) section[data-testid="stMain"] {
            background: #000000;
        }
        body:has(#landing-page) section[data-testid="stMain"] h1 {
            color: #F8FAFC;
            letter-spacing: 0.02em;
            text-shadow: 0 0 24px rgba(255, 255, 255, 0.18);
        }
        body:has(#landing-page) section[data-testid="stMain"] p {
            color: #CBD5E1;
        }
        body:has(#landing-page) .stButton>button {
            min-height: 3.35rem;
            font-size: 1.08rem;
            font-weight: 700;
            border: 1px solid #E5E5E5 !important;
            background: #F5F5F5 !important;
            color: #000000 !important;
            box-shadow: 0 8px 24px rgba(255, 255, 255, 0.08);
        }
        body:has(#landing-page) .stButton>button p,
        body:has(#landing-page) .stButton>button span {
            color: #000000 !important;
        }
        body:has(#landing-page) .stButton>button:hover {
            border-color: #FFFFFF !important;
            color: #FFFFFF !important;
            background: #262626 !important;
            box-shadow: 0 10px 28px rgba(255, 255, 255, 0.12);
        }
        body:has(#landing-page) .stButton>button:hover p,
        body:has(#landing-page) .stButton>button:hover span {
            color: #FFFFFF !important;
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
        .operation-loader {
            display: flex;
            align-items: center;
            gap: 0.9rem;
            margin: 1rem 0 1.25rem;
            padding: 0.8rem 1rem;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            background: linear-gradient(110deg, #F8FAFC, #FFFFFF, #F8FAFC);
            background-size: 200% 100%;
            animation: loader-sheen 1.6s ease-in-out infinite;
        }
        .operation-loader__media {
            display: grid;
            width: 42px;
            height: 42px;
            place-items: center;
            overflow: hidden;
            border-radius: 6px;
            background: #000000;
        }
        .operation-loader__media img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .operation-loader__message {
            flex: 1;
            color: #1E293B;
            font-size: 0.92rem;
            font-weight: 650;
        }
        .operation-loader__track {
            width: 90px;
            height: 4px;
            overflow: hidden;
            border-radius: 99px;
            background: #E2E8F0;
        }
        .operation-loader__track span {
            display: block;
            width: 45%;
            height: 100%;
            border-radius: inherit;
            background: #000000;
            animation: loader-progress 0.9s ease-in-out infinite;
        }
        @keyframes loader-sheen {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        @keyframes loader-progress {
            0% { transform: translateX(-110%); }
            100% { transform: translateX(330%); }
        }
        body:has(#landing-page) section[data-testid="stMain"] {
            min-height: 100vh;
        }
        body:has(#landing-page) .landing-copy {
            padding: 2.5rem 0 1.2rem;
            text-align: center;
        }
        body:has(#landing-page) .landing-kicker {
            color: #A3A3A3;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.2em;
            text-transform: uppercase;
        }
        body:has(#landing-page) .landing-copy h1 {
            margin: 0.6rem 0 0.8rem;
            font-size: clamp(2.2rem, 5vw, 4.8rem);
            line-height: 1.05;
        }
        body:has(#landing-page) .landing-quote {
            margin: 0;
            color: #D4D4D4 !important;
            font: italic 1.15rem/1.5 Georgia, serif;
        }
        body:has(#landing-page) .landing-intro {
            margin: 0.7rem 0 0;
            color: #A3A3A3 !important;
        }
        body:has(#landing-page) .landing-footer {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            margin: 2.2rem auto 1rem;
            padding: 1.1rem 1.4rem;
            max-width: 760px;
            border-top: 1px solid #404040;
            border-bottom: 1px solid #262626;
            color: #A3A3A3;
            text-align: center;
            font-size: 0.86rem;
        }
        body:has(#landing-page) .landing-footer strong {
            color: #E5E5E5;
            font-size: 0.9rem;
        }
        </style>
    """, unsafe_allow_html=True)


def render_hide_gif():
    render_asset_gallery()


def _thumbnail_data_url(path, size=(420, 260)):
    image = cv2.imdecode(np.frombuffer(path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return None

    target_width, target_height = size
    height, width = image.shape[:2]
    scale = max(target_width / width, target_height / height)
    resized = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    top = max((resized.shape[0] - target_height) // 2, 0)
    left = max((resized.shape[1] - target_width) // 2, 0)
    cropped = resized[top:top + target_height, left:left + target_width]
    success, encoded = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not success:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")


def _get_gallery_images():
    paths = sorted(path for path in ASSETS_DIR.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
    images = []
    for path in paths:
        try:
            data_url = _thumbnail_data_url(path)
        except OSError:
            data_url = None
        if data_url:
            images.append((path.stem.replace("_", " ").title(), data_url))
    return images


def render_asset_gallery():
    gallery_images = _get_gallery_images()
    cards = "".join(
        f"<div class='gallery-slot'><img src='{data_url}' alt='{name}' /></div>"
        for name, data_url in gallery_images
    )
    shift_count = max(len(gallery_images) - 4, 1)
    step_percent = 100 / (shift_count + 1)
    keyframes = ["0% { transform: translateX(0); }", f"{step_percent * 0.78:.2f}% {{ transform: translateX(0); }}"]
    for index in range(1, shift_count + 1):
        start = step_percent * index
        previous = -236 * (index - 1)
        current = -236 * index
        keyframes.append(f"{start:.2f}% {{ transform: translateX({previous}px); }}")
        keyframes.append(f"{start + step_percent * 0.18:.2f}% {{ transform: translateX({current}px); }}")
        keyframes.append(f"{start + step_percent * 0.78:.2f}% {{ transform: translateX({current}px); }}")
    keyframe_css = " ".join(keyframes)
    components.html(
        f"""
        <style>
            .drpe-gallery {{ width: 100%; overflow: hidden; padding: 12px 0 8px; background: #000; }}
            .drpe-gallery__track {{ display: flex; gap: 8px; width: max-content; animation: gallery-slide {max(shift_count * 4, 4)}s linear infinite; }}
            .drpe-gallery:hover .drpe-gallery__track {{ animation-play-state: paused; }}
            .gallery-slot {{ width: 228px; height: 190px; display: flex; align-items: center; justify-content: center; }}
            .drpe-gallery__track img {{ display: block; width: 228px; height: 148px; object-fit: cover; border-radius: 3px; }}
            .drpe-gallery__track .gallery-slot:nth-child(3n + 1) img {{ width: 166px; height: 190px; }}
            .drpe-gallery__track .gallery-slot:nth-child(3n + 2) img {{ width: 228px; height: 132px; }}
            .drpe-gallery__track .gallery-slot:nth-child(3n) img {{ width: 204px; height: 164px; }}
            @keyframes gallery-slide {{ {keyframe_css} }}
        </style>
        <div class="drpe-gallery" aria-label="Available encryption imagery">
            <div class="drpe-gallery__track">{cards}{cards}</div>
        </div>
        """,
        height=205,
        scrolling=False,
    )


def render_home_page(navigate_callback):
    inject_custom_css(is_home=True)
    st.markdown("<div id='landing-page'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <section class="landing-copy">
            <div class="landing-kicker">Optical security laboratory</div>
            <h1>Multimodal DRPE Encryption</h1>
            <p class="landing-quote">“Let's keep them nosey folks away.”</p>
            <p class="landing-intro">Protect images and audio with double random phase encoding.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_asset_gallery()

    image_col, audio_col = st.columns(2, gap="large")
    with image_col:
        if st.button("Launch image engine", use_container_width=True, type="primary"):
            navigate_callback("image")
    with audio_col:
        if st.button("Launch audio engine", use_container_width=True, type="primary"):
            navigate_callback("audio")

    st.markdown(
        """
        <footer class="landing-footer">
            <strong>Why encryption matters</strong>
            <span>Encryption turns private images and signals into information that only the intended recipient can recover.</span>
        </footer>
        """,
        unsafe_allow_html=True,
    )

