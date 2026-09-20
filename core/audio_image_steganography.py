"""Hide complex audio ciphertext inside a lossless RGB PNG cover image."""

import struct
import zlib

import numpy as np


_MAGIC = b"ADRPEIMG"
_VERSION = 1
_HEADER_FORMAT = ">8sBBIII4dI"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)
_QUANTIZATION_MAX = 65535.0


def _validate_lsb_depth(lsb_depth):
    if not isinstance(lsb_depth, (int, np.integer)) or not 1 <= lsb_depth <= 2:
        raise ValueError("lsb_depth must be an integer from 1 to 2.")


def _quantize_component(values):
    values = np.asarray(values, dtype=np.float64)
    low = float(values.min())
    high = float(values.max())
    if high == low:
        return np.zeros(values.shape, dtype=np.uint16), low, high
    quantized = np.rint(
        (values - low) / (high - low) * _QUANTIZATION_MAX
    ).astype(np.uint16)
    return quantized, low, high


def _dequantize_component(values, low, high):
    if high == low:
        return np.full(values.shape, low, dtype=np.float64)
    return values.astype(np.float64) / _QUANTIZATION_MAX * (high - low) + low


def _payload_for_cipher(cipher, sample_rate, lsb_depth):
    cipher = np.asarray(cipher)
    if cipher.ndim != 1 or cipher.size == 0 or not np.iscomplexobj(cipher):
        raise ValueError("cipher must be a non-empty one-dimensional complex array.")
    if not isinstance(sample_rate, (int, np.integer)) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer.")

    real_q, real_low, real_high = _quantize_component(cipher.real)
    imag_q, imag_low, imag_high = _quantize_component(cipher.imag)
    body = real_q.astype(">u2").tobytes() + imag_q.astype(">u2").tobytes()
    header = struct.pack(
        _HEADER_FORMAT,
        _MAGIC,
        _VERSION,
        lsb_depth,
        int(sample_rate),
        int(cipher.size),
        len(body),
        real_low,
        real_high,
        imag_low,
        imag_high,
        zlib.crc32(body),
    )
    return header, body


def required_cover_pixels(cipher_length, lsb_depth=1):
    """Return the minimum RGB cover-pixel count for an audio cipher."""
    _validate_lsb_depth(lsb_depth)
    if not isinstance(cipher_length, (int, np.integer)) or cipher_length <= 0:
        raise ValueError("cipher_length must be a positive integer.")
    header_bits = _HEADER_SIZE * 8
    body_bits = cipher_length * 4 * 8
    embedded_slots = header_bits + int(np.ceil(body_bits / lsb_depth))
    return int(np.ceil(embedded_slots / 3))


def _bits_to_values(bits, depth):
    pad = (-len(bits)) % depth
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    groups = bits.reshape(-1, depth)
    weights = (1 << np.arange(depth - 1, -1, -1)).astype(np.uint8)
    return (groups * weights).sum(axis=1).astype(np.uint8)


def _values_to_bits(values, bit_count, depth):
    mask = np.uint8((1 << depth) - 1)
    values = values & mask
    weights = (1 << np.arange(depth - 1, -1, -1)).astype(np.uint8)
    bits = ((values[:, None] & weights[None, :]) > 0).astype(np.uint8)
    return bits.reshape(-1)[:bit_count]


def embed_audio_cipher_in_image(cipher, cover_rgb, sample_rate, lsb_depth=1):
    """Embed a 1D complex audio cipher into a uint8 RGB cover image."""
    _validate_lsb_depth(lsb_depth)
    cover_rgb = np.asarray(cover_rgb)
    if cover_rgb.dtype != np.uint8 or cover_rgb.ndim != 3 or cover_rgb.shape[2] != 3:
        raise ValueError("cover_rgb must be a uint8 RGB image with shape (H, W, 3).")

    header, body = _payload_for_cipher(cipher, sample_rate, lsb_depth)
    needed = required_cover_pixels(len(cipher), lsb_depth)
    available = cover_rgb.shape[0] * cover_rgb.shape[1]
    if available < needed:
        raise ValueError(
            f"Cover image is too small: {available:,} pixels available, "
            f"{needed:,} required at lsb_depth={lsb_depth}."
        )

    header_bits = np.unpackbits(np.frombuffer(header, dtype=np.uint8))
    body_bits = np.unpackbits(np.frombuffer(body, dtype=np.uint8))
    header_values = header_bits.astype(np.uint8)
    body_values = _bits_to_values(body_bits, lsb_depth)

    stego = cover_rgb.copy()
    flat = stego.reshape(-1)
    header_end = len(header_values)
    flat[:header_end] = (flat[:header_end] & np.uint8(0xFE)) | header_values
    body_start = header_end
    body_end = body_start + len(body_values)
    mask = np.uint8((1 << lsb_depth) - 1)
    flat[body_start:body_end] = (flat[body_start:body_end] & ~mask) | body_values
    return stego


def _read_header(flat):
    header_bits = _values_to_bits(flat[:_HEADER_SIZE * 8], _HEADER_SIZE * 8, 1)
    header = struct.unpack(
        _HEADER_FORMAT,
        np.packbits(header_bits).tobytes(),
    )
    magic, version, lsb_depth, sample_rate, cipher_length, body_length, real_low, real_high, imag_low, imag_high, checksum = header
    if magic != _MAGIC or version != _VERSION:
        raise ValueError("This image does not contain a supported audio cipher.")
    _validate_lsb_depth(lsb_depth)
    if sample_rate <= 0 or cipher_length <= 0 or body_length != cipher_length * 4:
        raise ValueError("The embedded audio cipher header is invalid.")
    return {
        "lsb_depth": lsb_depth,
        "sample_rate": sample_rate,
        "cipher_length": cipher_length,
        "body_length": body_length,
        "real_low": real_low,
        "real_high": real_high,
        "imag_low": imag_low,
        "imag_high": imag_high,
        "checksum": checksum,
    }


def extract_audio_cipher_from_image(stego_rgb):
    """Extract a complex audio cipher and sample rate from an RGB image."""
    stego_rgb = np.asarray(stego_rgb)
    if stego_rgb.dtype != np.uint8 or stego_rgb.ndim != 3 or stego_rgb.shape[2] != 3:
        raise ValueError("stego_rgb must be a uint8 RGB image with shape (H, W, 3).")

    flat = stego_rgb.reshape(-1)
    header = _read_header(flat)
    header_slots = _HEADER_SIZE * 8
    body_bits_count = header["body_length"] * 8
    body_slots = int(np.ceil(body_bits_count / header["lsb_depth"]))
    if flat.size < header_slots + body_slots:
        raise ValueError("The image is too small for its embedded audio cipher.")

    body_bits = _values_to_bits(
        flat[header_slots:header_slots + body_slots],
        body_bits_count,
        header["lsb_depth"],
    )
    body = np.packbits(body_bits).tobytes()
    if zlib.crc32(body) != header["checksum"]:
        raise ValueError("The embedded audio cipher failed its integrity check.")

    length = header["cipher_length"]
    real_q = np.frombuffer(body[:length * 2], dtype=">u2")
    imag_q = np.frombuffer(body[length * 2:], dtype=">u2")
    real = _dequantize_component(real_q, header["real_low"], header["real_high"])
    imag = _dequantize_component(imag_q, header["imag_low"], header["imag_high"])
    return real + 1j * imag, header["sample_rate"]