# Fourier-Domain Image Encryptor — Project Plan

## Theoretical Background: Double Random Phase Encoding (DRPE)

### The core idea

DRPE was introduced by Refregier and Javidi (1995) as an optical encryption scheme, later adapted to digital/algorithmic implementations. The trick is to convert a structured image into something statistically indistinguishable from white noise, using two random phase masks and a Fourier transform pair.

### Step-by-step signal flow

**1. Represent the image as a complex field**

Let the input image be f(x,y), a real-valued (grayscale) function. Treat it as the amplitude of a complex signal with zero phase to start.

**2. First random phase mask (spatial domain)**

Generate a random phase mask:

    n1(x,y) = exp(j * 2π * φ1(x,y))

where φ1(x,y) is a matrix of i.i.d. uniform random values in [0,1). This is the **first key**. Multiply it elementwise with the image:

    g(x,y) = f(x,y) · n1(x,y)

This doesn't change the magnitude of any pixel — it randomizes phase only. Visually, if you looked at just this step's magnitude, it would look unchanged. The randomness is hidden in the phase.

**3. Fourier transform**

Take the 2D DFT:

    G(u,v) = F{ g(x,y) }

This is where the convolution theorem becomes relevant for the course requirement: multiplying by a random phase in the spatial domain is equivalent to *convolving* the image's spectrum with the random mask's spectrum in the frequency domain. That convolution is what starts smearing structured frequency content into noise.

**4. Second random phase mask (frequency domain)**

Generate a second independent random phase mask n2(u,v) = exp(j * 2π * φ2(u,v)) — the **second key**. Multiply:

    H(u,v) = G(u,v) · n2(u,v)

**5. Inverse Fourier transform**

    h(x,y) = F^-1{ H(u,v) }

This is the ciphertext. Because h(x,y) is generally complex, in practice you either store both magnitude and phase (as two real arrays), or store the real and imaginary parts, or map to a viewable format some other way — this is a design decision that needs to be made explicit in the implementation (a common trick is to display magnitude only for visualization, but retain full complex data for correct decryption).

### Decryption

Decryption reverses each step exactly, requiring both n1 and n2:

    ĝ(x,y) = F^-1{ F{h(x,y)} · n2*(u,v) }
    f̂(x,y) = ĝ(x,y) · n1*(x,y)

where n2* and n1* denote complex conjugates (which, for a unit-magnitude phase-only mask, is the same as exp(-j * 2π * φ) — the inverse phase shift). Since |n1| = |n2| = 1 everywhere, multiplying and then multiplying by the conjugate perfectly cancels, and f(x,y) is recovered exactly (up to floating-point error).

### Why an incorrect key gives noise

If a wrong key n2' ≠ n2 is used during decryption, the mismatch means n2'* · n2 ≠ 1 — it's some other complex value with essentially random phase across the array. This residual random phase term doesn't cancel, and when you inverse-transform something with an effectively-random phase spectrum, the result is close to white noise in the spatial domain. This is essentially why phase carries most of the perceptually meaningful structure of an image (a well-known result in Fourier image processing: swap magnitude and phase between two images, and the result looks like the image the phase came from, not the one the magnitude came from). This is the property that makes the "decryption failure under wrong key" demo visually striking.

### Where the convolution theorem comes in explicitly

The one-line argument for *why* this scrambles the image, not just *that* it does: multiplying by n1(x,y) in the spatial domain corresponds to convolving F(u,v) (the image's own spectrum) with N1(u,v) (the random mask's spectrum) in the frequency domain:

    F{ f · n1 } = F * N1   (convolution)

Since N1 is the transform of random noise, it has energy spread across essentially all frequencies. Convolving the image's (typically concentrated, low-frequency-heavy) spectrum with this broadband kernel spreads the image's energy across the whole frequency plane — which is exactly what "encryption" needs to do to a signal to make it look random.

### Security properties worth knowing (useful for the report)

