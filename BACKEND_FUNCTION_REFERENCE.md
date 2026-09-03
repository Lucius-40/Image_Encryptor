# Backend Function Reference

This document describes the public Python functions in `core/` and the data contracts needed to build a Streamlit frontend from scratch.

## 1. Backend Overview

The backend implements Double Random Phase Encoding (DRPE) for:

- grayscale images with 2-D FFTs;
- RGB images by encrypting each channel independently;
- mono audio with a 1-D FFT;
- key sensitivity and ciphertext robustness experiments;
- image and WAV conversion helpers.

All image values used by the encryption functions should be floating-point values in `[0, 1]`. Audio values should be floating-point samples in `[-1, 1]`. Keys are complex NumPy arrays with unit magnitude. Keep ciphertext complex: displaying only its magnitude is lossy and cannot be used for decryption.

## 2. Module Map

| Directory | File | Responsibility |
|---|---|---|
| `core/` | `drpe.py` | Grayscale phase masks, image encryption/decryption, key perturbation |
| `core/` | `rgb_dpre.py` | RGB key management and per-channel encryption/decryption |
| `core/` | `audio_drpe.py` | Audio phase masks, key management, audio encryption/decryption |
| `core/` | `audio_utils.py` | WAV loading, normalization, PCM conversion, WAV bytes |
| `core/` | `metrics.py` | PSNR, audio metrics, sensitivity, and robustness experiments |
| `core/` | `utils.py` | Image loading, display conversion, resize sizing |

`core/__init__.py` is empty and exports no functions.

## 3. Common Data Conventions

### Images

| Object | Expected type | Expected shape | Value/dtype requirements |
|---|---|---|---|
| Grayscale image | `numpy.ndarray` | `(H, W)` | Real, normally `float64`, normalized to `[0, 1]` |
| RGB image | `numpy.ndarray` | `(H, W, 3)` | Real, normally `float64`, RGB channel order, normalized to `[0, 1]` |
| Grayscale key | `numpy.ndarray` | `(H, W)` | `complex128`, approximately unit magnitude |
| RGB key set | `list[tuple[np.ndarray, np.ndarray]]` | length `3` | One `(key1, key2)` pair for each R, G, and B channel |
| Grayscale ciphertext | `numpy.ndarray` | `(H, W)` | `complex128`; preserve real and imaginary components |
| RGB ciphertext | `numpy.ndarray` | `(H, W, 3)` | `complex128`; preserve real and imaginary components |

`H` and `W` must match between an image, its keys, and its ciphertext. They can be any positive image dimensions; they do not need to be square.

### Audio

| Object | Expected type | Expected shape | Value/dtype requirements |
|---|---|---|---|
| Audio signal | `numpy.ndarray` | `(N,)` | Mono, real, normalized to `[-1, 1]` |
| Audio key | `numpy.ndarray` | `(N,)` | `complex128`, approximately unit magnitude |
| Audio ciphertext | `numpy.ndarray` | `(N,)` | `complex128`; preserve real and imaginary components |
| Sample rate | `int` | scalar | Samples per second, commonly 8000-48000 |

`N` is the number of audio samples. The two audio keys and ciphertext must have the same length.

## 4. Grayscale Image Functions

### `core.drpe.generate_random_phase_mask`

```python
generate_random_phase_mask(shape, seed=None)
```

- **Directory:** `core/`
- **File:** `drpe.py`
- **Inputs:** `shape` is a tuple or sequence of `int`, normally `(H, W)`. `seed` is an optional `int` or NumPy-compatible random seed; `None` uses random entropy.
- **Returns:** `numpy.ndarray`, dtype `complex128`, shape equal to `shape`.
- **Meaning:** A random phase mask whose elements have magnitude approximately `1`.
- **Frontend use:** Generate two masks with the image shape. For reproducible PIN mode, use `seed=pin` for key 1 and `seed=pin + 1` for key 2.

