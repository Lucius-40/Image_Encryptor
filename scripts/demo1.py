import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.drpe import generate_random_phase_mask, encrypt, decrypt
from core.utils import load_grayscale, ciphertext_magnitude_for_display


def synthetic_test_image(size=256):
    """Generate a simple checkerboard + circle test pattern (used if no image is supplied)."""
    x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    checker = (np.floor(x * 4) + np.floor(y * 4)) % 2
    circle = (x**2 + y**2) < 0.3
    img = 0.3 * checker + 0.7 * circle
    return np.clip(img, 0, 1)


def main():
    if len(sys.argv) > 1:
        image = load_grayscale(sys.argv[1], size=(256, 256))
    else:
        print("No image path given -- using a synthetic test pattern.")
        image = synthetic_test_image()

    key1 = generate_random_phase_mask(image.shape, seed=1)
    key2 = generate_random_phase_mask(image.shape, seed=2)
    wrong_key2 = generate_random_phase_mask(image.shape, seed=999)

    cipher = encrypt(image, key1, key2)
    decrypted_correct = decrypt(cipher, key1, key2)
    decrypted_wrong = decrypt(cipher, key1, wrong_key2)

    mse = np.mean((image - decrypted_correct) ** 2)
    print(f"MSE between original and decrypted (correct key): {mse:.2e}")

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    axes[0].imshow(image, cmap="gray")
    axes[0].set_title("Original")

    axes[1].imshow(ciphertext_magnitude_for_display(cipher), cmap="gray")
    axes[1].set_title("Ciphertext (magnitude)")

    axes[2].imshow(np.clip(decrypted_correct, 0, 1), cmap="gray")
    axes[2].set_title("Decrypted\n(correct key)")

    axes[3].imshow(np.clip(decrypted_wrong, 0, 1), cmap="gray")
    axes[3].set_title("Decrypted\n(wrong key)")

    for ax in axes:
        ax.axis("off")

    plt.tight_layout()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "app_assets", "demo_outputs")
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, "demo1.png")
    plt.savefig(out_path, dpi=150)
    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()
