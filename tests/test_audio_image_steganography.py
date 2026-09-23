import numpy as np
import pytest

from core.audio_drpe import decrypt_audio, encrypt_audio
from core.audio_image_steganography import (
    embed_audio_cipher_in_image,
    extract_audio_cipher_from_image,
    required_cover_pixels,
)


@pytest.mark.parametrize("lsb_depth", [1, 2])
def test_audio_cipher_round_trip_through_image(lsb_depth):
    rng = np.random.default_rng(21)
    audio = rng.uniform(-1.0, 1.0, 64)
    cipher, key1, key2 = encrypt_audio(audio, pin=2468)
    pixels = required_cover_pixels(len(cipher), lsb_depth) + 32
    cover = rng.integers(0, 256, (1, pixels, 3), dtype=np.uint8)

    stego = embed_audio_cipher_in_image(cipher, cover, 44100, lsb_depth)
    extracted, sample_rate = extract_audio_cipher_from_image(stego)
    recovered = decrypt_audio(extracted, key1, key2)

    assert sample_rate == 44100
    assert extracted.shape == cipher.shape
    assert np.mean(np.abs(audio - recovered)) < 1e-3


def test_audio_image_cipher_rejects_small_cover():
    cipher = np.ones(24, dtype=np.complex128)
    required = required_cover_pixels(len(cipher), lsb_depth=1)
    cover = np.zeros((1, required - 1, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="too small"):
        embed_audio_cipher_in_image(cipher, cover, 16000, 1)


def test_audio_image_cipher_detects_tampering():
    rng = np.random.default_rng(22)
    audio = rng.uniform(-1.0, 1.0, 32)
    cipher, _, _ = encrypt_audio(audio, pin=1357)
    pixels = required_cover_pixels(len(cipher), lsb_depth=1) + 8
    cover = rng.integers(0, 256, (1, pixels, 3), dtype=np.uint8)
    stego = embed_audio_cipher_in_image(cipher, cover, 16000, 1)
    stego.reshape(-1)[58 * 8 + 1] ^= 1

    with pytest.raises(ValueError, match="integrity check"):
        extract_audio_cipher_from_image(stego)