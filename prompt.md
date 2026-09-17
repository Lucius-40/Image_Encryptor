# Task: Add Steganography Embed/Extract panels to the DRPE Streamlit app

## Context

This is a Streamlit app for Double Random Phase Encoding (DRPE) image
encryption. It already has tabs for Encrypt, Decrypt, Analysis, and Color
(RGB), each implemented as `render_*_tab()` functions in `view/*.py`,
wired together in `app.py` via `st.tabs(...)`.

A new backend module, `core/steganography.py`, has just been added. It
hides a DRPE ciphertext inside an RGB cover image so the encrypted data
doesn't visibly look like noise/ciphertext to a casual viewer. **This
module is complete and tested — do not modify or reimplement its logic.**
Your job is only the Streamlit UI on top of it.

## Backend functions available (import from `core.steganography`)

```python
required_cover_pixels(cipher_shape, lsb_depth=1, channels=3, bits_per_part=8) -> int
    # Minimum number of cover pixels needed. cipher_shape is (H, W).

embed_cipher_lsb(cipher, cover_rgb, lsb_depth=1) -> (stego_rgb, meta)
    # cover_rgb: uint8 array (H_c, W_c, 3). Raises ValueError if cover
    # is too small -- catch this and show a friendly message, don't let
    # it crash the app.

extract_cipher_lsb(stego_rgb, meta) -> cipher   # complex128 array

embed_cipher_stretch(cipher, cover_rgb, resize_fn) -> (stego_rgb, meta)
extract_cipher_stretch(stego_rgb, meta) -> cipher
    # Fallback path for undersized covers -- stretches the cover and
    # overwrites its R/G channels entirely. DO NOT use this
    # automatically as a silent fallback in this UI (see Requirements
    # below) -- it exists for a different use case. If a cover is too
    # small, the correct UX here is to tell the user and let them pick
    # a bigger one, not to silently degrade to this method.
```

Also available: `core.utils.resize_stretch_to_shape(img, target_shape)`,
`core.utils.ciphertext_magnitude_for_display(cipher)` (returns a
normalized real array from a complex array, for visualization only),
`core.utils.to_uint8(img)`.

`meta` is a small dict (`method`, `cipher_shape`, `lsb_depth`,
`total_bits`, and quantization ranges `r_lo/r_hi/i_lo/i_hi`). It MUST
travel with the stego image — extraction is impossible without it.

**Important constraint you must design around**: the stego image only
survives **lossless** formats. If it's saved/downloaded as JPEG, the
LSB data is destroyed silently (no error, just garbage on extraction).
Only ever offer/accept **PNG** for the stego image at every point in
this flow — encode the download button's `st.download_button(...,
mime="image/png")` accordingly, and validate uploaded files' extensions
before accepting them in the extractor panel.

## Panel 1: Embed

Add a new tab (or section) for embedding a cipher into a cover image.

**Cipher input.** The user will have already generated a cipher in the
existing Encrypt tab (stored in `st.session_state['enc_cipher']`, per
the existing pattern in `encrypt_view.py`). Support:
- Using the cipher already in `st.session_state` if present (preferred,
  zero extra steps for the user), AND
- An option to upload a `.npy` cipher file instead (same `.item()`
  load pattern already used in `decrypt_view.py` for uploaded `.npy`
  ciphers), for cases where the user isn't continuing directly from
  the Encrypt tab in the same session.

**Cover image input.** Two options, user's choice:
- Pick from a small set of preset images stored in
  `app_assets/covers/` (list the files in that folder and let the
  user pick one via `st.selectbox` or thumbnail gallery).
- Upload their own image via `st.file_uploader`.
Either way, convert/ensure the result is a 3-channel RGB uint8 array
before passing it to any embed function (handle grayscale or RGBA
inputs by converting appropriately).

**Capacity check (before embedding).** Call `required_cover_pixels()`
with the cipher's shape and compare against the cover's actual pixel
count (`height * width`). If the cover is too small:
- Do NOT attempt to embed.
- Show a clear message stating how many pixels are needed vs. how many
  the chosen cover has, and ask the user to pick a larger cover image
  or increase `lsb_depth` (expose `lsb_depth` as a small selectbox/
  slider, e.g. 1 or 2, defaulting to 1 — recompute the required-pixel
  number live as they change it, so they can see whether a smaller
  cover becomes viable at depth 2).

**On successful embed**, call `embed_cipher_lsb(cipher, cover_rgb,
lsb_depth=...)` directly (not the stretch fallback — see constraint
above) and display, side by side:
1. The cover image, as provided (before embedding).
2. A magnitude plot of the cipher via `ciphertext_magnitude_for_display()`
   + `to_uint8()` — this is the noise-like visualization already used
   elsewhere in the app (see `encrypt_view.py`/`decrypt_view.py` for
   the existing pattern) — labeled something like "Cipher (before
   hiding)".
3. The resulting stego image — labeled to make clear it visually looks
   like an ordinary photo despite containing the hidden cipher.

Provide a download button for the stego image as **PNG only**, and a
separate download button for the `meta` dict (bundle it as a `.npy`
file the same way keys/ciphers are already bundled elsewhere in this
app). Make it obvious in the UI copy that both files are needed
together to later extract the cipher.

## Panel 2: Extract

Add a second new tab (or section) for the reverse operation.

**Inputs:**
- An uploaded stego image (**PNG only** — reject or warn clearly on
  `.jpg`/`.jpeg` uploads, since JPEG will have already destroyed the
  hidden data before it even reaches this app).
- An uploaded `meta` `.npy` file (from Panel 1's download).

**On extraction**, call `extract_cipher_lsb(stego_rgb, meta)` and
display:
1. The uploaded stego image (as the user gave it — looks like an
   ordinary photo).
2. The extracted cipher's magnitude plot via
   `ciphertext_magnitude_for_display()` + `to_uint8()`, labeled
   something like "Extracted cipher (recovered from hidden data)" —
   this should visually look like noise again, confirming the
   ciphertext was pulled back out intact.

Also provide a download button for the extracted cipher as a `.npy`
file (same bundling convention as the existing Decrypt tab expects),
so the user can feed it straight into the existing Decrypt tab to
finish recovering the original image. Don't try to do decryption
inline in this panel — that's already handled by the Decrypt tab.

**Validation**: if `meta['cipher_shape']` and the uploaded stego
image's dimensions are inconsistent with what `extract_cipher_lsb`
expects (e.g., stego image too small for the stated `total_bits`),
catch the resulting error and show a clear message rather than letting
Streamlit display a raw traceback.

## Style/consistency notes

- Match the existing tab structure, `st.session_state` usage patterns,
  and visual layout conventions already used in `encrypt_view.py`,
  `decrypt_view.py`, and `analysis_view.py` (e.g. `st.columns`,
  `st.image(..., use_container_width=True)`, success/error message
  styling).
- Add the two new tabs to `app.py`'s `st.tabs(...)` call and imports,
  following the same pattern used when the Color (RGB) tab was added.
- Do not modify `core/steganography.py`, `core/drpe.py`, or
  `core/utils.py`'s existing functions — only add the new
  `resize_stretch_to_shape` usage if/where it's actually needed (it
  isn't needed for the LSB-only flow described above, only for the
  stretch fallback, which this UI intentionally does not auto-invoke).