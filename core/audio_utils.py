import io
import numpy as np
from scipy.io import wavfile


def normalize_audio(signal: np.ndarray)->np.ndarray:
    """Normalize an audio signal to [-1, 1] while preserving zeros."""
    max_amp=np.max(np.abs(signal))
    if max_amp==0:
        return signal
    return signal/max_amp


def load_and_normalize_audio(file_path_or_buffer, max_duration_sec=None):
    """Load WAV audio, convert to mono, optionally crop duration, and normalize."""
    sample_rate, data = wavfile.read(file_path_or_buffer)

    if len(data.shape)>1:
        data = data.mean(axis=1)

    if max_duration_sec is not None:
        max_samples=int(sample_rate*max_duration_sec)
        if len(data)>max_samples:
            data= data[:max_samples]

    return sample_rate, normalize_audio(data)


def float_audio_to_int16(audio_float: np.ndarray) -> np.ndarray:
    """Convert float audio in [-1, 1] to 16-bit PCM."""
    clipped =np.clip(audio_float, -1.0, 1.0)
    return np.int16(clipped * 32767)


def wav_bytes_from_float_audio(audio_float: np.ndarray, sample_rate: int) -> bytes:
    """Build a WAV byte payload from normalized float audio."""
    pcm_audio = float_audio_to_int16(audio_float)
    buffer = io.BytesIO()
    wavfile.write(buffer, sample_rate, pcm_audio)
    return buffer.getvalue()
