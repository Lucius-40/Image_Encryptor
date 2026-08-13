"""
Week 5 demo script: RGB color DRPE encryption/decryption.

Run with:
    python scripts/demo2.py app_assets/mimtens.jpg

If no image path is given, a synthetic color test pattern is generated
instead, so this runs out of the box with no external image needed.

Demonstrates:
  1. Correct-key decryption (full recovery)
  2. Wrong keys on ALL channels (pure noise)
  3. Wrong key on ONLY the blue channel (color-shift failure mode,
     unique to independent per-channel keys)
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.rgb_dpre import generate_color_keys, encrypt_color, decrypt_color
from core.utils import load_color, ciphertext_magnitude_for_display


def synthetic_color_test_image(size=256):
    """Generate a colorful synthetic test pattern (used if no image is supplied)."""
    x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    r = np.clip(0.5 + 0.5 * np.sin(4 * x), 0, 1)
    g = np.clip(0.5 + 0.5 * np.cos(4 * y), 0, 1)
    b = ((x**2 + y**2) < 0.3).astype(float)
    return np.stack([r, g, b], axis=-1)


def main():
    if len(sys.argv) > 1:
        image = load_color(sys.argv[1], size=(256, 256))
    else:
        print("No image path given -- using a synthetic color test pattern.")
        image = synthetic_color_test_image()

    shape2d = image.shape[:2]
    keys = generate_color_keys(shape2d, shared=False, seed=1)
    wrong_keys = generate_color_keys(shape2d, shared=False, seed=999)
    mixed_keys = [keys[0], keys[1], wrong_keys[2]]  # correct R,G / wrong B

    cipher = encrypt_color(image, keys)
    decrypted_correct = decrypt_color(cipher, keys)
    decrypted_all_wrong = decrypt_color(cipher, wrong_keys)
    decrypted_partial_wrong = decrypt_color(cipher, mixed_keys)

    mse = np.mean((image - decrypted_correct) ** 2)
    print(f"MSE between original and decrypted (correct keys): {mse:.2e}")

    fig, axes = plt.subplots(1, 5, figsize=(20, 4))
    titles = [
        "Original",
        "Ciphertext\n(magnitude)",
        "Decrypted\n(correct keys)",
        "Decrypted\n(all keys wrong)",
        "Decrypted\n(only B key wrong)",
    ]
    panels = [
        image,
        ciphertext_magnitude_for_display(cipher),
        np.clip(decrypted_correct, 0, 1),
        np.clip(decrypted_all_wrong, 0, 1),
        np.clip(decrypted_partial_wrong, 0, 1),
    ]
    for ax, panel, title in zip(axes, panels, titles):
        ax.imshow(panel)
        ax.set_title(title)
        ax.axis("off")

    plt.tight_layout()
    output_dir = os.path.join(os.path.dirname(__file__), "..", "app_assets", "demo_outputs")
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, "demo2.png")
    plt.savefig(out_path, dpi=150)
    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()