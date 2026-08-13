

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.rgb_dpre import generate_color_keys, encrypt_color, decrypt_color


def test_round_trip_correct_keys_recovers_color_image():
    """Correct independent per-channel keys should recover the image exactly."""
    rng = np.random.default_rng(0)
    image = rng.random((32, 32, 3))

    keys = generate_color_keys(image.shape[:2], shared=False, seed=1)
    cipher = encrypt_color(image, keys)
    recovered = decrypt_color(cipher, keys)

    assert np.allclose(image, recovered, atol=1e-8)


def test_round_trip_shared_keys_recovers_color_image():
    """Shared (reused) keys across channels should also recover the image exactly."""
    rng = np.random.default_rng(0)
    image = rng.random((32, 32, 3))

    keys = generate_color_keys(image.shape[:2], shared=True, seed=1)
    cipher = encrypt_color(image, keys)
    recovered = decrypt_color(cipher, keys)

    assert np.allclose(image, recovered, atol=1e-8)


def test_wrong_keys_all_channels_gives_noise():
    """Wrong keys on all 3 channels should fail to recover the image."""
    rng = np.random.default_rng(0)
    image = rng.random((32, 32, 3))

    keys = generate_color_keys(image.shape[:2], shared=False, seed=1)
    wrong_keys = generate_color_keys(image.shape[:2], shared=False, seed=999)

    cipher = encrypt_color(image, keys)
    recovered_wrong = decrypt_color(cipher, wrong_keys)

    assert not np.allclose(image, recovered_wrong, atol=1e-2)


def test_partial_wrong_key_only_breaks_that_channel():
    """
    With independent per-channel keys, using the wrong key on ONLY the blue
    channel should still recover red and green correctly, while blue fails.
    This demonstrates the color-shift failure mode unique to independent keys.
    """
    rng = np.random.default_rng(0)
    image = rng.random((32, 32, 3))

    keys = generate_color_keys(image.shape[:2], shared=False, seed=1)
    wrong_keys = generate_color_keys(image.shape[:2], shared=False, seed=999)

    # correct keys on R, G; wrong key on B
    mixed_keys = [keys[0], keys[1], wrong_keys[2]]

    cipher = encrypt_color(image, keys)
    recovered = decrypt_color(cipher, mixed_keys)

    assert np.allclose(image[:, :, 0], recovered[:, :, 0], atol=1e-8), "Red channel should recover correctly"
    assert np.allclose(image[:, :, 1], recovered[:, :, 1], atol=1e-8), "Green channel should recover correctly"
    assert not np.allclose(image[:, :, 2], recovered[:, :, 2], atol=1e-2), "Blue channel should NOT recover"


if __name__ == "__main__":
    test_round_trip_correct_keys_recovers_color_image()
    test_round_trip_shared_keys_recovers_color_image()
    test_wrong_keys_all_channels_gives_noise()
    test_partial_wrong_key_only_breaks_that_channel()
    print("All tests passed.")