### `core.drpe.generate_perturbed_key`

```python
generate_perturbed_key(original_key, error_magnitude)
```

- **Directory:** `core/`
- **File:** `drpe.py`
- **Inputs:** `original_key` is a complex `numpy.ndarray` of any shape, normally `(H, W)`. `error_magnitude` is a numeric `float` controlling Gaussian phase-noise scale.
- **Returns:** complex `numpy.ndarray`, same shape as `original_key`.
- **Meaning:** Multiplies the key by a random unit-magnitude phase-noise mask. `0.0` leaves it unchanged up to floating-point arithmetic.

### `core.drpe.encrypt`

```python
encrypt(image, key1, key2)
```

- **Directory:** `core/`
- **File:** `drpe.py`
- **Inputs:** `image` is a numeric `numpy.ndarray`, shape `(H, W)`, normally real and normalized to `[0, 1]`. `key1` and `key2` are complex arrays, each shape `(H, W)`.
- **Returns:** complex `numpy.ndarray`, dtype `complex128`, shape `(H, W)`.
- **Algorithm:** Elementwise multiply by `key1`, apply `np.fft.fft2`, multiply by `key2`, then apply `np.fft.ifft2`.
- **Important:** Store the raw complex result. Do not replace it with `abs(cipher)`.

### `core.drpe.decrypt`

```python
decrypt(cipher, key1, key2)
```

- **Directory:** `core/`
- **File:** `drpe.py`
- **Inputs:** `cipher`, `key1`, and `key2` are complex `numpy.ndarray` objects of shape `(H, W)`.
- **Returns:** real `numpy.ndarray`, normally dtype `float64`, shape `(H, W)`.
- **Frontend use:** Clip to `[0, 1]` before display: `np.clip(recovered, 0, 1)`.
- **Round trip:** `decrypt(encrypt(image, key1, key2), key1, key2)` recovers `image` within floating-point tolerance.

## 5. RGB Image Functions

### `core.rgb_dpre.generate_color_keys`

```python
generate_color_keys(shape, shared=False, seed=None)
```

- **Directory:** `core/`
- **File:** `rgb_dpre.py`
- **Inputs:** `shape` is `(H, W)` only, not `(H, W, 3)`. `shared` is a `bool`. `seed` is optional; with a seed, keys are reproducible.
- **Returns:** `list` of length `3`. Each element is `(key1, key2)`, with both complex arrays shaped `(H, W)`.
- **Behavior:** `shared=True` creates one pair referenced by all channels. `shared=False` creates independent pairs for red, green, and blue.

### `core.rgb_dpre.encrypt_color`

```python
encrypt_color(image_rgb, keys)
```

- **Directory:** `core/`
- **File:** `rgb_dpre.py`
- **Inputs:** `image_rgb` is a real `numpy.ndarray`, shape `(H, W, 3)`, RGB order, values in `[0, 1]`. `keys` is a list of exactly three `(key1, key2)` pairs, with each key shape `(H, W)`.
- **Returns:** complex `numpy.ndarray`, dtype `complex128`, shape `(H, W, 3)`.
- **Errors:** Raises `AssertionError` unless the image has three channels and the key list has length three.

### `core.rgb_dpre.decrypt_color`

```python
decrypt_color(cipher_rgb, keys)
```

- **Directory:** `core/`
- **File:** `rgb_dpre.py`
- **Inputs:** `cipher_rgb` is complex, shape `(H, W, 3)`. `keys` is a list of exactly three `(key1, key2)` pairs, each key shape `(H, W)`.
- **Returns:** real `numpy.ndarray`, dtype `float64`, shape `(H, W, 3)`. Clip to `[0, 1]` before display.
- **Errors:** Raises `AssertionError` unless the ciphertext has three channels and the key list has length three.

## 6. Audio DRPE Functions

### `core.audio_drpe.generate_audio_phase_mask`

