import streamlit as st
import numpy as np
import io
from core.audio_drpe import encrypt_audio, decrypt_audio, perturb_audio_key
from core.audio_utils import load_and_normalize_audio, wav_bytes_from_float_audio
from core.metrics import (
    calculate_audio_snr_db,
    calculate_audio_mse,
    calculate_audio_correlation,
    run_audio_sensitivity_batch,
)
from view.plots import plot_audio_sensitivity_curve

def render_audio_encrypt():
    st.header("Audio Signal Encryption (1D DRPE)")

    # 1. State Management
    if 'audio_bytes' not in st.session_state:
        st.session_state['audio_bytes'] = None
    if 'audio_cipher' not in st.session_state:
        st.session_state['audio_cipher'] = None
        st.session_state['audio_k1'] = None
        st.session_state['audio_k2'] = None

    # 2. Upload Block
    if st.session_state['audio_bytes'] is None:
        uploaded_audio = st.file_uploader("Upload a .wav file", type=["wav"])
        if uploaded_audio is not None:
            st.session_state['audio_bytes'] = uploaded_audio.getvalue()
            st.rerun()
            
    # 3. Execution Terminal
    else:
        st.success("[ OK ] Audio payload loaded into secure memory.")

        audio_io = io.BytesIO(st.session_state['audio_bytes'])
        st.audio(audio_io, format="audio/wav")

        st.subheader("Security Settings")
        key_mode = st.radio(
            "Select Key Generation Method:",
            ["Secure Mode (Export Key Files)", "Demo Mode (Manual PIN)"],
            horizontal=True,
        )

        pin = None
        if key_mode == "Demo Mode (Manual PIN)":
            pin = st.number_input("Enter a numeric PIN (e.g., 4096)", min_value=0, max_value=999999, value=4096)
            st.caption("Using a low-entropy PIN is less secure and intended for demonstrations.")

        col_exec, col_clear = st.columns([3, 1])
        with col_exec:
            execute_btn = st.button("./execute_audio_encrypt.sh", type="primary")
        with col_clear:
            if st.button("rm payload"):
                st.session_state['audio_bytes'] = None
                st.session_state['audio_cipher'] = None
                st.session_state['audio_k1'] = None
                st.session_state['audio_k2'] = None
                st.session_state['audio_signal'] = None
                st.session_state['audio_sr'] = None
                st.rerun()

        # 4. Math Execution (Saves to state)
        if execute_btn:
            with st.spinner("Processing 1D Fast Fourier Transform..."):
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
                st.rerun() 

        # 5. Persistent Download UI
        if st.session_state['audio_cipher'] is not None:
            st.success("[ OK ] Signal Encrypted. Ready for extraction.")

            if st.session_state.get('audio_key_mode') == "Demo Mode (Manual PIN)":
                st.info(f"Remember your PIN ({st.session_state.get('audio_pin')}) for manual decryption.")

            dl1, dl2, dl3 = st.columns(3)

            def array_to_bytes(arr):
                buf = io.BytesIO()
                np.save(buf, arr)
                return buf.getvalue()
            
            with dl1:
                st.download_button("💾 Ciphertext (.npy)", array_to_bytes(st.session_state['audio_cipher']), "audio_cipher.npy")
            with dl2:
                st.download_button("🔑 Key 1 (.npy)", array_to_bytes(st.session_state['audio_k1']), "audio_key1.npy")
            with dl3:
                st.download_button("🔑 Key 2 (.npy)", array_to_bytes(st.session_state['audio_k2']), "audio_key2.npy")

            st.divider()
            st.subheader("Audio Key Sensitivity Analysis")
            st.write("Quantitatively perturb Key 2 with Gaussian phase noise and measure decryption quality.")

            if st.session_state.get('audio_signal') is None and st.session_state.get('audio_bytes') is not None:
                analysis_io = io.BytesIO(st.session_state['audio_bytes'])
                analysis_io.seek(0)
                sr_tmp, signal_tmp = load_and_normalize_audio(analysis_io)
                st.session_state['audio_sr'] = sr_tmp
                st.session_state['audio_signal'] = signal_tmp

            orig_audio = st.session_state.get('audio_signal')
            audio_sr = st.session_state.get('audio_sr', 16000)
            cipher = st.session_state['audio_cipher']
            k1 = st.session_state['audio_k1']
            k2 = st.session_state['audio_k2']

            if orig_audio is None:
                st.warning("Original audio signal was not found in session. Re-run encryption to enable analysis.")
                return

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

            a1, a2 = st.columns(2)
            with a1:
                st.caption("Original (Normalized)")
                st.audio(wav_bytes_from_float_audio(orig_audio, int(audio_sr)), format="audio/wav")
            with a2:
                st.caption("Recovered After Key Perturbation")
                st.audio(wav_bytes_from_float_audio(recovered_preview, int(audio_sr)), format="audio/wav")

            st.divider()
            steps = st.slider("Sensitivity Sweep Steps", min_value=10, max_value=200, value=50, step=10)

            if st.button("Plot Audio Sensitivity Curve", type="primary"):
                with st.spinner(f"Running {steps} decryption trials..."):
                    mags, snr_values, mse_values, corr_values = run_audio_sensitivity_batch(
                        orig_audio,
                        cipher,
                        k1,
                        k2,
                        steps=steps,
                        max_sigma=0.5,
                    )
                    fig = plot_audio_sensitivity_curve(mags, snr_values)
                    st.pyplot(fig)

                    st.caption(
                        f"Final point at sigma={mags[-1]:.2f}: "
                        f"SNR={snr_values[-1]:.2f} dB, "
                        f"MSE={mse_values[-1]:.6f}, "
                        f"Corr={corr_values[-1]:.4f}"
                    )