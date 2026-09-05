import streamlit as st
import numpy as np
import io
import time
import matplotlib.pyplot as plt

from core.audio_drpe import encrypt_audio, decrypt_audio, perturb_audio_key
from core.audio_utils import load_and_normalize_audio, wav_bytes_from_float_audio
from core.metrics import (
    calculate_audio_snr_db,
    calculate_audio_mse,
    calculate_audio_correlation,
    run_audio_sensitivity_batch,
)
from view.plots import plot_audio_sensitivity_curve


# --- 1. THE AUDIO MODAL POP-UP (The "Wow" Factor) ---
@st.dialog("SECURE AUDIO PAYLOAD EXTRACTED", width="large")
def render_audio_output_modal(orig_audio, sr, cipher, k1, k2, key_mode, pin):
    st.success("[ Encryption Complete.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Target Signal (Original)")
        st.audio(wav_bytes_from_float_audio(orig_audio, int(sr)), format="audio/wav")
        
    with col2:
        st.write("Ciphertext (Encrypted Noise)")
        # Convert complex ciphertext to playable float audio
        cipher_real = np.real(cipher)
        max_amp = np.max(np.abs(cipher_real))
        cipher_playable = cipher_real / max_amp if max_amp > 0 else cipher_real
        
        st.audio(wav_bytes_from_float_audio(cipher_playable, int(sr)), format="audio/wav")
        
    st.divider()
    
    # Waveform Visualization
    st.write("Signal Waveform Comparison")
    fig, ax = plt.subplots(1, 2, figsize=(12, 3))
    
    ax[0].plot(orig_audio[:1000], color='#39FF14') 
    ax[0].set_title("Original Waveform Structure", color='white')
    ax[0].set_facecolor('#050505')
    ax[0].axis('off')
    
    ax[1].plot(cipher_playable[:1000], color='red')
    ax[1].set_title("Scrambled Ciphertext", color='white')
    ax[1].set_facecolor('#050505')
    ax[1].axis('off')
    
    fig.patch.set_facecolor('#050505')
    st.pyplot(fig)
    
    st.divider()
    
    # Prepare Downloads
    def array_to_bytes(arr):
        buf = io.BytesIO()
        np.save(buf, arr)
        return buf.getvalue()
        
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button("💾 Ciphertext (.npy)", array_to_bytes(cipher), "audio_cipher.npy", use_container_width=True)
    with dl2:
        if key_mode == "Secure Mode (Export Key Files)":
            st.download_button("🔑 Key 1 (.npy)", array_to_bytes(k1), "audio_key1.npy", use_container_width=True)
    with dl3:
        if key_mode == "Secure Mode (Export Key Files)":
            st.download_button("🔑 Key 2 (.npy)", array_to_bytes(k2), "audio_key2.npy", use_container_width=True)
        else:
            st.info(f"Remember PIN: {pin}")