```python
generate_audio_phase_mask(length, seed=None)
```

- **Directory:** `core/`
- **File:** `audio_drpe.py`
- **Inputs:** positive `int` `length`, normally `N`, and optional NumPy-compatible `seed`.
- **Returns:** complex `numpy.ndarray`, dtype `complex128`, shape `(length,)`, approximately unit magnitude.

### `core.audio_drpe.generate_audio_keys`

```python
generate_audio_keys(signal_length, pin=None)
```

- **Directory:** `core/`
- **File:** `audio_drpe.py`
- **Inputs:** positive `int` `signal_length`, equal to `N`; optional numeric `pin` convertible to `int`.
- **Returns:** `(key1, key2)`, two complex `numpy.ndarray` objects, each shape `(N,)`.
- **Behavior:** `pin=None` creates random keys. A PIN uses deterministic seeds `pin` and `pin + 1`.

### `core.audio_drpe.perturb_audio_key`

```python
perturb_audio_key(original_key, error_magnitude)
```

- **Directory:** `core/`
- **File:** `audio_drpe.py`
- **Inputs:** complex `original_key`, normally shape `(N,)`; numeric `error_magnitude` controlling Gaussian phase-noise scale.
- **Returns:** complex `numpy.ndarray`, same shape as `original_key`.

### `core.audio_drpe.encrypt_audio`

```python
encrypt_audio(audio_signal, pin=None)
```

- **Directory:** `core/`
- **File:** `audio_drpe.py`
- **Inputs:** real `numpy.ndarray` `audio_signal`, shape `(N,)`, expected normalized range `[-1, 1]`; optional numeric PIN.
- **Returns:** `(ciphertext, key1, key2)`, three complex `numpy.ndarray` objects, each shape `(N,)`.
- **Important:** The ciphertext alone is insufficient for decryption. Save both keys too.

### `core.audio_drpe.decrypt_audio`

```python
decrypt_audio(ciphertext, k1, k2)
```

- **Directory:** `core/`
- **File:** `audio_drpe.py`
- **Inputs:** complex `numpy.ndarray` objects `ciphertext`, `k1`, and `k2`, all shape `(N,)`.
- **Returns:** real `numpy.ndarray`, normally `float64`, shape `(N,)`, clipped to `[-1, 1]`.
- **Frontend use:** Convert to WAV bytes with `wav_bytes_from_float_audio` and the original sample rate.

## 7. Audio I/O Functions

### `core.audio_utils.normalize_audio`

```python
normalize_audio(signal)
```

- **Directory:** `core/`
- **File:** `audio_utils.py`
- **Inputs:** numeric `numpy.ndarray`, usually shape `(N,)`; convert stereo to mono before calling.
- **Returns:** `numpy.ndarray`, same shape, scaled by maximum absolute amplitude into `[-1, 1]`.
- **Special case:** An all-zero signal is returned unchanged, so its dtype may remain integer.

### `core.audio_utils.load_and_normalize_audio`

```python
load_and_normalize_audio(file_path_or_buffer, max_duration_sec=None)
```

- **Directory:** `core/`
- **File:** `audio_utils.py`
- **Inputs:** `file_path_or_buffer` is a path or file-like object accepted by `scipy.io.wavfile.read`; use `io.BytesIO` for a Streamlit upload. `max_duration_sec` is an optional numeric duration.
- **Returns:** `(sample_rate, signal)`, where `sample_rate` is an `int` scalar and `signal` is a mono array shaped `(N,)`, normalized to approximately `[-1, 1]`.
- **Behavior:** Stereo data is averaged across axis `1`; optional cropping keeps at most `int(sample_rate * max_duration_sec)` samples.

### `core.audio_utils.float_audio_to_int16`

```python
float_audio_to_int16(audio_float)
```

