import streamlit as st
import numpy as np
from core.audio_drpe import decrypt_audio, generate_audio_keys
from core.audio_utils import wav_bytes_from_float_audio

def render_audio_decrypt():
    st.header("Audio Signal Decryption (1D DRPE)")
    st.write("Upload the secure matrix files to reconstruct the original audio signal.")

    key_mode = st.radio("Select Key Source:", ["Upload Key Files", "Enter Manual PIN"], horizontal=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        cipher_file = st.file_uploader("Upload Ciphertext (.npy)", type=["npy"])

    k1_file = None
    k2_file = None
    pin = None
    if key_mode == "Upload Key Files":
        with col2:
            k1_file = st.file_uploader("Upload Key 1 (.npy)", type=["npy"])
        with col3:
            k2_file = st.file_uploader("Upload Key 2 (.npy)", type=["npy"])
    else:
        with col2:
            pin = st.number_input("Enter your numeric PIN", min_value=0, max_value=999999, value=4096)
        with col3:
            st.caption("Manual PIN mode is less secure but easier to demonstrate.")

    st.divider()

    # 2. Sample Rate Configuration
    st.subheader("Playback Configuration")
    sample_rate = st.number_input(
        "Audio Sample Rate (Hz)",
        min_value=8000, max_value=48000, value=16000, step=1000,
        help="Default is 16000Hz (standard for speech data). CD quality is 44100Hz."
    )

    # 3. Execution Block
    can_run = False
    if key_mode == "Upload Key Files":
        can_run = cipher_file is not None and k1_file is not None and k2_file is not None
    else:
        can_run = cipher_file is not None

    if can_run:
        if st.button("./execute_audio_decrypt.sh", type="primary"):
            with st.spinner("Reversing 1D Fast Fourier Transform..."):
                try:
                    cipher = np.load(cipher_file)

                    if key_mode == "Upload Key Files":
                        k1 = np.load(k1_file)
                        k2 = np.load(k2_file)
                    else:
                        k1, k2 = generate_audio_keys(len(cipher), pin=pin)

                    recovered_audio_float = decrypt_audio(cipher, k1, k2)
                    audio_bytes = wav_bytes_from_float_audio(recovered_audio_float, sample_rate)

                    st.success("[ OK ] Audio signal successfully reconstructed.")
                    st.audio(audio_bytes, format="audio/wav")
                    st.download_button(
                        label="💾 Download Recovered Audio (.wav)",
                        data=audio_bytes,
                        file_name="recovered_signal.wav",
                        mime="audio/wav"
                    )
                except Exception as exc:
                    st.error(f"Audio decryption failed: {exc}")
    else:
        if key_mode == "Upload Key Files":
            st.info("Awaiting secure matrices. Please upload Ciphertext, Key 1, and Key 2.")
        else:
            st.info("Awaiting ciphertext. Upload Ciphertext and enter your PIN to continue.")
        