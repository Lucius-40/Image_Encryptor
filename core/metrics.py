import numpy as np
from core.drpe import decrypt, generate_perturbed_key
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
