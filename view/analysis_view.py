# views/analysis_view.py
import streamlit as st
import numpy as np

from core.drpe import decrypt, generate_perturbed_key 
from core.metrics import (
    calculate_psnr,
    run_sensitivity_batch,
    run_robustness_batch,
    add_gaussian_noise,
    quantize_complex,
    jpeg_compress_complex,
)
from core.utils import to_uint8
from view.plots import plot_sensitivity_curve, plot_robustness_curve

def render_analysis_tab():
    st.header("3. Corruption Analysis")
    st.write("Compare the effect of corrupted decryption keys and corrupted ciphertext on recovery quality.")

    if 'enc_img_norm' not in st.session_state:
        st.info("Please encrypt an image in Tab 1 first to run the analysis.")
        return

    orig_img = st.session_state['enc_img_norm']
    cipher = st.session_state['enc_cipher']
    k1 = st.session_state['enc_k1']
    k2 = st.session_state['enc_k2']

    key_tab, cipher_tab = st.tabs(["Key corruption", "Cipher corruption"])
    with key_tab:
        _render_key_corruption(orig_img, cipher, k1, k2)
    with cipher_tab:
        _render_cipher_corruption(orig_img, cipher, k1, k2)


def _render_key_corruption(orig_img, cipher, k1, k2):
    st.subheader("Key corruption")
    st.write("Test how the algorithm reacts when the decryption key is slightly damaged or guessed incorrectly.")
    error_mag = st.slider("Key Error Magnitude (Gaussian Noise Scale)", 0.0, 0.5, 0.0, 0.01, key="key_error_magnitude")

    damaged_k2 = generate_perturbed_key(k2, error_magnitude=error_mag)
    recovered = np.clip(decrypt(cipher, k1, damaged_k2), 0, 1)
    current_psnr = calculate_psnr(orig_img, recovered)

    col1, col2 = st.columns(2)
    with col1:
        st.image(to_uint8(orig_img), caption="Original Input")
    with col2:
        label = "Decrypted (Perfect Match: Infinity dB)" if current_psnr == float('inf') else f"Decrypted (PSNR: {current_psnr:.2f} dB)"
        st.image(to_uint8(recovered), caption=label)

    st.subheader("Generate Key Sensitivity Curve")
    batch_steps = st.slider("Sensitivity Batch Steps", min_value=10, max_value=200, value=50, step=10, key="key_sensitivity_steps")
    if st.button("Plot Key Sensitivity Curve", type="primary", key="plot_key_curve"):
        with st.spinner(f"Running {batch_steps} decryptions..."):
            magnitudes, psnr_values = run_sensitivity_batch(orig_img, cipher, k1, k2, steps=batch_steps)
            st.plotly_chart(plot_sensitivity_curve(magnitudes, psnr_values), use_container_width=True)


def _render_cipher_corruption(orig_img, cipher, k1, k2):
    st.subheader("Cipher corruption")
    st.write("Measure how noise, compression, and quantization damage the encrypted ciphertext.")
    robustness_mode = st.selectbox(
        "Corruption model",
        ["Gaussian Noise", "JPEG Compression", "Quantization"],
        key="cipher_robustness_mode",
    )

    if robustness_mode == "Gaussian Noise":
        levels = np.linspace(0.01, 0.5, 20)
        title = "DRPE Robustness: Gaussian Noise"
    elif robustness_mode == "JPEG Compression":
        levels = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90])
        title = "DRPE Robustness: JPEG Compression"
    else:
        levels = np.array([8, 16, 32, 64, 128, 256, 512, 1024])
        title = "DRPE Robustness: Quantization"

    if st.button("Run Cipher Robustness Test", type="primary", key="run_cipher_robustness"):
        mode = {"Gaussian Noise": "noise", "JPEG Compression": "jpeg", "Quantization": "quant"}[robustness_mode]
        severity, psnr_values = run_robustness_batch(orig_img, cipher, k1, k2, mode=mode, levels=levels)
        st.plotly_chart(plot_robustness_curve(severity, psnr_values, title), use_container_width=True)

    st.subheader("Three Corruption Stages and Their Decryption")
    if st.button("Show 3 Cipher Corruption Samples", type="secondary", key="show_cipher_samples"):
        mode = {"Gaussian Noise": "noise", "JPEG Compression": "jpeg", "Quantization": "quant"}[robustness_mode]
        if mode == "noise":
            severities = [0.05, 0.2, 0.4]
            corrupt = add_gaussian_noise
        elif mode == "jpeg":
            severities = [75, 40, 15]
            corrupt = jpeg_compress_complex
        else:
            severities = [512, 128, 32]
            corrupt = quantize_complex

        cols = st.columns(3)
        for i, severity in enumerate(severities):
            corrupted = corrupt(cipher, severity)
            recovered = np.clip(decrypt(corrupted, k1, k2), 0, 1)
            psnr = calculate_psnr(orig_img, recovered)
            with cols[i]:
                st.caption(f"Level {i + 1}: severity = {severity}")
                st.image(to_uint8(np.abs(corrupted)), caption="Corrupted ciphertext magnitude")
                st.image(to_uint8(recovered), caption=f"Decrypted image (PSNR: {psnr:.2f} dB)")