import streamlit as st
import numpy as np
import cv2

from core.rgb_dpre import generate_color_keys, encrypt_color, decrypt_color
from core.drpe import generate_perturbed_key
from core.metrics import calculate_psnr
from core.utils import ciphertext_magnitude_for_display, to_uint8, compute_target_size


def render_color_tab():
    st.header("5. Color (RGB) Encryption")
    st.write("Encrypt a color image using DRPE, with either one shared key set or independent keys per channel.")

    uploaded_img = st.file_uploader(
        "Upload Color Image (JPG/PNG)", type=['png', 'jpg', 'jpeg'], key="color_uploader"
    )

    st.subheader("Key Settings")
    key_mode = st.radio(
        "Number of Keys",
        ["1 Key (Shared across R, G, B)", "3 Keys (Independent per channel)"],
        horizontal=True,
        key="color_key_mode"
    )
    shared = key_mode.startswith("1")
    seed = st.number_input("Seed", min_value=0, max_value=999999, value=1, key="color_seed")

    if not uploaded_img:
        st.info("Upload a color image to begin.")
        return

    file_bytes = np.asarray(bytearray(uploaded_img.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    target_w, target_h = compute_target_size(*img_bgr.shape[:2], max_dim=768)
    img_bgr = cv2.resize(img_bgr, (target_w, target_h))
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_norm = img_rgb.astype(np.float64) / 255.0

    if st.button("Generate Keys & Encrypt", type="primary", key="color_encrypt_btn"):
        keys = generate_color_keys(img_norm.shape[:2], shared=shared, seed=seed)
        cipher = encrypt_color(img_norm, keys)

        st.session_state['color_img_norm'] = img_norm
        st.session_state['color_keys'] = keys
        st.session_state['color_cipher'] = cipher
        st.session_state['color_shared'] = shared
        st.session_state['color_encryption_done'] = True

    if not st.session_state.get('color_encryption_done'):
        return

    c_img = st.session_state['color_img_norm']
    c_keys = st.session_state['color_keys']
    c_cipher = st.session_state['color_cipher']
    c_shared = st.session_state['color_shared']

    col1, col2 = st.columns(2)
    with col1:
        st.image(to_uint8(c_img), caption="Original Image", use_container_width=True)
    with col2:
        cipher_display = ciphertext_magnitude_for_display(c_cipher)
        st.image(to_uint8(cipher_display), caption="Ciphertext (Visual Magnitude)", use_container_width=True)

    st.divider()

    if c_shared:
        st.info(
            "Using 1 shared key pair across all channels — decrypts perfectly with the "
            "correct pair, or fails completely with a wrong one. Switch to 3-Key mode "
            "below to test per-channel key corruption."
        )
        decrypted = np.clip(decrypt_color(c_cipher, c_keys), 0, 1)
        psnr = calculate_psnr(c_img, decrypted)
        st.image(to_uint8(decrypted), caption=f"Decrypted (PSNR: {psnr:.2f} dB)", use_container_width=True)
        return

    st.subheader("Per-Channel Key Corruption")
    st.write("Independently corrupt the decryption key for each channel and see how the reconstruction degrades.")

    r_err = st.slider("Red channel key error", 0.0, 0.5, 0.0, 0.01, key="color_r_err")
    g_err = st.slider("Green channel key error", 0.0, 0.5, 0.0, 0.01, key="color_g_err")
    b_err = st.slider("Blue channel key error", 0.0, 0.5, 0.0, 0.01, key="color_b_err")
    errs = [r_err, g_err, b_err]

    decrypt_keys = []
    for ch in range(3):
        key1, key2 = c_keys[ch]
        damaged_key2 = generate_perturbed_key(key2, error_magnitude=errs[ch])
        decrypt_keys.append((key1, damaged_key2))

    decrypted = np.clip(decrypt_color(c_cipher, decrypt_keys), 0, 1)
    overall_psnr = calculate_psnr(c_img, decrypted)

    per_channel = []
    for ch, label in enumerate(["R", "G", "B"]):
        ch_psnr = calculate_psnr(c_img[:, :, ch], decrypted[:, :, ch])
        per_channel.append(f"{label}: {ch_psnr:.1f} dB")

    st.image(
        to_uint8(decrypted),
        caption=f"Decrypted (Overall PSNR: {overall_psnr:.2f} dB | {' / '.join(per_channel)})",
        use_container_width=True,
    )