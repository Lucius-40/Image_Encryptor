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
    st.header("3. Key Sensitivity Analysis")
    st.write("Test how the algorithm reacts when the decryption key is slightly damaged or guessed incorrectly.")

    if 'enc_img_norm' not in st.session_state:
        st.info("Please encrypt an image in Tab 1 first to run the analysis.")
        return

    # 1. Pull Baseline Data
    orig_img = st.session_state['enc_img_norm']
    cipher = st.session_state['enc_cipher']
    k1 = st.session_state['enc_k1']
    k2 = st.session_state['enc_k2']

    st.divider()

    # --- PART A: Interactive Slider ---
    st.subheader("Interactive Perturbation")
    error_mag = st.slider("Key Error Magnitude (Gaussian Noise Scale)", 0.0, 0.5, 0.0, 0.01)

    damaged_k2 = generate_perturbed_key(k2, error_magnitude=error_mag)
    recovered = np.clip(decrypt(cipher, k1, damaged_k2), 0, 1)
    current_psnr = calculate_psnr(orig_img, recovered)

    col1, col2 = st.columns(2)
    with col1:
        st.image(to_uint8(orig_img), caption="Original Input")
    with col2:
        label = "Decrypted (Perfect Match: Infinity dB)" if current_psnr == float('inf') else f"Decrypted (PSNR: {current_psnr:.2f} dB)"
        st.image(to_uint8(recovered), caption=label)

    st.divider()

    # --- PART B: Sensitivity Curve Graph ---
    st.subheader("Generate Sensitivity Curve")
    batch_steps = st.slider("Sensitivity Batch Steps", min_value=10, max_value=200, value=50, step=10)

    if st.button("Plot Curve", type="primary"):
        with st.spinner(f"Running {batch_steps} decryptions..."):
            magnitudes, psnr_values = run_sensitivity_batch(orig_img, cipher, k1, k2, steps=batch_steps)
            fig = plot_sensitivity_curve(magnitudes, psnr_values)
            st.pyplot(fig)

    st.divider()
    st.header("4. Robustness to Ciphertext Corruption")

    robustness_mode = st.selectbox(
        "Corruption model",
        ["Gaussian Noise", "JPEG Compression", "Quantization"],
        key="robustness_mode"
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

    if st.button("Run Robustness Test", type="primary"):
        mode = {
            "Gaussian Noise": "noise",
            "JPEG Compression": "jpeg",
            "Quantization": "quant"
        }[robustness_mode]

        severity, psnr_values = run_robustness_batch(
            orig_img, cipher, k1, k2, mode=mode, levels=levels
        )
        fig = plot_robustness_curve(severity, psnr_values, title)
        st.pyplot(fig)

    st.subheader("Three Corruption Stages and Their Decryption")

    if st.button("Show 3 Corruption Samples", type="secondary"):
        mode = {
            "Gaussian Noise": "noise",
            "JPEG Compression": "jpeg",
            "Quantization": "quant"
        }[robustness_mode]

        if mode == "noise":
            severities = [0.05, 0.2, 0.4]
            samples = []
            for s in severities:
                corrupted = add_gaussian_noise(cipher, s)
                recovered = np.clip(decrypt(corrupted, k1, k2), 0, 1)
                psnr = calculate_psnr(orig_img, recovered)
                samples.append((s, corrupted, recovered, psnr))

        elif mode == "jpeg":
            severities = [75, 40, 15]
            samples = []
            for s in severities:
                corrupted = jpeg_compress_complex(cipher, quality=s)
                recovered = np.clip(decrypt(corrupted, k1, k2), 0, 1)
                psnr = calculate_psnr(orig_img, recovered)
                samples.append((s, corrupted, recovered, psnr))

        else:
            severities = [512, 128, 32]
            samples = []
            for s in severities:
                corrupted = quantize_complex(cipher, levels=s)
                recovered = np.clip(decrypt(corrupted, k1, k2), 0, 1)
                psnr = calculate_psnr(orig_img, recovered)
                samples.append((s, corrupted, recovered, psnr))

        cols = st.columns(3)
        for i, (sev, corrupted, recovered, psnr) in enumerate(samples):
            with cols[i]:
                st.caption(f"Level {i + 1}: severity = {sev}")
                st.image(to_uint8(np.abs(corrupted)), caption="Corrupted ciphertext magnitude")
                st.image(to_uint8(recovered), caption=f"Decrypted image (PSNR: {psnr:.2f} dB)")