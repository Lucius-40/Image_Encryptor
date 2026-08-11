import matplotlib.pyplot as plt

def plot_sensitivity_curve(magnitudes, psnr_values):
    """Renders the Week 3 Key Sensitivity Curve."""
    fig, ax = plt.subplots(figsize=(6,3))
    ax.plot(magnitudes, psnr_values, marker='.', color='red', linestyle='-')
    
    ax.set_title("DRPE Key Sensitivity Curve (The Sharp Cliff)")
    ax.set_xlabel("Error Magnitude (Additive Gaussian Noise to Key Phase)")
    ax.set_ylabel("Decryption Quality (PSNR in dB)")
    ax.grid(True, linestyle='--', alpha=0.7)
    
    ax.axhline(y=10, color='black', linestyle='--', label='Total Data Loss Threshold')
    ax.legend()
    
    return fig