- **Directory:** `core/`
- **File:** `audio_utils.py`
- **Inputs:** numeric array, normally shape `(N,)`, expected range `[-1, 1]`.
- **Returns:** `numpy.ndarray`, dtype `int16`, same shape, clipped and scaled by `32767`.

### `core.audio_utils.wav_bytes_from_float_audio`

```python
wav_bytes_from_float_audio(audio_float, sample_rate)
```

- **Directory:** `core/`
- **File:** `audio_utils.py`
- **Inputs:** normalized numeric `audio_float`, normally shape `(N,)`; integer `sample_rate` in Hz.
- **Returns:** Python `bytes` containing a valid WAV payload with 16-bit PCM samples.
- **Frontend use:** Pass the bytes to `st.audio` and `st.download_button` with MIME type `audio/wav`.

## 8. Metrics and Experiment Functions

### `core.metrics.calculate_psnr`

```python
calculate_psnr(original, recovered)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** two broadcast-compatible numeric arrays, normally identical-shape image arrays in `[0, 1]`.
- **Returns:** Python `float` in dB. Returns positive infinity when MSE is zero.

### `core.metrics.calculate_audio_mse`

```python
calculate_audio_mse(original, recovered)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** two broadcast-compatible numeric audio arrays, normally shape `(N,)`.
- **Returns:** NumPy scalar float containing mean squared error.

### `core.metrics.calculate_audio_snr_db`

```python
calculate_audio_snr_db(original, recovered, eps=1e-12)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** two broadcast-compatible numeric arrays, normally `(N,)`, and optional numeric `eps`.
- **Returns:** Python `float` in dB, or positive infinity when noise power is at most `eps`.

### `core.metrics.calculate_audio_correlation`

```python
calculate_audio_correlation(original, recovered, eps=1e-12)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** two broadcast-compatible numeric audio arrays, normally `(N,)`, and optional numeric `eps`.
- **Returns:** Python `float` correlation coefficient. Returns `0.0` when either input has standard deviation at most `eps`.

### `core.metrics.run_sensitivity_batch`

```python
run_sensitivity_batch(orig_img, cipher, k1, k2, steps=50)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** normalized `orig_img`, complex `cipher`, and complex `k1`/`k2`, all shape `(H, W)`; positive integer `steps`.
- **Returns:** `(magnitudes, psnr_values)`, two sequences each shape `(steps,)`. Magnitudes span `0.0` through `0.5`; infinite PSNR is capped at `100` for graphing.
- **Behavior:** Perturbs only `k2` for each trial.

### `core.metrics.run_audio_sensitivity_batch`

```python
run_audio_sensitivity_batch(orig_audio, cipher, k1, k2, steps=50, max_sigma=0.5)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** compatible 1-D arrays `orig_audio`, `cipher`, `k1`, and `k2`, all shape `(N,)`; positive integer `steps`; numeric `max_sigma`.
- **Returns:** `(magnitudes, snr_values, mse_values, corr_values)`, four NumPy arrays each shape `(steps,)`.
- **Behavior:** Perturbs audio `k2` from `0.0` through `max_sigma`; infinite SNR is replaced with `120.0` for plotting.

### `core.metrics.add_gaussian_noise`

```python
add_gaussian_noise(cipher, sigma)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** complex ciphertext array of any shape and numeric `sigma`.
- **Returns:** complex `numpy.ndarray`, same shape, with independent real and imaginary Gaussian noise added.

### `core.metrics.quantize_complex`

```python
quantize_complex(cipher, levels=256)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** complex ciphertext array of any shape; positive integer-like `levels`.
- **Returns:** complex array, same shape, uniformly quantized using a step derived from maximum magnitude.
- **Special case:** Zero-magnitude input returns an unchanged copy.

### `core.metrics.jpeg_compress_complex`

