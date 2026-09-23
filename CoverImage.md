# Hide an Image Cipher Inside a Cover Image

This project can hide the DRPE image ciphertext inside another real image. The resulting image is called a **stego image**. It looks like the selected cover image, but it contains the ciphertext needed for extraction.

The recipient needs two things:

1. The generated stego PNG.
2. The encryption keys (`keys.npy`) or the same PIN used during encryption.

The original, untouched cover image is not required during extraction.

## How the Workflow Works

```text
Original image
    -> DRPE encryption
Complex ciphertext + phase keys
    -> lossless LSB embedding into a cover image
Stego PNG
    -> ciphertext extraction
Complex ciphertext
    -> DRPE decryption with the correct keys
Recovered image
```

The ciphertext is complex-valued. Both its real and imaginary components are embedded. The displayed ciphertext magnitude is only a visualization and must never be used for decryption.

## Sender Procedure

### 1. Encrypt the image

1. Start the application:

   ```powershell
   .venv\Scripts\Activate.ps1
   streamlit run app.py
   ```

2. Open **Image tools**.
3. Open **1. Encrypt**.
4. Upload the image.
5. Select one key mode:
   - **Secure Mode**: download `keys.npy` and keep it secret.
   - **Demo Mode**: remember the numeric PIN. This mode is deterministic and is intended for demonstrations, not serious security.
6. Click **Encrypt image**.

In Secure Mode, download `keys.npy`. The `.npy` file containing the ciphertext is only an intermediate input for the hiding step.

### 2. Hide the ciphertext in a cover image

1. Open **5. Hide Cipher**.
2. For **Cipher source**, choose **Use cipher from Encrypt** if the encryption was performed in the same application session. Otherwise choose **Upload cipher (.npy)** and upload the encrypted data file.
3. Select **Upload cover** and choose a real cover image, or select a preset cover.
4. Choose the LSB depth:
   - **1 bit** changes fewer cover-image bits and gives better visual preservation, but requires a larger cover.
   - **2 bits** provides more capacity, but makes slightly larger changes to the cover image.
5. Check the displayed capacity. The available cover pixels must be at least the required number.
6. Click **Embed cipher into cover**.
7. Download `stego_image.png`.

Send `stego_image.png` to the recipient. Send `keys.npy` or the PIN through a separate, trusted channel.

## Recipient Procedure

The simplest route is now to decrypt directly from the stego PNG. The separate extraction route remains available when the recipient wants to inspect or export the recovered ciphertext.

### Direct route: decrypt from the stego PNG

1. Open **2. Decrypt**.
2. Under **Cipher source**, choose **Stego image (.png)**.
3. Upload `stego_image.png`.
4. Choose **Upload Key File** and upload `keys.npy`, or choose **Enter Manual PIN** and enter the same PIN used by the sender.
5. Leave **Simulate Wrong Key Attack** disabled.
6. Click **Decrypt image**.

The application extracts the complex ciphertext from the PNG automatically and decrypts it with the supplied keys.

### 1. Extract the hidden ciphertext

1. Open **6. Extract Cipher**.
2. Upload the received `stego_image.png`.
3. Click **Extract hidden cipher**.
4. Download the extracted file, normally named `extracted_cipher.npy`.

The PNG contains a small header with the ciphertext shape, LSB depth, and the ranges needed to reconstruct the real and imaginary components. No separate steganography metadata file is required.

### 2. Decrypt the extracted image

1. Open **2. Decrypt**.
2. Upload `extracted_cipher.npy`.
3. Choose **Upload Key File** and upload `keys.npy`, or choose **Enter Manual PIN** and enter the same PIN used by the sender.
4. Leave **Simulate Wrong Key Attack** disabled.
5. Click **Decrypt image**.

With the correct keys, the original working-size image is recovered. An incorrect key or PIN produces a noisy, unusable result.

## Standalone Python Example

The following example uses the same functions as the Streamlit application. It demonstrates embedding, lossless PNG transfer, extraction, and decryption.

