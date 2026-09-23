# Audio DRPE Theory and Implementation Plan

## Scope
This document explains only the audio encryption and decryption theory for 1D Double Random Phase Encoding (DRPE), including the signal-domain mathematics and the practical implementation plan used in this project.

## 1) Signal Model
Let the normalized mono audio signal be

$$
f[n] \in [-1,1], \quad n=0,1,\dots,N-1
$$

where $N$ is the number of samples.

In implementation, the real signal is promoted to complex values before phase operations:

$$
f_c[n] = f[n] + j0
$$

## 2) Phase-Only Keys
Two unit-magnitude random phase masks are used:

$$
k_1[n] = e^{j\phi_1[n]}, \qquad k_2[n] = e^{j\phi_2[n]}
$$

with

$$
|k_1[n]| = |k_2[n]| = 1
$$

for all $n$.

### Key generation modes
- Secure random mode:
  - $\phi_1, \phi_2$ are generated from nondeterministic RNG.
- Manual PIN mode (demo mode):
  - key 1 uses seed $s=\text{PIN}$
  - key 2 uses seed $s+1$
  - this is deterministic and reproducible, but weaker from a security perspective.

## 3) 1D DRPE Encryption Mathematics
Define the 1D DFT operator as $\mathcal{F}\{\cdot\}$ and inverse DFT as $\mathcal{F}^{-1}\{\cdot\}$.

### Step A: First phase modulation
$$
g[n] = f_c[n] \cdot k_1[n]
$$

### Step B: Forward transform
$$
G[m] = \mathcal{F}\{g[n]\}
$$

### Step C: Second phase modulation in Fourier domain
$$
H[m] = G[m] \cdot k_2[m]
$$

### Step D: Inverse transform to ciphertext
$$
h[n] = \mathcal{F}^{-1}\{H[m]\}
$$

The encrypted audio representation is the complex sequence $h[n]$.

## 4) 1D DRPE Decryption Mathematics
Given ciphertext $h[n]$ and correct keys $(k_1,k_2)$:

### Step A: Forward transform
$$
H[m] = \mathcal{F}\{h[n]\}
$$

### Step B: Remove second phase key
$$
\tilde{G}[m] = H[m] \cdot k_2^*[m]
$$

### Step C: Inverse transform
$$
\tilde{g}[n] = \mathcal{F}^{-1}\{\tilde{G}[m]\}
$$

### Step D: Remove first phase key
$$
\hat{f}_c[n] = \tilde{g}[n] \cdot k_1^*[n]
$$

### Step E: Recover real audio
$$
\hat{f}[n] = \operatorname{Re}(\hat{f}_c[n])
$$

Then clip to valid playback range:

$$
\hat{f}_{clip}[n] = \min(1, \max(-1, \hat{f}[n]))
$$

## 5) Why Correct Decryption Works
Using the encryption definition:

$$
H[m] = G[m]k_2[m]
$$

Multiply by conjugate $k_2^*$:

$$
H[m]k_2^*[m] = G[m]k_2[m]k_2^*[m] = G[m]|k_2[m]|^2 = G[m]
$$

since $|k_2[m]|=1$.

Then

$$
\mathcal{F}^{-1}\{G[m]\} = g[n] = f_c[n]k_1[n]
$$

and multiplying by $k_1^*$ gives

$$
f_c[n]k_1[n]k_1^*[n] = f_c[n]|k_1[n]|^2 = f_c[n]
$$

so the original signal is recovered (up to numerical precision).

## 6) Wrong-Key Behavior
If either key is incorrect, phase cancellation is incomplete. The residual random phase causes strong distortion in reconstructed waveform and audible intelligibility collapses quickly.

## 7) Signal Processing Path Used in Code
1. Load WAV.
2. Convert stereo to mono by channel mean.
3. Normalize amplitude to $[-1,1]$.
4. Encrypt via 1D DRPE equations above.
5. Store/export ciphertext and keys as NumPy arrays.
6. Decrypt with either uploaded keys or PIN-derived keys.
7. Convert decrypted float samples to PCM16 and serialize to WAV bytes for playback/download.

## 8) Implementation Plan (Completed)
This is the completed implementation structure for audio mode support.

