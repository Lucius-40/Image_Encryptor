from pathlib import Path

import cv2
import numpy as np
import streamlit as st

from core.Steganography import embed_cipher_self_contained, required_cover_pixels_self_contained
from core.utils import ciphertext_magnitude_for_display, to_uint8


COVERS_DIR = Path(__file__).resolve().parent.parent / "app_assets" / "covers"


def _decode_rgb(file_bytes):
    image = cv2.imdecode(np.frombuffer(file_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("The selected file is not a readable image.")
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _as_uint8_rgb(image):
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image


def _load_cipher(uploaded_cipher):
    if uploaded_cipher is None:
        cipher = st.session_state.get("enc_cipher")
        if cipher is None:
            return None
        return np.asarray(cipher)

    loaded_data = np.load(uploaded_cipher, allow_pickle=True).item()
    if not isinstance(loaded_data, dict) or "cipher" not in loaded_data:
        raise ValueError("The uploaded file does not contain a cipher payload.")
    return np.asarray(loaded_data["cipher"])


def _png_bytes(image):
    success, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not success:
        raise ValueError("Could not encode the stego image as PNG.")
    return encoded.tobytes()


def render_steganography_embed_tab():
    st.header("5. Hide a Cipher in a Cover Image")
    st.caption("The single PNG stego image contains everything needed for lossless extraction.")

    cipher_source = st.radio(
        "Cipher source",
        ["Use cipher from Encrypt", "Upload cipher (.npy)"],
        index=0 if "enc_cipher" in st.session_state else 1,
        horizontal=True,
        key="steg_embed_cipher_source",
    )
    uploaded_cipher = None
    if cipher_source == "Upload cipher (.npy)":
        uploaded_cipher = st.file_uploader(
            "Upload encrypted data (.npy)", type=["npy"], key="steg_embed_cipher"
        )
    elif "enc_cipher" not in st.session_state:
        st.info("Run the Encrypt page first, or choose the upload option above.")

    cover_source = st.radio(
        "Cover image source", ["Preset cover", "Upload cover"], horizontal=True, key="steg_cover_source"
    )
    cover = None
    cover_name = None
    if cover_source == "Preset cover":
        preset_paths = sorted(COVERS_DIR.iterdir()) if COVERS_DIR.exists() else []
        if not preset_paths:
            st.warning("No preset covers are available. Upload a cover image instead.")
        else:
            selected_cover_key = "steg_preset_cover"
            selected_cover = st.session_state.get(selected_cover_key, str(preset_paths[0]))
            if selected_cover not in {str(path) for path in preset_paths}:
                selected_cover = str(preset_paths[0])

            st.caption("Choose a cover preview")
            preview_columns = st.columns(min(3, len(preset_paths)))
            for index, path in enumerate(preset_paths):
                with preview_columns[index % len(preview_columns)]:
                    try:
                        preview = _decode_rgb(path.read_bytes())
                        st.image(preview, caption=path.name, use_container_width=True)
                    except (OSError, ValueError) as error:
                        st.error(f"Could not preview {path.name}: {error}")
                    if st.button(
                        "Selected" if selected_cover == str(path) else "Use this cover",
                        key=f"steg_select_cover_{index}",
                        use_container_width=True,
                    ):
                        selected_cover = str(path)
                        st.session_state[selected_cover_key] = selected_cover

            selected_path = Path(selected_cover)
            st.caption(f"Selected cover: {selected_path.name}")
            cover_name = selected_path.name
            try:
                cover = _decode_rgb(selected_path.read_bytes())
            except (OSError, ValueError) as error:
                st.error(f"Could not load the preset cover: {error}")
    else:
        uploaded_cover = st.file_uploader(
            "Upload a cover image", type=["png", "jpg", "jpeg", "bmp"], key="steg_cover_upload"
        )
        if uploaded_cover is not None:
            cover_name = uploaded_cover.name
            try:
                cover = _decode_rgb(uploaded_cover.getvalue())
            except ValueError as error:
                st.error(str(error))

    lsb_depth = st.select_slider("LSB depth", options=[1, 2], value=1, key="steg_lsb_depth")

    try:
        cipher = _load_cipher(uploaded_cipher)
    except Exception as error:
        st.error(f"Could not load the cipher: {error}")
        cipher = None

    needed = None
    available = cover.shape[0] * cover.shape[1] if cover is not None else None
    if cipher is not None:
        if cipher.ndim != 2 or not np.iscomplexobj(cipher):
            st.error("The cipher must be a 2D complex-valued array.")
            cipher = None
        else:
            needed = required_cover_pixels_self_contained(cipher.shape, lsb_depth=lsb_depth)
            if available is not None:
                st.write(f"Capacity: **{available:,}** cover pixels available / **{needed:,}** required")
                if available < needed:
                    st.warning(
                        f"This cover is too small: it needs {needed:,} pixels but has {available:,}. "
                        "Choose a larger cover or increase LSB depth."
                    )

    if st.button("Embed cipher into cover", type="primary", use_container_width=True, key="steg_embed_action"):
        if cipher is None or cover is None:
            st.error("Provide a valid cipher and cover image before embedding.")
        elif available < needed:
            st.error("Embedding was not attempted because the selected cover is too small.")
        else:
            try:
                stego = embed_cipher_self_contained(cipher, _as_uint8_rgb(cover), lsb_depth=lsb_depth)
                st.session_state["steg_embed_result_v2"] = (cover, stego, cipher, cover_name)
            except (ValueError, TypeError) as error:
                st.error(f"Could not embed the cipher: {error}")

    result = st.session_state.get("steg_embed_result_v2")
    if result is None:
        return

    original_cover, stego, embedded_cipher, result_cover_name = result
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(original_cover, caption=f"Cover: {result_cover_name}", use_container_width=True)
    with col2:
        st.image(
            to_uint8(ciphertext_magnitude_for_display(embedded_cipher)),
            caption="Cipher (before hiding)",
            use_container_width=True,
        )
    with col3:
        st.image(stego, caption="Stego image (cipher hidden inside)", use_container_width=True)

    st.success("Cipher embedded successfully. The PNG contains everything needed for extraction.")
    st.download_button(
        "Download stego image (.png)",
        data=_png_bytes(stego),
        file_name="stego_image.png",
        mime="image/png",
        key="steg_download_image",
    )