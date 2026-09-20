import io

import numpy as np
import streamlit as st

from core.steganography_io import extract_cipher_from_png
from core.utils import ciphertext_magnitude_for_display, to_uint8


def render_steganography_extract_tab():
    st.header("6. Extract a Hidden Cipher")
    st.caption("Upload the original PNG stego image. It contains the header and hidden cipher.")

    uploaded_stego = st.file_uploader(
        "Upload stego image (PNG only)", type=["png", "jpg", "jpeg"], key="steg_extract_image"
    )
    if st.button("Extract hidden cipher", type="primary", use_container_width=True, key="steg_extract_action"):
        if uploaded_stego is None:
            st.error("Upload the PNG stego image before extracting the cipher.")
            return
        if not uploaded_stego.name.lower().endswith(".png"):
            st.error("Extraction only accepts PNG stego images. JPEG destroys the hidden LSB data.")
            return

        try:
            stego, cipher = extract_cipher_from_png(uploaded_stego.getvalue())
            st.session_state["steg_extract_result_v2"] = (stego, cipher)
        except Exception as error:
            st.error(f"Could not extract the cipher. Check that this is an intact PNG produced by the Embed panel: {error}")

    result = st.session_state.get("steg_extract_result_v2")
    if result is None:
        return

    stego, cipher = result
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.image(stego, caption="Uploaded stego image", use_container_width=True)
    with col2:
        st.image(
            to_uint8(ciphertext_magnitude_for_display(cipher)),
            caption="Extracted cipher (recovered from hidden data)",
            use_container_width=True,
        )

    cipher_buffer = io.BytesIO()
    export_data = {
        "cipher": cipher,
        "orig_shape": cipher.shape,
    }
    np.save(cipher_buffer, export_data, allow_pickle=True)
    st.success("Cipher extracted successfully. Download it and provide it to the Decrypt page.")
    st.download_button(
        "Download extracted cipher (.npy)",
        data=cipher_buffer.getvalue(),
        file_name="extracted_cipher.npy",
        mime="application/octet-stream",
        key="steg_download_cipher",
    )