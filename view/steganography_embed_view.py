from pathlib import Path
import io

import cv2
import numpy as np
import streamlit as st

from core.Steganography import (
    embed_cipher_self_contained,
    embed_key_payload,
    embed_key_payload_scaled,
    required_cover_pixels_bytes,
    required_cover_pixels_self_contained,
)
from core.steganography_io import decode_rgb_image
from core.utils import ciphertext_magnitude_for_display, to_uint8
from view.ui import operation_loader


COVERS_DIR = Path(__file__).resolve().parent.parent / "app_assets" / "covers"


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


def _render_cipher_embed_tab():
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
                        preview = decode_rgb_image(path.read_bytes())
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
                cover = decode_rgb_image(selected_path.read_bytes())
            except (OSError, ValueError) as error:
                st.error(f"Could not load the preset cover: {error}")
    else:
        uploaded_cover = st.file_uploader(
            "Upload a cover image", type=["png", "jpg", "jpeg", "bmp"], key="steg_cover_upload"
        )
        if uploaded_cover is not None:
            cover_name = uploaded_cover.name
            try:
                cover = decode_rgb_image(uploaded_cover.getvalue())
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
                with operation_loader("Embedding the cipher into the cover image..."):
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


def _render_key_embed_tab():
    st.subheader("Hide encryption keys")
    st.caption("Upload the keys file generated by Encrypt, then hide it in a separate cover image.")
    key_source = st.radio(
        "Key source",
        ["Use keys from Encrypt", "Upload keys (.npy)"],
        index=0 if {"enc_k1", "enc_k2"}.issubset(st.session_state) else 1,
        horizontal=True,
        key="steg_key_source",
    )
    uploaded_keys = None
    if key_source == "Upload keys (.npy)":
        uploaded_keys = st.file_uploader("Upload encryption keys (.npy)", type=["npy"], key="steg_key_file")
    cover_source = st.radio(
        "Key cover source",
        ["Preset cover", "Upload cover"],
        horizontal=True,
        key="steg_key_cover_source",
    )
    lsb_depth = st.select_slider("Key payload LSB depth", options=[1, 2], value=1, key="steg_key_lsb_depth")
    embed_method = st.radio(
        "Key embedding method",
        ["LSB (preserve cover)", "Repeat pixels to fit"],
        horizontal=True,
        key="steg_key_embed_method",
    )

    keys_data = None
    if key_source == "Use keys from Encrypt":
        if {"enc_k1", "enc_k2"}.issubset(st.session_state):
            keys_data = {
                "key1": st.session_state["enc_k1"],
                "key2": st.session_state["enc_k2"],
            }
        else:
            st.info("Encrypt an image first to make its keys available, or choose the upload option.")
    elif uploaded_keys is not None:
        try:
            keys_data = np.load(uploaded_keys, allow_pickle=True).item()
            if not isinstance(keys_data, dict) or not {"key1", "key2"}.issubset(keys_data):
                raise ValueError("The file must contain key1 and key2 arrays.")
            st.success("Keys loaded successfully.")
        except Exception as error:
            st.error(f"Could not load the keys file: {error}")

    keys_payload = None
    if keys_data is not None:
        key_buffer = io.BytesIO()
        np.save(key_buffer, {"key1": keys_data["key1"], "key2": keys_data["key2"]}, allow_pickle=True)
        keys_payload = key_buffer.getvalue()

    cover = None
    if cover_source == "Preset cover":
        preset_paths = sorted(COVERS_DIR.iterdir()) if COVERS_DIR.exists() else []
        if not preset_paths:
            st.warning("No preset covers are available. Upload a cover image instead.")
        else:
            selected_cover_key = "steg_key_preset_cover"
            selected_cover = st.session_state.get(selected_cover_key, str(preset_paths[0]))
            if selected_cover not in {str(path) for path in preset_paths}:
                selected_cover = str(preset_paths[0])

            st.caption("Choose a key cover preview")
            preview_columns = st.columns(min(3, len(preset_paths)))
            for index, path in enumerate(preset_paths):
                with preview_columns[index % len(preview_columns)]:
                    try:
                        preview = decode_rgb_image(path.read_bytes())
                        st.image(preview, caption=path.name, use_container_width=True)
                    except (OSError, ValueError) as error:
                        st.error(f"Could not preview {path.name}: {error}")
                    if st.button(
                        "Selected" if selected_cover == str(path) else "Use this cover",
                        key=f"steg_key_select_cover_{index}",
                        use_container_width=True,
                    ):
                        selected_cover = str(path)
                        st.session_state[selected_cover_key] = selected_cover

            try:
                cover = decode_rgb_image(Path(selected_cover).read_bytes())
            except (OSError, ValueError) as error:
                st.error(f"Could not load the preset cover: {error}")
    else:
        cover_file = st.file_uploader(
            "Upload a cover image for the keys",
            type=["png", "jpg", "jpeg", "bmp"],
            key="steg_key_cover",
        )
        if cover_file is not None:
            try:
                cover = decode_rgb_image(cover_file.getvalue())
            except ValueError as error:
                st.error(str(error))

    if keys_payload is not None and cover is not None:
        needed = required_cover_pixels_bytes(len(keys_payload), lsb_depth=lsb_depth)
        available = cover.shape[0] * cover.shape[1]
        st.write(f"Capacity: **{available:,}** cover pixels available / **{needed:,}** required")
        if available < needed:
            if embed_method == "LSB (preserve cover)":
                st.warning("This cover is too small for LSB embedding. Choose Repeat pixels to fit or use a larger image.")
            else:
                scale = max(1, int(np.ceil(np.sqrt(needed / available))))
                st.info(f"Cover pixels will be repeated **{scale}x** to {cover.shape[1] * scale} x {cover.shape[0] * scale} pixels before LSB embedding.")
    else:
        needed = None
        available = None

    if st.button("Hide keys in cover", type="primary", use_container_width=True, key="steg_key_embed_action"):
        if keys_payload is None or cover is None:
            st.error("Provide a valid keys file and cover image before embedding.")
        elif available < needed and embed_method == "LSB (preserve cover)":
            st.error("Embedding was not attempted because the cover is too small.")
        else:
            try:
                with operation_loader("Hiding the encryption keys in the cover image..."):
                    if embed_method == "Repeat pixels to fit":
                        stego, scale = embed_key_payload_scaled(
                            keys_payload,
                            _as_uint8_rgb(cover),
                            cv2.resize,
                            lsb_depth=lsb_depth,
                        )
                    else:
                        stego = embed_key_payload(keys_payload, _as_uint8_rgb(cover), lsb_depth=lsb_depth)
                st.session_state["steg_key_embed_result"] = (cover, stego)
            except (ValueError, TypeError) as error:
                st.error(f"Could not embed the keys: {error}")

    result = st.session_state.get("steg_key_embed_result")
    if result is not None:
        original_cover, stego = result
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.image(original_cover, caption="Original key cover", use_container_width=True)
        with col2:
            st.image(stego, caption="Key stego image", use_container_width=True)
        st.success("Keys hidden successfully. Keep this separate from the cipher stego image.")
        st.download_button(
            "Download key stego image (.png)",
            data=_png_bytes(stego),
            file_name="key_stego_image.png",
            mime="image/png",
            key="steg_key_download_image",
        )


def render_steganography_embed_tab():
    st.header("5. Hide Data in a Cover Image")
    cipher_tab, key_tab = st.tabs(["Hide cipher", "Hide keys"])
    with cipher_tab:
        _render_cipher_embed_tab()
    with key_tab:
        _render_key_embed_tab()