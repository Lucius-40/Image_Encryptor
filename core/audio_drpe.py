import numpy as np
from core.audio_utils import load_and_normalize_audio


def generate_audio_phase_mask(length, seed=None):
    rng = np.random.default_rng(seed)
    phi = rng.random(length)
    return np.exp(1j * 2 * np.pi * phi)


def generate_audio_keys(signal_length, pin=None):
    if pin is None:
        key1 = generate_audio_phase_mask(signal_length)
        key2 = generate_audio_phase_mask(signal_length)
        return key1, key2

    base_seed = int(pin)
    key1 = generate_audio_phase_mask(signal_length, seed=base_seed)
    key2 = generate_audio_phase_mask(signal_length, seed=base_seed + 1)
    return key1, key2


def perturb_audio_key(original_key, error_magnitude):
    noise = np.random.normal(loc=0.0, scale=error_magnitude, size=original_key.shape)
    noise_mask = np.exp(1j * 2 * np.pi * noise)
    return original_key * noise_mask


def encrypt_audio(audio_signal, pin=None):
    "applies drpe to audio array"

    signal_length = len(audio_signal)
    k1, k2 = generate_audio_keys(signal_length, pin=pin)

    step1 = audio_signal * k1
    step2 = np.fft.fft(step1)
    ciphertext = np.fft.ifft(step2 * k2)

    return ciphertext, k1, k2


def decrypt_audio(ciphertext, k1, k2):
    step1 = np.fft.fft(ciphertext)
    step2 = np.fft.ifft(step1 * np.conj(k2))
    recovered_complex = step2 * np.conj(k1)

    recovered_audio = np.real(recovered_complex)

    return np.clip(recovered_audio, -1.0, 1.0)
