import io
import numpy as np
from PIL import Image

from core.drpe import decrypt
from core.drpe import decrypt, generate_perturbed_key
from core.audio_drpe import decrypt_audio, perturb_audio_key
def calculate_psnr(original, recovered):
    """
    Calculates the psnr btn 2 images

    expects float arrays normalized btn 0.0 and 1.0
    """

    mse=np.mean((original-recovered)**2)
    if mse==0:
        return float('inf')


    max_pixel=1.0

    psnr=20*np.log10(max_pixel/np.sqrt(mse))
    return psnr


def calculate_audio_mse(original, recovered):
    return np.mean((original - recovered) ** 2)


def calculate_audio_snr_db(original, recovered, eps=1e-12):
    signal_power = np.mean(original ** 2)
    noise_power = np.mean((original - recovered) ** 2)
    if noise_power <= eps:
        return float('inf')
    return 10 * np.log10((signal_power + eps) / (noise_power + eps))


def calculate_audio_correlation(original, recovered, eps=1e-12):
    orig = np.asarray(original)
    rec = np.asarray(recovered)
    if np.std(orig) <= eps or np.std(rec) <= eps:
        return 0.0
    return float(np.corrcoef(orig, rec)[0, 1])



def run_sensitivity_batch(orig_img, cipher, k1, k2, steps=50):
    """Runs the decryption simulation across increasing error magnitudes."""
    magnitudes = np.linspace(0.0, 0.5, steps)
    psnr_values = []
    
    for mag in magnitudes:
        test_k2 = generate_perturbed_key(k2, error_magnitude=mag)
        test_recovered = decrypt(cipher, k1, test_k2)
        test_recovered_clipped = np.clip(test_recovered, 0, 1)
        
        psnr = calculate_psnr(orig_img, test_recovered_clipped)
        
        if psnr == float('inf'):
            psnr = 100 # Cap for graphing purposes
            
        psnr_values.append(psnr)
        
    return magnitudes, psnr_values


def run_audio_sensitivity_batch(orig_audio, cipher, k1, k2, steps=50, max_sigma=0.5):
    magnitudes = np.linspace(0.0, max_sigma, steps)
    snr_values = []
    mse_values = []
    corr_values = []

    for mag in magnitudes:
        test_k2 = perturb_audio_key(k2, error_magnitude=mag)
        recovered = decrypt_audio(cipher, k1, test_k2)

        snr_db = calculate_audio_snr_db(orig_audio, recovered)
        if snr_db == float('inf'):
            snr_db = 120.0

        snr_values.append(snr_db)
        mse_values.append(calculate_audio_mse(orig_audio, recovered))
        corr_values.append(calculate_audio_correlation(orig_audio, recovered))

    return magnitudes, np.array(snr_values), np.array(mse_values), np.array(corr_values)

def add_gaussian_noise(cipher, sigma):
    """Add complex Gaussian noise to the ciphertext."""
    noise = sigma * (
        np.random.randn(*cipher.shape)
        + 1j * np.random.randn(*cipher.shape)
    )
    return cipher + noise

def quantize_complex(cipher, levels=256):
    """
    Uniform quantization of the complex ciphertext.
    Larger levels = finer quantization = less damage.
    """
    magnitude = np.abs(cipher)
    max_mag = magnitude.max()
    if max_mag == 0:
        return cipher.copy()
    step = (2 * max_mag) / levels
    return np.round(cipher / step) * step


def jpeg_compress_complex(cipher, quality=50):
    """
    Simulate JPEG compression on the ciphertext magnitude only.
    Keep phase intact so decryption remains valid as a structured corruption.
    """
    mag = np.abs(cipher)
    phase = np.angle(cipher)

    mag_min = mag.min()
    mag_max = mag.max()
    if mag_max == mag_min:
        return cipher.copy()

    mag_norm = (mag - mag_min) / (mag_max - mag_min + 1e-8)
    mag_u8 = np.uint8(np.clip(mag_norm, 0, 1) * 255)

    buffer = io.BytesIO()
    Image.fromarray(mag_u8).save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    mag_jpeg = np.array(Image.open(buffer).convert("L")) / 255.0
    mag_restored = mag_jpeg * (mag_max - mag_min) + mag_min
    return mag_restored * np.exp(1j * phase)


def run_robustness_batch(orig_img, cipher, k1, k2, mode="noise", levels=None):
    """
    mode: 'noise', 'jpeg', or 'quant'
    returns (severity_values, psnr_values)
    """
    if levels is None:
        levels = np.linspace(0.01, 0.5, 20) if mode == "noise" else \
                 np.array([10, 20, 30, 40, 50, 60, 70, 80, 90]) if mode == "jpeg" else \
                 np.array([8, 16, 32, 64, 128, 256, 512, 1024])

    severity = []
    psnr_values = []

    for value in levels:
        if mode == "noise":
            corrupted = add_gaussian_noise(cipher, value)
        elif mode == "jpeg":
            corrupted = jpeg_compress_complex(cipher, quality=int(value))
        elif mode == "quant":
            corrupted = quantize_complex(cipher, levels=int(value))
        else:
            raise ValueError("Unknown robustness mode")

        recovered = np.clip(decrypt(corrupted, k1, k2), 0, 1)
        psnr_values.append(calculate_psnr(orig_img, recovered))
        severity.append(value)

    return np.array(severity), np.array(psnr_values)