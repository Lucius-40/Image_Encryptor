import numpy as np
 
from core.drpe import generate_random_phase_mask, encrypt, decrypt

"Colored images have 3 channels , gray scaled images have 1."
"So two things to demonstrate here : We can encrypt all 3 channels with"
"the same key , or generate seperate keys for seperate channels to show what happens if 1 channel "
"is corrupted."

def generate_color_keys(shape, shared=False, seed=None):
    if shared == True :
        key1 = generate_random_phase_mask(shape,seed)
        key2 = generate_random_phase_mask(shape, seed= None if seed is None else seed + 1)

        return [(key1, key2)] * 3 

    keys = []
    for ch in range(3):
        s1 = None if seed is None else seed + 10 * ch
        s2 = None if seed is None else seed + 10 * ch + 1
        key1 = generate_random_phase_mask(shape, seed=s1)
        key2 = generate_random_phase_mask(shape, seed=s2)
        keys.append((key1, key2))
    return keys


def encrypt_color(image_rgb, keys):
    """
    np.ndarray, shape (H, W, 3), complex128
        per channel ciphertext. Same complex-data caveat as grayscale:
        preserve real+imaginary parts for correct decryption.
    """
    assert image_rgb.ndim == 3 and image_rgb.shape[2] == 3, \
        "Expected an (H, W, 3) RGB image"
    assert len(keys) == 3, "Expected 3 (key1, key2) pairs, one per channel"
 
    H, W, _ = image_rgb.shape
    cipher = np.zeros((H, W, 3), dtype=np.complex128)
    for ch in range(3):
        key1, key2 = keys[ch]
        cipher[:, :, ch] = encrypt(image_rgb[:, :, ch], key1, key2)
    return cipher

def decrypt_color(cipher_rgb, keys):
    assert cipher_rgb.ndim == 3 and cipher_rgb.shape[2] == 3, \
        "Expected an (H, W, 3) ciphertext"
    assert len(keys) == 3, "Expected 3 (key1, key2) pairs, one per channel"
 
    H, W, _ = cipher_rgb.shape
    recovered = np.zeros((H, W, 3), dtype=np.float64)
    for ch in range(3):
        key1, key2 = keys[ch]
        recovered[:, :, ch] = decrypt(cipher_rgb[:, :, ch], key1, key2)
    return recovered