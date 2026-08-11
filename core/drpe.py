import numpy as np


def generate_random_phase_mask(shape, seed=None):
    rng = np.random.default_rng(seed)
    phi = rng.random(shape)
    mask = np.exp(1j * 2 * np.pi * phi)
    return mask


def generate_perturbed_key(original_key, error_magnitude):
    """
    Corrupts an existing phase mask by multiplying it with a noise phase mask.
    This works perfectly regardless of whether a seed or pure entropy was used.
    """
    #Generate Gaussian noise 
    noise = np.random.normal(loc=0.0, scale=error_magnitude, size=original_key.shape)
    
    #Wrap the noise in a complex phase mask
    noise_mask = np.exp(1j * 2 * np.pi * noise)
    
    #Apply the noise to the original key
    return original_key * noise_mask

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