```python
jpeg_compress_complex(cipher, quality=50)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** complex ciphertext, normally 2-D `(H, W)`; integer-like JPEG `quality`.
- **Returns:** complex array, normally `(H, W)`. Only magnitude is JPEG-compressed; original phase is restored.
- **Special case:** Constant-magnitude input returns an unchanged copy.
- **Constraint:** Intended for 2-D grayscale ciphertext. Handle RGB per channel if using it for color data.

### `core.metrics.run_robustness_batch`

```python
run_robustness_batch(orig_img, cipher, k1, k2, mode="noise", levels=None)
```

- **Directory:** `core/`
- **File:** `metrics.py`
- **Inputs:** normalized grayscale `orig_img`, complex grayscale `cipher`, and matching complex keys, all `(H, W)`; `mode` must be one of `"noise"`, `"jpeg"`, or `"quant"`; optional 1-D `levels` sequence.
- **Returns:** `(severity, psnr_values)`, NumPy arrays each shape `(number_of_levels,)`.
- **Default levels:** noise uses 20 values from `0.01` to `0.5`; JPEG uses `[10,20,30,40,50,60,70,80,90]`; quantization uses `[8,16,32,64,128,256,512,1024]`.
- **Errors:** Raises `ValueError("Unknown robustness mode")` for any other mode.

## 9. Image Utility Functions

### `core.utils.load_grayscale`

```python
load_grayscale(path, size=None)
```

- **Directory:** `core/`
- **File:** `utils.py`
- **Inputs:** `path` is a filesystem path accepted by OpenCV. Optional `size` is `(width, height)` for `cv2.resize`.
- **Returns:** `numpy.ndarray`, dtype `float64`, shape `(H, W)`, values in `[0, 1]`.
- **Errors:** Raises `FileNotFoundError` if OpenCV cannot read the path.

### `core.utils.to_uint8`

```python
to_uint8(img)
```

- **Directory:** `core/`
- **File:** `utils.py`
- **Inputs:** numeric image array of any shape, expected values in `[0, 1]`.
- **Returns:** `numpy.ndarray`, dtype `uint8`, same shape, clipped to `[0, 1]` and scaled to `[0, 255]`.
- **Frontend use:** Use immediately before `st.image` or image-file output, never before decryption.

### `core.utils.ciphertext_magnitude_for_display`

```python
ciphertext_magnitude_for_display(cipher)
```

- **Directory:** `core/`
- **File:** `utils.py`
- **Inputs:** complex ciphertext array of any shape.
- **Returns:** real NumPy array, same shape, normalized magnitude in `[0, 1]`.
- **Important:** Visualization only. It discards phase information and must never be passed to `decrypt` or `decrypt_color`.

### `core.utils.load_color`

```python
load_color(path, size=None)
```

- **Directory:** `core/`
- **File:** `utils.py`
- **Inputs:** filesystem `path`; optional `size` as `(width, height)` for OpenCV resizing.
- **Returns:** `numpy.ndarray`, dtype `float64`, shape `(H, W, 3)`, RGB order, values in `[0, 1]`.
- **Errors:** Raises `FileNotFoundError` if OpenCV cannot read the path.

### `core.utils.compute_target_size`

```python
compute_target_size(height, width, max_dim=768)
```

- **Directory:** `core/`
- **File:** `utils.py`
- **Inputs:** integer `height` and `width`; optional integer-like `max_dim`.
- **Returns:** tuple `(new_width, new_height)` of integers, in OpenCV resize order.
- **Behavior:** Preserves aspect ratio and does not upscale images whose longer side is already at most `max_dim`.
- **Frontend use:** `target_w, target_h = compute_target_size(*image.shape[:2])`, then `cv2.resize(image, (target_w, target_h))`.

## 10. Streamlit Workflow Recipes

### Grayscale encryption page

```python
uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])
file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
img_u8 = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
target_w, target_h = compute_target_size(*img_u8.shape)
img_u8 = cv2.resize(img_u8, (target_w, target_h))
image = img_u8.astype(np.float64) / 255.0

