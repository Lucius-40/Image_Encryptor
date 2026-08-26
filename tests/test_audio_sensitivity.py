import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.audio_drpe import encrypt_audio, perturb_audio_key
from core.metrics import run_audio_sensitivity_batch


def test_audio_key_perturbation_preserves_unit_magnitude():
    key = np.exp(1j * 2 * np.pi * np.random.default_rng(0).random(128))
    perturbed = perturb_audio_key(key, error_magnitude=0.15)
    assert np.allclose(np.abs(perturbed), 1.0, atol=1e-10)


def test_audio_sensitivity_batch_returns_expected_shapes():
    rng = np.random.default_rng(1)
    signal = rng.uniform(-1.0, 1.0, 512)
    cipher, k1, k2 = encrypt_audio(signal, pin=4096)

    magnitudes, snr_values, mse_values, corr_values = run_audio_sensitivity_batch(
        signal,
        cipher,
        k1,
        k2,
        steps=25,
        max_sigma=0.5,
    )

    assert len(magnitudes) == 25
    assert len(snr_values) == 25
    assert len(mse_values) == 25
    assert len(corr_values) == 25
    assert np.isclose(magnitudes[0], 0.0)
    assert np.isclose(magnitudes[-1], 0.5)


def test_audio_sensitivity_degrades_with_higher_perturbation():
    np.random.seed(0)
    rng = np.random.default_rng(2)
    signal = rng.uniform(-1.0, 1.0, 1024)
    cipher, k1, k2 = encrypt_audio(signal, pin=4096)

    magnitudes, snr_values, mse_values, corr_values = run_audio_sensitivity_batch(
        signal,
        cipher,
        k1,
        k2,
        steps=40,
        max_sigma=0.5,
    )

    assert magnitudes[0] < magnitudes[-1]
    assert snr_values[0] > snr_values[-1]
    assert mse_values[0] < mse_values[-1]
    assert corr_values[0] > corr_values[-1]
