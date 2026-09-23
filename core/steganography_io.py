"""Image I/O helpers for self-contained ciphertext steganography."""

import cv2
import numpy as np

from core.Steganography import extract_cipher_self_contained


def decode_rgb_image(file_bytes):
    """Decode image bytes into an RGB uint8 array."""
    image = cv2.imdecode(
        np.frombuffer(file_bytes, dtype=np.uint8),
        cv2.IMREAD_UNCHANGED,
    )
    if image is None:
        raise ValueError("The selected file is not a readable image.")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    elif image.ndim == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError("The image must have one, three, or four channels.")
    return image


def extract_cipher_from_png(file_bytes):
    """Decode a self-contained stego PNG and recover its complex cipher."""
    stego_rgb = decode_rgb_image(file_bytes)
    return stego_rgb, extract_cipher_self_contained(stego_rgb)