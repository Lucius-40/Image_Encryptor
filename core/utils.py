"""
Image I/O and display helper utilities.
"""

import numpy as np
import cv2


def load_grayscale(path, size=None):
    """
    Load an image as grayscale, normalized to [0, 1] float64.

    Parameters
    ----------
    path : str
    size : tuple(int, int) or None
        Optional (width, height) to resize to.

    Returns
    -------
    np.ndarray (float64), values in [0, 1]
    """
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    if size is not None:
        img = cv2.resize(img, size)
    return img.astype(np.float64) / 255.0


def to_uint8(img):
    """
    Clip and convert a float image in [0,1] back to uint8 [0,255] for display/saving.
    """
    img = np.clip(img, 0, 1)
    return (img * 255).astype(np.uint8)


def ciphertext_magnitude_for_display(cipher):
    """
    Produce a viewable (real, normalized) version of a complex ciphertext
    by taking its magnitude and rescaling to [0, 1].

    NOTE: this is for visualization ONLY. It discards the phase information
    needed to recover the original image -- never use this output for
    decryption, only the raw complex `cipher` array.
    """
    mag = np.abs(cipher)
    mag = mag - mag.min()
    if mag.max() > 0:
        mag = mag / mag.max()
    return mag