key1 = generate_random_phase_mask(image.shape, seed=pin)
key2 = generate_random_phase_mask(image.shape, seed=None if pin is None else pin + 1)
cipher = encrypt(image, key1, key2)
recovered = np.clip(decrypt(cipher, key1, key2), 0, 1)
```

Display with `to_uint8(image)`, `to_uint8(ciphertext_magnitude_for_display(cipher))`, and `to_uint8(recovered)`. Keep `image`, `cipher`, `key1`, and `key2` in `st.session_state` while the page is active.

### Grayscale encrypted payload

The current application writes a dictionary into a NumPy `.npy` file:

```python
payload = {"cipher": cipher, "orig_shape": original_shape}
buffer = io.BytesIO()
np.save(buffer, payload, allow_pickle=True)
```

Read it with:

```python
payload = np.load(uploaded_npy, allow_pickle=True).item()
cipher = payload["cipher"]
original_shape = payload["orig_shape"]
```

If the frontend must restore the original dimensions, resize the recovered normalized image to `(original_shape[1], original_shape[0])`, then clip and convert to `uint8`.

### RGB encryption page

1. Load an RGB array shaped `(H, W, 3)` with values `[0, 1]`.
2. Call `keys = generate_color_keys((H, W), shared=shared, seed=seed)`.
3. Call `cipher = encrypt_color(image_rgb, keys)`.
4. Display `to_uint8(ciphertext_magnitude_for_display(cipher))`.
5. Decrypt with `np.clip(decrypt_color(cipher, keys), 0, 1)`.
6. Compare with `calculate_psnr(original, recovered)` if desired.

### Audio encryption page

```python
audio_io = io.BytesIO(uploaded_audio.getvalue())
sample_rate, signal = load_and_normalize_audio(audio_io)
cipher, key1, key2 = encrypt_audio(signal, pin=pin)
```

Save the three arrays independently with `np.save` into separate buffers. Keep `sample_rate` alongside the files or request it during decryption; a ciphertext does not contain the sample rate.

### Audio decryption page

```python
cipher = np.load(cipher_file)
key1 = np.load(key1_file)
key2 = np.load(key2_file)
recovered = decrypt_audio(cipher, key1, key2)
wav_bytes = wav_bytes_from_float_audio(recovered, sample_rate)
st.audio(wav_bytes, format="audio/wav")
```

For PIN mode, regenerate keys with `generate_audio_keys(len(cipher), pin=pin)` instead of loading key files.

### Analysis page

For interactive key sensitivity, create a damaged key with `generate_perturbed_key` or `perturb_audio_key`, decrypt, clip the image/audio result, and calculate the matching metric. For a curve, call `run_sensitivity_batch` or `run_audio_sensitivity_batch` and plot each returned 1-D array against its magnitude array.

For image robustness, map user labels to `mode="noise"`, `mode="jpeg"`, or `mode="quant"`, call `run_robustness_batch`, and plot returned `severity` against `psnr_values`.

## 11. Frontend Validation Checklist

- Validate image dimensions and RGB channel count before encryption.
- Validate that every key shape equals the corresponding image or signal shape.
- Preserve complex ciphertext arrays; never serialize only magnitude or phase for the normal workflow.
- Clip recovered images to `[0, 1]` and audio to `[-1, 1]` before display/export.
- Keep the original audio sample rate for WAV playback and download.
- Treat PIN-generated keys as demo convenience, not secure key storage.
- Show infinity metrics separately because perfect round trips return `float("inf")`.
- Use `allow_pickle=True` only for the current dictionary-based image payload format, and validate uploaded payload contents before using them.

## 12. Dependencies

The backend imports:

- `numpy`
- `scipy` (`scipy.io.wavfile`)
- `Pillow` (`PIL.Image`)
- `opencv-python` (`cv2`)

The Streamlit frontend additionally uses `streamlit`. The exact installed versions are listed in `requirements.txt`.