- **Key space**: the keys are the full phase masks (as large as the image itself), giving an enormous key space — brute-forcing a key is infeasible for realistic image sizes.
- **Known vulnerability**: DRPE is linear (it's just multiplications and Fourier transforms), so it's known in the literature to be vulnerable to *known-plaintext attacks* using techniques like phase retrieval algorithms (e.g., iterative Gerchberg–Saxton-style attacks can sometimes recover the keys if an attacker has plaintext-ciphertext pairs). Good to mention in the report as a limitation/future work item — shows depth without needing to implement an attack.
- **Motivates the "robustness under noise/compression" extension**: DRPE's decryption is exact and unforgiving — even small quantization error (like from JPEG compression) in the ciphertext can degrade decryption quality since there's no error correction built in. Testing this is a legitimate and interesting extension.

---

## 6-Week Roadmap

| Week | Milestone | Details |
|---|---|---|
| **1** | Core DRPE engine + repo setup | Implement `encrypt(img, key1, key2)` / `decrypt(cipher, key1, key2)` in `core/`. Test on a single grayscale image. Confirm bit-exact (or near floating-point) recovery with correct keys, and visually confirm noise with wrong keys. Repo scaffolding, venv, first PRs merged. |
| **2** | Streamlit GUI v1 | Build `app.py`: upload image, generate/display random keys, show original / encrypted / decrypted side by side. Add a "use wrong key" toggle to demonstrate decryption failure live. |
| **3** | Key-sensitivity analysis | Quantitatively perturb one key (e.g., small Gaussian perturbation on φ2) and measure decryption quality (MSE, correlation coefficient, or PSNR) vs. perturbation magnitude. Plot the sensitivity curve — likely a very sharp cliff, a strong result to show. Add this as an interactive Streamlit panel with a slider. |
| **4** | Robustness testing | Simulate ciphertext corruption: additive noise, JPEG compression at various quality levels, quantization. Measure decrypted-image degradation (PSNR/SSIM) vs. corruption severity. This is where DRPE's fragility is shown empirically — a legitimate, interesting negative result. |
| **5** | Extension (color / multi-image) | Pick one, given time: (a) extend to RGB by applying DRPE per-channel or on a luminance-preserving transform, or (b) multi-image encryption (multiplex several images into one ciphertext using distinct key pairs — a known DRPE variant). Scope this realistically based on how weeks 1–4 went. |
| **6** | Polish, report, and demo prep | Finalize GUI, write up the theory + convolution-theorem justification + experimental results (sensitivity curves, robustness plots) into the report. Rehearse the live demo: correct decryption, wrong-key noise, and at least one extension result. |

### Pacing notes

- Weeks 1–2 are the highest-risk part — get the core algorithm numerically correct first (write a unit test asserting `decrypt(encrypt(img, k1, k2), k1, k2) ≈ img` within floating-point tolerance) before touching the GUI.
- Weeks 3–4 are where most of the "signal processing depth" grade will come from — don't compress them if week 5's extension is optional/stretch.
- If short on time by week 5, dropping the color/multi-image extension entirely and instead deepening the robustness analysis (e.g., testing multiple noise types: Gaussian, salt-and-pepper, quantization) is a safe fallback that still satisfies "sufficient depth."

---

## Tech Stack (for reference)

- **Language**: Python
- **Core signal processing**: NumPy / SciPy (`np.fft.fft2`, `fftshift`)
- **Image I/O**: OpenCV (`opencv-python`) or Pillow
- **Visualization / experiments**: Matplotlib
- **GUI**: Streamlit
- **Repo structure**:
  - `core/` — DRPE algorithm, phase mask generation, encryption/decryption functions
  - `app.py` — Streamlit GUI, imports from `core/`
  - `notebooks/` — experiments, key-sensitivity analysis, plots for the report
  - `tests/` — sanity checks (e.g., round-trip correctness test)