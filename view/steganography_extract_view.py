import io

import numpy as np
import streamlit as st

from core.Steganography import extract_cipher_self_contained, extract_key_payload
from core.utils import ciphertext_magnitude_for_display, to_uint8


def _decode_rgb(file_bytes):
    image = cv2.imdecode(np.frombuffer(file_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("The selected file is not a readable PNG.")
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _render_cipher_extract_tab():
    st.header("6. Extract a Hidden Cipher")
    st.caption("Upload the original PNG stego image. It contains the header and hidden cipher.")

    uploaded_stego = st.file_uploader(
        "Upload stego image (PNG only)", type=["png", "jpg", "jpeg"], key="steg_extract_image"
    )
    if uploaded_stego is None:
        st.markdown(
            """
            <div class="empty-watermark" aria-label="No stego image uploaded">
                <div class="empty-watermark__title">Awaiting Stego Image</div>
                <div class="empty-watermark__hint">Upload a PNG with a hidden cipher to begin extraction.</div>
            </div>
            """,
            unsafe_allow_html=True,
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


def _render_key_extract_tab():
    st.subheader("Extract encryption keys")
    st.caption("Upload the separate key stego image produced by Hide keys.")
    uploaded_key_stego = st.file_uploader(
        "Upload key stego image (PNG only)",
        type=["png"],
        key="steg_extract_key_image",
    )
    if uploaded_key_stego is None:
        st.markdown(
            """
            <div class="empty-watermark" aria-label="No key stego image uploaded">
                <div class="empty-watermark__title">Awaiting Key Image</div>
                <div class="empty-watermark__hint">Upload the separate PNG containing the hidden encryption keys.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Extract hidden keys", type="primary", use_container_width=True, key="steg_extract_keys_action"):
        if uploaded_key_stego is None:
            st.error("Upload the key stego image before extracting the keys.")
        else:
            try:
                key_payload = extract_key_payload(_decode_rgb(uploaded_key_stego.getvalue()))
                keys_data = np.load(io.BytesIO(key_payload), allow_pickle=True).item()
                if not isinstance(keys_data, dict) or not {"key1", "key2"}.issubset(keys_data):
                    raise ValueError("The extracted payload does not contain key1 and key2.")
                st.session_state["steg_extract_keys_result"] = (uploaded_key_stego.getvalue(), key_payload)
            except Exception as error:
                st.error(f"Could not extract the keys. Check that this is a key stego PNG: {error}")

    result = st.session_state.get("steg_extract_keys_result")
    if result is not None:
        image_bytes, key_payload = result
        st.image(_decode_rgb(image_bytes), caption="Uploaded key stego image", use_container_width=True)
        st.success("Encryption keys extracted successfully.")
        st.download_button(
            "Download extracted keys (.npy)",
            data=key_payload,
            file_name="extracted_keys.npy",
            mime="application/octet-stream",
            key="steg_download_keys",
        )


def render_steganography_extract_tab():
    st.header("6. Extract Hidden Data")
    cipher_tab, key_tab = st.tabs(["Extract cipher", "Extract keys"])
    with cipher_tab:
        _render_cipher_extract_tab()
    with key_tab:
        _render_key_extract_tab()