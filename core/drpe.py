import numpy as np


def generate_random_phase_mask(shape, seed=None):
    rng = np.random.default_rng(seed)
    phi = rng.random(shape)
    mask = np.exp(1j * 2 * np.pi * phi)
    return mask


def encrypt(image, key1, key2):
    
    image = image.astype(np.complex128)
    g = image * key1
    G = np.fft.fft2(g)
    H = G * key2
    h = np.fft.ifft2(H)

    return h


def decrypt(cipher, key1, key2):
    
    H = np.fft.fft2(cipher)
    G = H * np.conj(key2)
    g = np.fft.ifft2(G)
    f_hat = g * np.conj(key1)
    return np.real(f_hat)
