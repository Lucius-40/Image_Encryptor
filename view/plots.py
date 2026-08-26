import matplotlib.pyplot as plt


def plot_sensitivity_curve(magnitudes, psnr_values):
    """Renders the Week 3 Key Sensitivity Curve."""
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(magnitudes, psnr_values, marker='.', color='red', linestyle='-')

    ax.set_title("DRPE Key Sensitivity Curve (The Sharp Cliff)")
    ax.set_xlabel("Error Magnitude (Additive Gaussian Noise to Key Phase)")
    ax.set_ylabel("Decryption Quality (PSNR in dB)")
    ax.grid(True, linestyle='--', alpha=0.7)

    ax.axhline(y=10, color='black', linestyle='--', label='Total Data Loss Threshold')
    ax.legend()

    return fig


def plot_robustness_curve(severity, psnr_values, title):
    """Render the Week 4 ciphertext corruption curve."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(severity, psnr_values, marker='o', linestyle='-', color='darkorange')

    ax.set_title(title)
    ax.set_xlabel("Corruption Severity")
    ax.set_ylabel("PSNR (dB)")
    ax.grid(True, linestyle='--', alpha=0.7)

    return fig


def plot_audio_sensitivity_curve(magnitudes, snr_values):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(magnitudes, snr_values, marker='o', color='royalblue', linestyle='-')
    ax.set_title("Audio Key Sensitivity Curve")
    ax.set_xlabel("Perturbation Magnitude (Gaussian Phase Noise)")
    ax.set_ylabel("Decryption Quality (SNR in dB)")
    ax.grid(True, linestyle='--', alpha=0.7)
    return fig