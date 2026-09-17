"""
Steganographic embedding of a DRPE ciphertext inside a cover image.

Two embedding strategies, auto-selected by embed_cipher_in_cover() based
on whether the cover has enough pixels to hold the ciphertext data using
only its least significant bits:

- LSB embedding (embed_cipher_lsb / extract_cipher_lsb):
    Used when the cover is large enough. Spreads the quantized ciphertext
    across the cover's least-significant bits at a chosen depth
    (1-2 bits/channel is visually imperceptible). The cover's native
    resolution and appearance are fully preserved.

- Stretch + channel-replace (embed_cipher_stretch / extract_cipher_stretch):
    Fallback for covers too small to hold the data via LSBs. The cover is
    stretched (aspect ratio NOT preserved) to exactly match the cipher's
    shape, then its Red and Green channels are entirely overwritten with
    the quantized real/imaginary parts of the cipher. The Blue channel is
    left untouched so the result still has some visual resemblance to the
    original cover, though R/G are no longer the cover's own data.

Both paths quantize the cipher's real and imaginary parts to 8 bits each
(~50 dB PSNR loss in practice -- visually indistinguishable from a
perfect reconstruction).
"""

import struct

import numpy as np

# Fixed header layout: H(uint32), W(uint32), lsb_depth(uint8),
# r_lo/r_hi/i_lo/i_hi (float32 each). Always embedded at 1 bit/channel
# regardless of the body's lsb_depth, so it can always be read back
# without any external information -- this is what makes the stego
# image fully self-contained.
_HEADER_FORMAT = ">IIBffff"
_HEADER_BYTES = struct.calcsize(_HEADER_FORMAT)
_HEADER_BITS = _HEADER_BYTES * 8


# ---------------------------------------------------------------------
# Quantization helpers (shared by both embedding strategies)
# ---------------------------------------------------------------------

def quantize_to_uint8(arr):
    """
    Linearly quantize a real-valued array to uint8 [0, 255].

    Returns (q, lo, hi) -- the quantized array and the original min/max,
    which are required to invert the quantization later.
    """
    lo = float(arr.min())
    hi = float(arr.max())
    if hi == lo:
        # constant array -- avoid divide by zero, everything quantizes to 0
        return np.zeros(arr.shape, dtype=np.uint8), lo, hi
    q = np.round((arr - lo) / (hi - lo) * 255).astype(np.uint8)
    return q, lo, hi


def dequantize_from_uint8(q, lo, hi):
    """Inverse of quantize_to_uint8()."""
    if hi == lo:
        return np.full(q.shape, lo, dtype=np.float64)
    return q.astype(np.float64) / 255.0 * (hi - lo) + lo


# ---------------------------------------------------------------------
# Capacity calculation
# ---------------------------------------------------------------------

def required_cover_pixels(cipher_shape, lsb_depth=1, channels=3, bits_per_part=8):
    """
    Minimum number of cover pixels needed to embed a cipher of the given
    shape via LSB embedding, at the given bit depth per channel.

    bits_per_part is fixed at 8 by both embed/extract functions below
    (quantize_to_uint8/dequantize_from_uint8 are 8-bit); the parameter
    is exposed here mainly so the capacity formula is self-documenting.
    """
    H, W = cipher_shape
    total_bits = H * W * bits_per_part * 2  # real + imaginary parts
    capacity_per_pixel = channels * lsb_depth
    return int(np.ceil(total_bits / capacity_per_pixel))


# ---------------------------------------------------------------------
# Strategy 1: LSB embedding (cover fully preserved)
# ---------------------------------------------------------------------

def embed_cipher_lsb(cipher, cover_rgb, lsb_depth=1):
    """
    Embed `cipher` into the least-significant bits of `cover_rgb`,
    without resizing the cover, PROVIDED it has enough pixels.

    cipher    : complex128 array, shape (H, W)
    cover_rgb : uint8 array, shape (H_c, W_c, 3), with
                H_c * W_c >= required_cover_pixels((H, W), lsb_depth)
    lsb_depth : bits per channel to use (1-2 recommended for stealth)

    Returns (stego_rgb, meta) where meta is a dict needed by
    extract_cipher_lsb() to reverse the process.
    """
    H, W = cipher.shape
    needed = required_cover_pixels((H, W), lsb_depth=lsb_depth)
    available = cover_rgb.shape[0] * cover_rgb.shape[1]
    if available < needed:
        raise ValueError(
            f"Cover too small for LSB embedding: has {available} pixels, "
            f"needs at least {needed} pixels at lsb_depth={lsb_depth}. "
            f"Use a larger cover, increase lsb_depth, or fall back to "
            f"embed_cipher_stretch()."
        )

    real_q, r_lo, r_hi = quantize_to_uint8(cipher.real)
    imag_q, i_lo, i_hi = quantize_to_uint8(cipher.imag)

    # Flatten both quantized planes into one bitstream: real bits first,
    # then imag bits. unpackbits gives MSB-first bits per byte.
    bits = np.concatenate([
        np.unpackbits(real_q.flatten()),
        np.unpackbits(imag_q.flatten()),
    ])
    total_bits = bits.size  # = H*W*16, needed exactly by extraction to trim padding

    # Pad to a multiple of lsb_depth so we can group bits evenly.
    pad = (-total_bits) % lsb_depth
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])

    n_slots = bits.size // lsb_depth
    bits_grouped = bits.reshape(n_slots, lsb_depth)
    weights = (1 << np.arange(lsb_depth - 1, -1, -1)).astype(np.uint8)
    values = (bits_grouped * weights).sum(axis=1).astype(np.uint8)

    stego = cover_rgb.copy()
    flat = stego.reshape(-1)  # view: channel-innermost raster order
    clear_mask = np.uint8((0xFF << lsb_depth) & 0xFF)
    flat[:n_slots] = (flat[:n_slots] & clear_mask) | values

    meta = {
        "method": "lsb",
        "cipher_shape": (H, W),
        "lsb_depth": lsb_depth,
        "total_bits": total_bits,
        "r_lo": r_lo, "r_hi": r_hi,
        "i_lo": i_lo, "i_hi": i_hi,
    }
    return stego, meta