# --- 2. THE MAIN TERMINAL VIEW ---
def render_audio_encrypt():
    st.header("Audio Signal Encryption (1D DRPE)")

    if 'audio_bytes' not in st.session_state:
        st.session_state['audio_bytes'] = None
    if 'audio_cipher' not in st.session_state:
        st.session_state['audio_cipher'] = None
        st.session_state['audio_k1'] = None
        st.session_state['audio_k2'] = None

    # Upload Block
    if st.session_state['audio_bytes'] is None:
        uploaded_audio = st.file_uploader("Upload a .wav file", type=["wav"])
        if uploaded_audio is not None:
            st.session_state['audio_bytes'] = uploaded_audio.getvalue()
            st.rerun()
            
    # Execution Terminal
    else:
        st.success("[ OK ] Audio payload loaded into secure memory.")
        audio_io = io.BytesIO(st.session_state['audio_bytes'])
        
        # Progressive Disclosure: Hide settings by default
        with st.expander("⚙️ Advanced Security Settings"):
            key_mode = st.radio(
                "Select Key Generation Method:",
                ["Secure Mode (Export Key Files)", "Demo Mode (Manual PIN)"],
                horizontal=True,
            )

            pin = None
            if key_mode == "Demo Mode (Manual PIN)":
                pin = st.number_input("Enter a numeric PIN (e.g., 4096)", min_value=0, max_value=999999, value=4096)
                st.caption("⚠️ Using a low-entropy PIN makes the encryption vulnerable to brute-force attacks. Use only for presentations.")

        col_exec, col_clear = st.columns([3, 1])
        with col_exec:
            execute_btn = st.button("./execute_audio_encrypt.sh", type="primary", use_container_width=True)
        with col_clear:
            if st.button("rm payload", use_container_width=True):
                st.session_state['audio_bytes'] = None
                st.session_state['audio_cipher'] = None
                st.session_state['audio_signal'] = None
                st.rerun()

        # Math Execution & Trigger Modal
        if execute_btn:
            # Cinematic progress bar
            progress_text = "Applying 1D phase masks and executing FFT..."
            my_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.01) 
                my_bar.progress(percent_complete + 1, text=progress_text)
            my_bar.empty()

            audio_io.seek(0)
            sr, audio_signal = load_and_normalize_audio(audio_io)

            if key_mode == "Demo Mode (Manual PIN)":
                cipher, k1, k2 = encrypt_audio(audio_signal, pin=pin)
            else:
                cipher, k1, k2 = encrypt_audio(audio_signal)

            st.session_state['audio_cipher'] = cipher
            st.session_state['audio_k1'] = k1
            st.session_state['audio_k2'] = k2
            st.session_state['audio_signal'] = audio_signal
            st.session_state['audio_sr'] = sr
            st.session_state['audio_key_mode'] = key_mode
            st.session_state['audio_pin'] = pin
            
            # Fire the Modal
            render_audio_output_modal(audio_signal, sr, cipher, k1, k2, key_mode, pin)

        # --- 3. THE ANALYTICS ENGINE (Remains on page after modal closes) ---
        if st.session_state['audio_cipher'] is not None:
            st.divider()
            st.subheader("Audio Key Sensitivity Analysis")
            st.write("Quantitatively perturb Key 2 with Gaussian phase noise and measure decryption quality.")

            orig_audio = st.session_state.get('audio_signal')
            audio_sr = st.session_state.get('audio_sr', 16000)
            cipher = st.session_state['audio_cipher']
            k1 = st.session_state['audio_k1']
            k2 = st.session_state['audio_k2']

            sigma = st.slider("Key 2 Perturbation Magnitude (sigma)", 0.0, 0.5, 0.0, 0.01)

            damaged_k2 = perturb_audio_key(k2, error_magnitude=sigma)
            recovered_preview = decrypt_audio(cipher, k1, damaged_k2)

            snr_db = calculate_audio_snr_db(orig_audio, recovered_preview)
            mse = calculate_audio_mse(orig_audio, recovered_preview)
            corr = calculate_audio_correlation(orig_audio, recovered_preview)

            m1, m2, m3 = st.columns(3)
            with m1:
                snr_label = "inf" if snr_db == float('inf') else f"{snr_db:.2f}"
                st.metric("SNR (dB)", snr_label)
            with m2:
                st.metric("MSE", f"{mse:.6f}")
            with m3:
                st.metric("Correlation", f"{corr:.4f}")

            st.divider()
            steps = st.slider("Sensitivity Sweep Steps", min_value=10, max_value=200, value=50, step=10)

            # Utilizing your friend's Plotly update!
            if st.button("Plot Audio Sensitivity Curve", type="primary"):
                with st.spinner(f"Running {steps} decryption trials..."):
                    mags, snr_values, mse_values, corr_values = run_audio_sensitivity_batch(
                        orig_audio, cipher, k1, k2, steps=steps, max_sigma=0.5,
                    )
                    fig = plot_audio_sensitivity_curve(mags, snr_values)
                    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

                    st.caption(
                        f"Final point at sigma={mags[-1]:.2f}: "
                        f"SNR={snr_values[-1]:.2f} dB, "
                        f"MSE={mse_values[-1]:.6f}, "
                        f"Corr={corr_values[-1]:.4f}"
                    )