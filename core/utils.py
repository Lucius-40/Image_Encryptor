"""
Image I/O and display helper utilities.
"""

import numpy as np
import cv2


def load_grayscale(path, size=None):
    
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
    """"
    NOTE: this is for visualization ONLY. It discards the phase information
    needed to recover the original image -- never use this output for
    decryption, only the raw complex `cipher` array.
    """
    mag = np.abs(cipher)
    mag = mag - mag.min()
    if mag.max() > 0:
        mag = mag / mag.max()
    return mag

def load_color(path, size=None):
    """
    Returns
  
    np.ndarray (float64), shape (H, W, 3), values in [0, 1], channel order RGB
    """
    img = cv2.imread(path, cv2.IMREAD_COLOR)  # loads as BGR
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    if size is not None:
        img = cv2.resize(img, size)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # convert to RGB
    return img.astype(np.float64) / 255.0

def compute_target_size(height, width, max_dim=768):
    """
    Compute a resize target that preserves aspect ratio and caps the
    longer side at max_dim, without forcing a fixed square shape.

    If the image is already smaller than max_dim on its longer side,
    it's left at native resolution (never upscaled).

    Returns (new_width, new_height) -- note the order matches cv2.resize's
    (width, height) argument convention.
    """
    longer_side = max(height, width)
    if longer_side <= max_dim:
        new_h, new_w = height, width
    else:
        scale = max_dim / longer_side
        new_h = int(round(height * scale))
        new_w = int(round(width * scale))
    return (new_w, new_h)