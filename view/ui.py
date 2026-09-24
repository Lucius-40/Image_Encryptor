import base64
import time
from contextlib import contextmanager
from pathlib import Path

import streamlit as st


GIF_PATH = Path(__file__).resolve().parent.parent / "assets" / "side.gif"


def _gif_data_url():
    try:
        encoded = base64.b64encode(GIF_PATH.read_bytes()).decode("ascii")
    except OSError:
        return None
    return f"data:image/gif;base64,{encoded}"


@contextmanager
def operation_loader(message):
    started_at = time.perf_counter()
    placeholder = st.empty()
    gif_url = _gif_data_url()
    media = f'<img src="{gif_url}" alt="" />' if gif_url else '<span class="operation-loader__pulse"></span>'
    placeholder.markdown(
        f"""
        <div class="operation-loader" role="status">
            <div class="operation-loader__media">{media}</div>
            <div class="operation-loader__message">{message}</div>
            <div class="operation-loader__track"><span></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        time.sleep(max(0.0, 1.0 - (time.perf_counter() - started_at)))
        placeholder.empty()