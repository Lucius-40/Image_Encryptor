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
