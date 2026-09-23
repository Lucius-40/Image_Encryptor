import streamlit as st
import numpy as np
import io
import time
import matplotlib.pyplot as plt
import cv2
from scipy.io import wavfile

from core.audio_drpe import encrypt_audio, decrypt_audio, perturb_audio_key
from core.audio_image_steganography import (
    embed_audio_cipher_in_image,
    required_cover_pixels as required_audio_image_pixels,
)
from core.audio_steganography import embed_audio_cipher, required_cover_samples
from core.audio_utils import load_and_normalize_audio, wav_bytes_from_float_audio
from core.steganography_io import decode_rgb_image
from core.metrics import (
    calculate_audio_snr_db,
    calculate_audio_mse,
    calculate_audio_correlation,
    run_audio_sensitivity_batch,
)
from view.plots import plot_audio_sensitivity_curve


def _wav_bytes_from_pcm16(audio, sample_rate):
    buffer = io.BytesIO()
    wavfile.write(buffer, int(sample_rate), np.asarray(audio, dtype=np.int16))
    return buffer.getvalue()


def _png_bytes_from_rgb(image):
    success, encoded = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not success:
        raise ValueError("Could not encode the audio stego image as PNG.")
    return encoded.tobytes()


# --- 1. THE AUDIO MODAL POP-UP (The "Wow" Factor) ---
@st.dialog("Audio encryption results", width="large")
def render_audio_output_modal(
    orig_audio,
    sr,
    cipher,
    k1,
    k2,
    key_mode,
    pin,
    stego_bytes=None,
    stego_image_bytes=None,
):
    st.success("Audio encryption complete.")
    
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
    
    ax[0].plot(orig_audio[:1000], color='#2563EB')
    ax[0].set_title("Original waveform", color='#1E293B')
    ax[0].set_facecolor('#FFFFFF')
    ax[0].axis('off')
    
    ax[1].plot(cipher_playable[:1000], color='#2563EB')
    ax[1].set_title("Encrypted waveform", color='#1E293B')
    ax[1].set_facecolor('#FFFFFF')
    ax[1].axis('off')
    
    fig.patch.set_facecolor('#FFFFFF')
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

    if stego_bytes is not None:
        st.download_button(
            "🎵 Download Stego Audio (.wav)",
            data=stego_bytes,
            file_name="stego_audio.wav",
            mime="audio/wav",
            use_container_width=True,
        )

    if stego_image_bytes is not None:
        st.image(stego_image_bytes, caption="Audio ciphertext hidden in cover image")
        st.download_button(
            "🖼️ Download Audio Stego Image (.png)",
            data=stego_image_bytes,
            file_name="audio_stego_image.png",
            mime="image/png",
            use_container_width=True,
        )


# --- Main audio view ---
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
            
    # Encryption controls
    else:
        st.success("Audio file loaded successfully.")
        st.subheader("Input Audio Preview")
        st.audio(st.session_state['audio_bytes'], format="audio/wav")
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

        cover_audio_file = st.file_uploader(
            "Optional: upload a cover WAV to hide the encrypted audio",
            type=["wav"],
            key="audio_cover_upload",
            help="The cover must be long enough to hold the encrypted ciphertext.",
        )
        lsb_depth = st.select_slider(
            "Audio steganography LSB depth",
            options=[1, 2, 3, 4],
            value=1,
            key="audio_steg_lsb_depth",
        )

        cover_image_file = st.file_uploader(
            "Optional: upload a cover image to hide the encrypted audio",
            type=["png", "jpg", "jpeg", "bmp"],
            key="audio_cover_image_upload",
            help="The cover image must have enough pixels for the encrypted audio payload.",
        )
        image_lsb_depth = st.select_slider(
            "Audio-in-image LSB depth",
            options=[1, 2],
            value=1,
            key="audio_image_steg_lsb_depth",
        )

        cover_image = None
        if cover_image_file is not None:
            try:
                _, secret_audio_for_image = load_and_normalize_audio(
                    io.BytesIO(st.session_state["audio_bytes"])
                )
                cover_image = decode_rgb_image(cover_image_file.getvalue())
                required_pixels = required_audio_image_pixels(
                    len(secret_audio_for_image), image_lsb_depth
                )
                available_pixels = cover_image.shape[0] * cover_image.shape[1]
                st.caption(
                    f"Image capacity: {available_pixels:,} pixels available / "
                    f"{required_pixels:,} required"
                )
                st.image(cover_image, caption="Cover image preview", use_container_width=True)
                if available_pixels < required_pixels:
                    st.warning(
                        "The cover image is too small. Choose a larger image or increase "
                        "the image LSB depth."
                    )
            except Exception as error:
                st.error(f"Could not read the cover image: {error}")
                cover_image = None

        cover_audio = None
        cover_sample_rate = None
        if cover_audio_file is not None:
            try:
                _, secret_audio = load_and_normalize_audio(
                    io.BytesIO(st.session_state["audio_bytes"])
                )
                cover_sample_rate, cover_audio = load_and_normalize_audio(
                    io.BytesIO(cover_audio_file.getvalue())
                )
                required = required_cover_samples(len(secret_audio), lsb_depth)
                available = len(cover_audio)
                st.caption(
                    f"Cover capacity: {available:,} samples available / "
                    f"{required:,} required"
                )
                st.audio(cover_audio_file.getvalue(), format="audio/wav")
                if available < required:
                    st.warning("The cover WAV is too short. Choose a longer cover or increase LSB depth.")
            except Exception as error:
                st.error(f"Could not read the cover WAV: {error}")
                cover_audio = None

        col_exec, col_clear = st.columns([3, 1])
        with col_exec:
            encrypt_btn = st.button("Encrypt audio", type="primary", use_container_width=True)
        with col_clear:
            if st.button("Clear audio", use_container_width=True):
                st.session_state['audio_bytes'] = None
                st.session_state['audio_cipher'] = None
                st.session_state['audio_signal'] = None
                st.rerun()

        # Math Execution & Trigger Modal
        if encrypt_btn:
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
            
            stego_bytes = None
            if cover_audio_file is not None and cover_audio is not None:
                try:
                    stego_audio = embed_audio_cipher(
                        cipher,
                        cover_audio,
                        sample_rate=sr,
                        lsb_depth=lsb_depth,
                    )
                    stego_bytes = _wav_bytes_from_pcm16(stego_audio, cover_sample_rate)
                except (TypeError, ValueError) as error:
                    st.error(f"Could not hide the encrypted audio in the cover WAV: {error}")

            stego_image_bytes = None
            if cover_image_file is not None and cover_image is not None:
                try:
                    stego_image = embed_audio_cipher_in_image(
                        cipher,
                        cover_image,
                        sample_rate=sr,
                        lsb_depth=image_lsb_depth,
                    )
                    stego_image_bytes = _png_bytes_from_rgb(stego_image)
                except (TypeError, ValueError) as error:
                    st.error(f"Could not hide the encrypted audio in the cover image: {error}")

            # Fire the Modal
            render_audio_output_modal(
                audio_signal,
                sr,
                cipher,
                k1,
                k2,
                key_mode,
                pin,
                stego_bytes,
                stego_image_bytes,
            )

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