### A. Backend structure
- Keep DRPE mechanics unchanged:
  - encryption: multiply -> FFT -> multiply -> IFFT
  - decryption: FFT -> conjugate multiply -> IFFT -> conjugate multiply
- Separate key-generation concerns from transform steps.
- Provide helper API for audio keys:
  - random mode keys
  - PIN-seeded deterministic keys with seed=PIN and seed+1

### B. Encrypt UI behavior
- Offer two modes:
  - Secure Mode (random keys)
  - Demo Mode (manual PIN)
- In demo mode:
  - collect integer PIN in range [0, 999999]
  - derive key1 from PIN and key2 from PIN+1
- Preserve existing outputs:
  - ciphertext .npy
  - key1 .npy
  - key2 .npy

### C. Decrypt UI behavior
- Offer two key-source options:
  - Upload Key Files
  - Enter Manual PIN
- PIN mode is PIN-only:
  - derive keys from ciphertext length and PIN
  - no key file upload required
- Keep sample-rate selection and WAV output path unchanged.

### D. Validation criteria
- Round-trip recovery succeeds with correct keys/PIN.
- Decryption fails perceptually with wrong PIN.
- Existing non-audio DRPE behavior remains unaffected.
- Diagnostics pass and automated tests pass.

## 9) Complexity and Practical Notes
- FFT and IFFT dominate complexity:
  - each is $O(N\log N)$
- Total encryption/decryption complexity remains $O(N\log N)$.
- Numerical errors are expected at floating-point tolerance scale.
- Manual PIN mode is for demonstration and reproducibility, not strong key entropy.

## 10) Audio-Cover Steganography

Audio mode also supports hiding the encrypted complex ciphertext inside a
second audio file. This is separate from DRPE: DRPE protects the ciphertext,
while steganography hides the ciphertext's presence.

### Sender workflow

1. Upload and encrypt the secret WAV as usual.
2. Optionally upload a second mono WAV as the cover audio.
3. Choose an LSB depth from 1 to 4.
4. Confirm that the cover has enough samples.
5. Download `stego_audio.wav` together with the existing keys or PIN.

The stego file is written as lossless PCM16 WAV. The embedded payload contains
a versioned header, the secret sample rate, ciphertext length, quantization
ranges, payload length, and a CRC32 checksum. The ciphertext's real and
imaginary components are stored as quantized unsigned 16-bit values.

### Recipient workflow

1. Open Audio Decryption.
2. Choose **Stego Audio (.wav)** as the cipher source.
3. Upload `stego_audio.wav`.
4. Upload the two keys or enter the original PIN.
5. Decrypt the audio.

The sample rate is recovered from the embedded header, so it does not need to
be entered manually for stego audio. The original `.npy` ciphertext workflow
continues to use the existing manual sample-rate field.

### Format and capacity requirements

- Use mono PCM WAV cover audio.
- Do not convert the stego WAV to MP3, AAC, or another lossy format.
- Do not edit, resample, normalize, or trim the stego WAV after embedding.
- A cover sample stores 1 to 4 hidden bits depending on the selected depth.
- Higher LSB depth provides more capacity but causes more audible cover noise.
- The cover must be longer than the secret audio because each ciphertext sample
  contains both real and imaginary components.
- The correct DRPE keys or PIN are still required; the cover audio is not a key.

## 11) Audio Cipher Hidden in a Cover Image

The encrypted audio ciphertext can also be hidden inside an ordinary RGB image.
This does not convert the audio into a lossy spectrogram. The application stores
the complex ciphertext itself inside the image pixels.

### Sender workflow

1. Upload and encrypt the secret WAV.
2. Upload an image under **Optional: upload a cover image to hide the encrypted audio**.
3. Select image LSB depth 1 or 2.
4. Confirm that the image has enough pixels.
5. Download `audio_stego_image.png` together with the keys or PIN.

### Recipient workflow

1. Open Audio Decryption.
2. Select **Stego Image (.png)** as the cipher source.
3. Upload `audio_stego_image.png`.
4. Upload both keys or enter the original PIN.
5. Click **Decrypt audio**.

The PNG header restores the ciphertext length and sample rate automatically.
PNG must remain lossless: do not convert the stego image to JPEG, resize it,
or pass it through a service that recompresses or modifies image pixels.

The image cover is concealment only. It does not replace the DRPE keys, and the
correct keys or PIN are still required for audio recovery.