```python
from pathlib import Path

import cv2
import numpy as np

from core.Steganography import (
    embed_cipher_self_contained,
    extract_cipher_self_contained,
    required_cover_pixels_self_contained,
)
from core.drpe import decrypt, encrypt, generate_random_phase_mask


def read_gray(path):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image.astype(np.float64) / 255.0


def read_rgb(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


work_image = read_gray(Path("secret.png"))
cover_rgb = read_rgb(Path("cover.png"))

# DRPE encryption. Keep the raw complex ciphertext.
key1 = generate_random_phase_mask(work_image.shape, seed=101)
key2 = generate_random_phase_mask(work_image.shape, seed=102)
cipher = encrypt(work_image, key1, key2)

lsb_depth = 1
required = required_cover_pixels_self_contained(cipher.shape, lsb_depth=lsb_depth)
available = cover_rgb.shape[0] * cover_rgb.shape[1]
if available < required:
    raise ValueError(
        f"Cover is too small: {available} pixels available, {required} required"
    )

# Embed the ciphertext and write the result as PNG.
stego_rgb = embed_cipher_self_contained(
    cipher,
    cover_rgb,
    lsb_depth=lsb_depth,
)
stego_bgr = cv2.cvtColor(stego_rgb, cv2.COLOR_RGB2BGR)
if not cv2.imwrite("stego_image.png", stego_bgr):
    raise IOError("Could not write stego_image.png")

# The recipient reads the PNG and extracts the complex ciphertext.
loaded_bgr = cv2.imread("stego_image.png", cv2.IMREAD_COLOR)
if loaded_bgr is None:
    raise ValueError("Could not read stego_image.png")
loaded_rgb = cv2.cvtColor(loaded_bgr, cv2.COLOR_BGR2RGB)
extracted_cipher = extract_cipher_self_contained(loaded_rgb)

# Decrypt with the separately delivered keys.
recovered = np.clip(decrypt(extracted_cipher, key1, key2), 0.0, 1.0)
recovered_u8 = np.round(recovered * 255).astype(np.uint8)
cv2.imwrite("recovered.png", recovered_u8)

print("Cipher shape:", extracted_cipher.shape)
print("Mean absolute recovery error:", np.mean(np.abs(work_image - recovered)))
```

## Capacity Calculation

The ciphertext has one 8-bit quantized real value and one 8-bit quantized imaginary value for every ciphertext pixel. The self-contained format also stores a header.

For a ciphertext of shape `(H, W)`, the approximate number of cover pixels required is:

```text
required pixels = ceil((header bits + ceil(H * W * 16 / lsb depth)) / 3)
```

The application calculates this automatically with `required_cover_pixels_self_contained()` and displays the result before embedding.

## Important Rules

- Keep the ciphertext complex. Do not save or embed `abs(cipher)` or the displayed ciphertext magnitude.
- Use PNG for the stego image. PNG preserves the exact pixel values required by LSB extraction.
- Do not send the stego image through JPEG conversion, social-media recompression, screenshotting, resizing, or filters.
- Keep `keys.npy` or the PIN separate from the stego PNG.
- The cover image hides the ciphertext; it does not replace the DRPE keys or provide authentication.
- Use a cover image with enough pixels. A larger cover also gives more room to distribute the hidden data.
- The current UI is designed for grayscale DRPE image encryption. RGB ciphertext requires a separate per-channel container format and is not handled by the current cover-image UI.

## Resolution and Fidelity Notes

The Encrypt page limits the working image's longest side to 768 pixels. If the uploaded image is larger, encryption is performed on a resized working copy.

The normal `.npy` workflow stores the original shape and resizes the decrypted result back to it. The current self-contained stego header stores the ciphertext shape, but not the original pre-resize shape. Therefore, for the most predictable cover-image workflow, use an image whose longest side is already 768 pixels or less.

The embedding process quantizes the real and imaginary ciphertext components to 8 bits. Decryption is expected to be high quality, but it is not guaranteed to be mathematically identical to decrypting the original unquantized `.npy` ciphertext.

## Troubleshooting

### The cover is too small

Use a larger cover, select 2-bit LSB depth, or reduce the working image size before encrypting. The application will show the available and required pixel counts.

### Extraction fails

Confirm that the recipient has the original PNG produced by the application. JPEG files and modified/resized images can destroy the hidden bits.

### Decryption produces noise

Check that the recipient used the matching `keys.npy` or exactly the same PIN. Also confirm that the ciphertext magnitude was not used instead of the raw complex ciphertext.

### The recovered image has a different size

This is expected when the source image exceeded the 768-pixel working-size limit. The current stego header preserves the encrypted working shape, not the original pre-resize shape.

### The stego image looks slightly different

This is normal for LSB embedding. Use 1-bit depth for the smallest visual change. The cover is not expected to be pixel-identical after embedding.
