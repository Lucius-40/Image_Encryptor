# views/analysis_view.py
import streamlit as st
import numpy as np

from core.drpe import decrypt, generate_perturbed_key 
from core.metrics import calculate_psnr, run_sensitivity_batch
from core.utils import to_uint8
from view.plots import plot_sensitivity_curve

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
            # Call the math engine
            magnitudes, psnr_values = run_sensitivity_batch(orig_img, cipher, k1, k2, steps=batch_steps)
            
            # Call the plot generator
            fig = plot_sensitivity_curve(magnitudes, psnr_values)
            
            # Display it
            st.pyplot(fig)