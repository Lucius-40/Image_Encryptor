import numpy as np
import pytest

from core.audio_drpe import decrypt_audio, encrypt_audio
from core.audio_steganography import (
    embed_audio_cipher,
    extract_audio_cipher,
    required_cover_samples,
)


@pytest.mark.parametrize("lsb_depth", [1, 2, 4])
def test_audio_cipher_round_trip(lsb_depth):
    rng = np.random.default_rng(7)
    audio = rng.uniform(-1.0, 1.0, 64)
    cipher, key1, key2 = encrypt_audio(audio, pin=1234)
    cover_length = required_cover_samples(len(cipher), lsb_depth) + 32
    cover = rng.uniform(-1.0, 1.0, cover_length)

    stego = embed_audio_cipher(cipher, cover, sample_rate=44100, lsb_depth=lsb_depth)
    extracted, sample_rate = extract_audio_cipher(stego)
    recovered = decrypt_audio(extracted, key1, key2)

    assert sample_rate == 44100
    assert extracted.shape == cipher.shape
    assert np.mean(np.abs(audio - recovered)) < 1e-3


def test_audio_cipher_rejects_short_cover():
    cipher = np.ones(32, dtype=np.complex128)
    required = required_cover_samples(len(cipher), lsb_depth=1)

    with pytest.raises(ValueError, match="too short"):
        embed_audio_cipher(cipher, np.zeros(required - 1), sample_rate=16000)


def test_audio_cipher_detects_tampering():
    rng = np.random.default_rng(9)
    audio = rng.uniform(-1.0, 1.0, 32)
    cipher, _, _ = encrypt_audio(audio, pin=55)
    cover = rng.uniform(-1.0, 1.0, required_cover_samples(len(cipher)) + 8)
    stego = embed_audio_cipher(cipher, cover, sample_rate=16000)
    stego[required_cover_samples(len(cipher)) - 1] ^= 1

    with pytest.raises(ValueError, match="integrity check"):
        extract_audio_cipher(stego)