def extract_cipher_lsb(stego_rgb, meta):
    """Inverse of embed_cipher_lsb()."""
    H, W = meta["cipher_shape"]
    lsb_depth = meta["lsb_depth"]
    total_bits = meta["total_bits"]

    pad = (-total_bits) % lsb_depth
    n_slots = (total_bits + pad) // lsb_depth

    flat = stego_rgb.reshape(-1)
    slot_mask = np.uint8((1 << lsb_depth) - 1)
    values = flat[:n_slots] & slot_mask

    weights = (1 << np.arange(lsb_depth - 1, -1, -1)).astype(np.uint8)
    bits_grouped = ((values[:, None] & weights[None, :]) > 0).astype(np.uint8)
    bits = bits_grouped.reshape(-1)[:total_bits]  # drop the padding bits

    half = H * W * 8
    real_bits = bits[:half]
    imag_bits = bits[half:]

    real_q = np.packbits(real_bits).reshape(H, W)
    imag_q = np.packbits(imag_bits).reshape(H, W)

    real = dequantize_from_uint8(real_q, meta["r_lo"], meta["r_hi"])
    imag = dequantize_from_uint8(imag_q, meta["i_lo"], meta["i_hi"])
    return real + 1j * imag


# ---------------------------------------------------------------------
# Strategy 1b: self-contained LSB embedding (no separate meta file)
# ---------------------------------------------------------------------
#
# Same LSB approach as embed_cipher_lsb/extract_cipher_lsb above, but
# writes a small self-describing header (shape, lsb_depth, quantization
# ranges) into the image itself, always at 1 bit/channel, before the
# ciphertext body. This means a single downloaded image is everything
# the extractor needs -- no meta.npy to keep track of separately.
#
# Prefer this over embed_cipher_lsb/extract_cipher_lsb for any UI where
# the user only wants to deal with one file.

def _bits_to_slots(flat, start_slot, bits, depth):
    n_slots = len(bits) // depth
    grouped = bits[:n_slots * depth].reshape(n_slots, depth)
    weights = (1 << np.arange(depth - 1, -1, -1)).astype(np.uint8)
    values = (grouped * weights).sum(axis=1).astype(np.uint8)
    mask = np.uint8((0xFF << depth) & 0xFF)
    flat[start_slot:start_slot + n_slots] = (flat[start_slot:start_slot + n_slots] & mask) | values
    return start_slot + n_slots


def _slots_to_bits(flat, start_slot, n_bits, depth):
    n_slots = int(np.ceil(n_bits / depth))
    slot_mask = np.uint8((1 << depth) - 1)
    values = flat[start_slot:start_slot + n_slots] & slot_mask
    weights = (1 << np.arange(depth - 1, -1, -1)).astype(np.uint8)
    grouped = ((values[:, None] & weights[None, :]) > 0).astype(np.uint8)
    bits = grouped.reshape(-1)[:n_bits]
    return bits, start_slot + n_slots


def required_cover_pixels_self_contained(cipher_shape, lsb_depth=1, channels=3):
    """Like required_cover_pixels(), but also accounts for the header's
    own storage cost (always 1 bit/channel, independent of lsb_depth)."""
    H, W = cipher_shape
    header_slots = _HEADER_BITS  # header is always depth=1
    body_bits = H * W * 8 * 2
    body_slots = int(np.ceil(body_bits / lsb_depth))
    return int(np.ceil((header_slots + body_slots) / channels))


