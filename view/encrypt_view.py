import streamlit as st
import numpy as np
import cv2
import io
import matplotlib.pyplot as plt

from core.drpe import generate_random_phase_mask, encrypt
from core.utils import ciphertext_magnitude_for_display, to_uint8, compute_target_size

def _contrast_stretch(values, low=1, high=99):
    minimum, maximum = np.percentile(values, [low, high])
    return np.clip(values, minimum, maximum)

def plot_behind_the_scenes(image_norm, key1, cipher):
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(15, 4.5),
        facecolor="#030805",
        constrained_layout=True,
    )

    fig.patch.set_edgecolor("#123D22")
    fig.patch.set_linewidth(2)

    panel_titles = [
        "Key 1 Phase Angles",
        "Original Frequency Spectrum",
        "Ciphertext Frequency Spectrum",
    ]

    # Key phase image
    key_phase = np.angle(key1)
    axes[0].imshow(
        key_phase,
        cmap="hsv",
        vmin=-np.pi,
        vmax=np.pi,
        interpolation="nearest",
    )

    # Original frequency spectrum
    original_frequency = np.fft.fftshift(np.fft.fft2(image_norm))
    original_spectrum = _contrast_stretch(
        np.log1p(np.abs(original_frequency))
    )
    axes[1].imshow(
        original_spectrum,
        cmap="magma",
        interpolation="nearest",
    )

    # Ciphertext frequency spectrum
    cipher_frequency = np.fft.fftshift(np.fft.fft2(cipher))
    cipher_spectrum = _contrast_stretch(
        np.log1p(np.abs(cipher_frequency))
    )
    axes[2].imshow(
        cipher_spectrum,
        cmap="magma",
        interpolation="nearest",
    )

    for axis, title in zip(axes, panel_titles):
        axis.set_facecolor("#07150D")
        axis.set_title(
            title,
            color="#F2FFF0",
            fontsize=13,
            fontweight="bold",
            pad=12,
        )

        # Hide ticks while preserving the panel border.
        axis.set_xticks([])
        axis.set_yticks([])

        for spine in axis.spines.values():
            spine.set_visible(True)
            spine.set_color("#39FF14")
            spine.set_linewidth(1.5)

    return fig

def render_encrypt_tab():
    st.header("1. Encrypt an Image")
    
    # Initialize the session state for holding our results on the screen
    if 'encryption_done' not in st.session_state:
        st.session_state['encryption_done'] = False

    # 1. Primary Input
    uploaded_img = st.file_uploader("Upload Image (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
    
    # 2. Progressive Disclosure: Hide the advanced settings!
    with st.expander("⚙️ Advanced Security Settings & Analysis"):
        key_mode = st.radio(
            "Select Key Generation Method:", 
            ["Secure Mode (Export Key File)", "Demo Mode (Manual PIN)"], 
            horizontal=True
        )
        
        pin = None
        if key_mode == "Demo Mode (Manual PIN)":
            pin = st.number_input("Enter a numeric PIN (e.g., 4096)", min_value=0, max_value=999999, value=4096)
            st.caption("⚠️ Using a low-entropy PIN makes the encryption mathematically vulnerable to brute-force attacks. Use only for fast presentations.")

        show_math = st.toggle("🔍 Show Behind the Scenes (Signal Processing)")

    if uploaded_img:
        file_bytes = np.asarray(bytearray(uploaded_img.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
        
        orig_shape = img.shape
        target_w, target_h = compute_target_size(*orig_shape, max_dim=768)
        img_resized = cv2.resize(img, (target_w, target_h))
        img_norm = img_resized.astype(np.float64) / 255.0
        
        # 3. Primary Action
        if st.button("./execute_drpe_encryption.sh", type="primary", use_container_width=True):
            with st.spinner("Processing 2D Fast Fourier Transform..."):
                if key_mode == "Demo Mode (Manual PIN)":
                    k1 = generate_random_phase_mask(img_norm.shape, seed=pin)
                    k2 = generate_random_phase_mask(img_norm.shape, seed=pin + 1)
                else:
                    k1 = generate_random_phase_mask(img_norm.shape)
                    k2 = generate_random_phase_mask(img_norm.shape)
                    
                cipher = encrypt(img_norm, k1, k2)
                
                st.session_state['enc_img_norm'] = img_norm
                st.session_state['enc_k1'] = k1
                st.session_state['enc_k2'] = k2
                st.session_state['enc_cipher'] = cipher
                st.session_state['enc_orig_shape'] = orig_shape
                st.session_state['enc_key_mode'] = key_mode
                st.session_state['enc_pin'] = pin
                st.session_state['encryption_done'] = True

        # 4. Output Display
        if st.session_state['encryption_done']:
            c_img_norm = st.session_state['enc_img_norm']
            c_k1 = st.session_state['enc_k1']
            c_k2 = st.session_state['enc_k2']
            c_cipher = st.session_state['enc_cipher']
            c_shape = st.session_state['enc_orig_shape']
            c_mode = st.session_state['enc_key_mode']
            c_pin = st.session_state['enc_pin']

            col1, col2 = st.columns(2)
            with col1:
                st.image(to_uint8(c_img_norm), caption="Original Image", use_container_width=True)
            with col2:
                display_cipher = to_uint8(ciphertext_magnitude_for_display(c_cipher))
                st.image(display_cipher, caption="Ciphertext (Visual Magnitude)", use_container_width=True)
            
            if show_math:
                st.divider()
                st.pyplot(
                    plot_behind_the_scenes(c_img_norm, c_k1, c_cipher),
                    use_container_width=True,
                )
            
            export_data = {'cipher': c_cipher, 'orig_shape': c_shape}
            buffer = io.BytesIO()
            np.save(buffer, export_data, allow_pickle=True)
            
            st.success("[ OK ] Encryption complete. Payload ready for extraction.")
            
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button("🔒 Download Encrypted Data (.npy)", data=buffer.getvalue(), file_name="secret_data.npy")
            
            with dl_col2:
                if c_mode == "Secure Mode (Export Key File)":
                    key_data = {'key1': c_k1, 'key2': c_k2}
                    key_buffer = io.BytesIO()
                    np.save(key_buffer, key_data, allow_pickle=True)
                    st.download_button("🔑 Download Encryption Keys (.npy)", data=key_buffer.getvalue(), file_name="keys.npy")
                else:
                    st.info(f"Remember your PIN ({c_pin}) to decrypt this file.")