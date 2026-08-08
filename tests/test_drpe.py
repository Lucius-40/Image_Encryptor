

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.drpe import generate_random_phase_mask, encrypt, decrypt


def test_round_trip_correct_key_recovers_image():
    """Encrypting then decrypting with the SAME keys should recover the original image."""
    rng = np.random.default_rng(0)
    image = rng.random((64, 64))  # synthetic grayscale image, values in [0, 1)

    key1 = generate_random_phase_mask(image.shape, seed=1)
    key2 = generate_random_phase_mask(image.shape, seed=2)

    cipher = encrypt(image, key1, key2)
    recovered = decrypt(cipher, key1, key2)

    assert np.allclose(image, recovered, atol=1e-8), (
        "Decryption with correct keys did not recover the original image within tolerance."
    )


def test_wrong_key_does_not_recover_image():
    """Decrypting with an incorrect key should NOT recover the original image."""
    rng = np.random.default_rng(0)
    image = rng.random((64, 64))

    key1 = generate_random_phase_mask(image.shape, seed=1)
    key2 = generate_random_phase_mask(image.shape, seed=2)
    wrong_key2 = generate_random_phase_mask(image.shape, seed=999)  # different seed

    cipher = encrypt(image, key1, key2)
    recovered_wrong = decrypt(cipher, key1, wrong_key2)

    assert not np.allclose(image, recovered_wrong, atol=1e-2), (
        "Decryption with an incorrect key unexpectedly recovered the original image."
    )


def test_ciphertext_looks_like_noise():
    """The ciphertext should show no obvious correlation with the original structure."""
    # simple gradient image -- has strong, easily-detected structure in its raw form
    image = np.tile(np.linspace(0, 1, 64), (64, 1))

    key1 = generate_random_phase_mask(image.shape, seed=1)
    key2 = generate_random_phase_mask(image.shape, seed=2)

    cipher = encrypt(image, key1, key2)
    mag = np.abs(cipher)

    # crude structure check: correlation between ciphertext magnitude and the
    # original gradient pattern should be very low
    corr = np.corrcoef(mag.flatten(), image.flatten())[0, 1]
    assert abs(corr) < 0.3, f"Ciphertext magnitude appears correlated with original image (corr={corr:.3f})"


def test_keys_are_unit_magnitude():
    """Random phase masks must have unit magnitude everywhere (phase-only)."""
    mask = generate_random_phase_mask((32, 32), seed=42)
    assert np.allclose(np.abs(mask), 1.0, atol=1e-10)


def test_different_seeds_give_different_keys():
    """Sanity check that seeding actually produces distinct masks."""
    mask_a = generate_random_phase_mask((16, 16), seed=1)
    mask_b = generate_random_phase_mask((16, 16), seed=2)
    assert not np.allclose(mask_a, mask_b)


if __name__ == "__main__":
    test_round_trip_correct_key_recovers_image()
    test_wrong_key_does_not_recover_image()
    test_ciphertext_looks_like_noise()
    test_keys_are_unit_magnitude()
    test_different_seeds_give_different_keys()
    print("All tests passed.")