def embed_cipher_self_contained(cipher, cover_rgb, lsb_depth=1):
    """
    Embed cipher into cover_rgb along with a small header describing how
    to read it back -- the returned image needs NO separate meta dict.

    Raises ValueError if cover_rgb doesn't have enough pixels; check
    required_cover_pixels_self_contained() first to give a friendly
    error message instead of catching this.
    """
    H, W = cipher.shape
    needed = required_cover_pixels_self_contained((H, W), lsb_depth=lsb_depth)
    available = cover_rgb.shape[0] * cover_rgb.shape[1]
    if available < needed:
        raise ValueError(
            f"Cover too small: has {available} pixels, needs at least "
            f"{needed} pixels at lsb_depth={lsb_depth} (including header overhead)."
        )

    real_q, r_lo, r_hi = quantize_to_uint8(cipher.real)
    imag_q, i_lo, i_hi = quantize_to_uint8(cipher.imag)

    header_bytes = struct.pack(_HEADER_FORMAT, H, W, lsb_depth, r_lo, r_hi, i_lo, i_hi)
    header_bits = np.unpackbits(np.frombuffer(header_bytes, dtype=np.uint8))
    body_bits = np.concatenate([
        np.unpackbits(real_q.flatten()),
        np.unpackbits(imag_q.flatten()),
    ])

    stego = cover_rgb.copy()
    flat = stego.reshape(-1)
    next_slot = _bits_to_slots(flat, 0, header_bits, depth=1)
    _bits_to_slots(flat, next_slot, body_bits, depth=lsb_depth)
    return stego


def extract_cipher_self_contained(stego_rgb):
    """
    Recover the cipher from an image produced by embed_cipher_self_contained().
    No metadata argument needed -- everything required is read from the
    image's own embedded header.
    """
    flat = stego_rgb.reshape(-1)
    header_bits, next_slot = _slots_to_bits(flat, 0, _HEADER_BITS, depth=1)
    H, W, lsb_depth, r_lo, r_hi, i_lo, i_hi = struct.unpack(
        _HEADER_FORMAT, np.packbits(header_bits).tobytes()
    )

    body_bits_needed = H * W * 8 * 2
    body_bits, _ = _slots_to_bits(flat, next_slot, body_bits_needed, depth=lsb_depth)

    half = H * W * 8
    real_q = np.packbits(body_bits[:half]).reshape(H, W)
    imag_q = np.packbits(body_bits[half:]).reshape(H, W)
    real = dequantize_from_uint8(real_q, r_lo, r_hi)
    imag = dequantize_from_uint8(imag_q, i_lo, i_hi)
    return real + 1j * imag


# ---------------------------------------------------------------------
# Strategy 2: stretch + channel replace (fallback for small covers)
# ---------------------------------------------------------------------

def embed_cipher_stretch(cipher, cover_rgb, resize_fn):
    """
    Fallback for covers too small for LSB embedding: stretch cover_rgb
    to exactly match cipher.shape (ignoring aspect ratio), then replace
    its Red channel with the quantized real part and Green channel with
    the quantized imaginary part. Blue is left as the (stretched) cover's
    own data.

    resize_fn : a function(img, (target_w, target_h)) -> resized img,
                e.g. a thin wrapper around cv2.resize. Passed in rather
                than imported directly, so this module has no hard
                dependency on OpenCV.
    """
    H, W = cipher.shape
    stretched = resize_fn(cover_rgb, (W, H))  # (width, height) order

    real_q, r_lo, r_hi = quantize_to_uint8(cipher.real)
    imag_q, i_lo, i_hi = quantize_to_uint8(cipher.imag)

    stego = stretched.copy()
    stego[:, :, 0] = real_q
    stego[:, :, 1] = imag_q
    # channel 2 (Blue) left untouched

    meta = {
        "method": "stretch",
        "cipher_shape": (H, W),
        "r_lo": r_lo, "r_hi": r_hi,
        "i_lo": i_lo, "i_hi": i_hi,
    }
    return stego, meta


def extract_cipher_stretch(stego_rgb, meta):
    """Inverse of embed_cipher_stretch()."""
    real_q = stego_rgb[:, :, 0]
    imag_q = stego_rgb[:, :, 1]
    real = dequantize_from_uint8(real_q, meta["r_lo"], meta["r_hi"])
    imag = dequantize_from_uint8(imag_q, meta["i_lo"], meta["i_hi"])
    return real + 1j * imag


# ---------------------------------------------------------------------
# Auto-dispatch wrapper
# ---------------------------------------------------------------------

def embed_cipher_in_cover(cipher, cover_rgb, resize_fn, lsb_depth=1):
    """
    Picks LSB embedding if the cover is large enough to fully preserve
    its appearance; otherwise falls back to the stretch+replace method.
    """
    H, W = cipher.shape
    needed = required_cover_pixels((H, W), lsb_depth=lsb_depth)
    available = cover_rgb.shape[0] * cover_rgb.shape[1]

    if available >= needed:
        return embed_cipher_lsb(cipher, cover_rgb, lsb_depth=lsb_depth)
    return embed_cipher_stretch(cipher, cover_rgb, resize_fn)


def extract_cipher_from_stego(stego_rgb, meta):
    """Dispatches to the correct extraction function based on meta['method']."""
    if meta["method"] == "lsb":
        return extract_cipher_lsb(stego_rgb, meta)
    elif meta["method"] == "stretch":
        return extract_cipher_stretch(stego_rgb, meta)
    raise ValueError(f"Unknown embedding method in meta: {meta.get('method')}")