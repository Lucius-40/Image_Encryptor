"""Lossless PCM-WAV steganography for complex audio ciphertexts."""

import struct
import zlib

import numpy as np


_MAGIC = b"ADRPESTG"
_VERSION = 1
_HEADER_FORMAT = ">8sBBII4dII"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)
_QUANTIZATION_MAX = 65535.0


def _validate_lsb_depth(lsb_depth):
    if not isinstance(lsb_depth, (int, np.integer)) or not 1 <= lsb_depth <= 4:
        raise ValueError("lsb_depth must be an integer from 1 to 4.")


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
    checksum = zlib.crc32(body)
    header = struct.pack(
        _HEADER_FORMAT,
        _MAGIC,
        _VERSION,
        lsb_depth,
        int(cipher.size),
        int(sample_rate),
        real_low,
        real_high,
        imag_low,
        imag_high,
        len(body),
        checksum,
    )
    return header + body


def _bytes_to_bits(data):
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def _bits_to_bytes(bits):
    if len(bits) % 8:
        raise ValueError("Embedded payload is not byte-aligned.")
    return np.packbits(bits).tobytes()


def required_cover_samples(cipher_length, lsb_depth=1):
    """Return the minimum PCM sample count for a ciphertext payload."""
    _validate_lsb_depth(lsb_depth)
    if not isinstance(cipher_length, (int, np.integer)) or cipher_length <= 0:
        raise ValueError("cipher_length must be a positive integer.")
    header_bits = _HEADER_SIZE * 8
    body_bits = cipher_length * 4 * 8
    return header_bits + int(np.ceil(body_bits / lsb_depth))


def _as_pcm16(audio):
    audio = np.asarray(audio)
    if audio.ndim != 1:
        raise ValueError("Cover audio must be a mono one-dimensional array.")
    if np.issubdtype(audio.dtype, np.integer):
        return np.clip(audio, -32768, 32767).astype(np.int16)
    return np.rint(np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)


def embed_audio_cipher(cipher, cover_audio, sample_rate, lsb_depth=1):
    """Embed a complex cipher into mono PCM cover samples.

    Returns an int16 mono array. The returned audio must be written as a
    lossless PCM WAV file for extraction to work.
    """
    _validate_lsb_depth(lsb_depth)
    cover_pcm = _as_pcm16(cover_audio)
    payload = _payload_for_cipher(cipher, sample_rate, lsb_depth)
    needed = required_cover_samples(len(cipher), lsb_depth)
    if cover_pcm.size < needed:
        raise ValueError(
            f"Cover audio is too short: {cover_pcm.size:,} samples available, "
            f"{needed:,} required at lsb_depth={lsb_depth}."
        )

    header_bits = _bytes_to_bits(payload[:_HEADER_SIZE])
    body_bits = _bytes_to_bits(payload[_HEADER_SIZE:])
    bits = np.concatenate([header_bits, body_bits])
    body_offset = len(header_bits)
    pad = (-len(body_bits)) % lsb_depth
    if pad:
        body_bits = np.concatenate([body_bits, np.zeros(pad, dtype=np.uint8)])
    grouped_body = body_bits.reshape(-1, lsb_depth)
    weights = (1 << np.arange(lsb_depth - 1, -1, -1)).astype(np.uint16)
    body_values = (grouped_body * weights).sum(axis=1).astype(np.uint16)
    header_values = header_bits.astype(np.uint16)

    stego = cover_pcm.copy().view(np.uint16)
    stego[:len(header_values)] = (stego[:len(header_values)] & np.uint16(0xFFFE)) | header_values
    mask = np.uint16((1 << lsb_depth) - 1)
    start = body_offset
    stop = start + len(body_values)
    stego[start:stop] = (stego[start:stop] & ~mask) | body_values
    return stego.view(np.int16)


def _read_header(stego_pcm):
    header_bits_count = _HEADER_SIZE * 8
    header_slots = int(np.ceil(header_bits_count / 1))
    values = stego_pcm.view(np.uint16)[:header_slots] & 1
    header_bits = values.astype(np.uint8)
    header = _bits_to_bytes(header_bits)
    magic, version, lsb_depth, cipher_length, sample_rate, real_low, real_high, imag_low, imag_high, body_length, checksum = struct.unpack(
        _HEADER_FORMAT, header
    )
    if magic != _MAGIC or version != _VERSION:
        raise ValueError("This WAV does not contain a supported audio cipher.")
    _validate_lsb_depth(lsb_depth)
    if cipher_length <= 0 or body_length != cipher_length * 4:
        raise ValueError("The embedded audio cipher header is invalid.")
    if sample_rate <= 0:
        raise ValueError("The embedded sample rate is invalid.")
    return {
        "cipher_length": cipher_length,
        "lsb_depth": lsb_depth,
        "sample_rate": sample_rate,
        "real_low": real_low,
        "real_high": real_high,
        "imag_low": imag_low,
        "imag_high": imag_high,
        "body_length": body_length,
        "checksum": checksum,
    }


def extract_audio_cipher(stego_audio):
    """Extract a complex cipher and sample rate from PCM16 mono samples."""
    stego_pcm = _as_pcm16(stego_audio)
    header = _read_header(stego_pcm)
    header_slots = _HEADER_SIZE * 8
    body_bits_count = header["body_length"] * 8
    body_slots = int(np.ceil(body_bits_count / header["lsb_depth"]))
    if stego_pcm.size < header_slots + body_slots:
        raise ValueError("The WAV is too short for its embedded audio cipher.")

    values = (
        stego_pcm.view(np.uint16)[header_slots:header_slots + body_slots]
        & np.uint16((1 << header["lsb_depth"]) - 1)
    )
    weights = (1 << np.arange(header["lsb_depth"] - 1, -1, -1)).astype(np.uint16)
    body_bits = ((values[:, None] & weights[None, :]) > 0).astype(np.uint8)
    body = _bits_to_bytes(body_bits.reshape(-1)[:body_bits_count])
    if zlib.crc32(body) != header["checksum"]:
        raise ValueError("The embedded audio cipher failed its integrity check.")

    length = header["cipher_length"]
    real_q = np.frombuffer(body[:length * 2], dtype=">u2")
    imag_q = np.frombuffer(body[length * 2:], dtype=">u2")
    real = _dequantize_component(real_q, header["real_low"], header["real_high"])
    imag = _dequantize_component(imag_q, header["imag_low"], header["imag_high"])
    return real + 1j * imag, header["sample_rate"]