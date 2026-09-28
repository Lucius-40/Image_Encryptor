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
    with st.spinner(message, show_time=False):
        yield