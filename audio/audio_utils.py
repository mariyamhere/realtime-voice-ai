from __future__ import annotations
import audioop
import math
import struct
from typing import Iterable

def pcm16_to_float32(pcm: bytes) -> list[float]:
    if len(pcm) % 2:
        raise ValueError("PCM16 byte buffer must contain an even number of bytes.")
    if not pcm:
        return []
    count = len(pcm) // 2
    values = struct.unpack(f"<{count}h", pcm)
    return [sample / 32768.0 for sample in values]

def float32_to_pcm16(samples: Iterable[float]) -> bytes:
    values = [
        int(max(-1.0, min(0.999969482421875, float(sample))) * 32768.0)
        for sample in samples
    ]
    return struct.pack("<" + "h" * len(values), *values)

def pcm16_rms(pcm: bytes) -> float:
    if not pcm:
        return 0.0
    if len(pcm) % 2:
        raise ValueError("PCM16 byte buffer must contain an even number of bytes.")
    values = struct.unpack(f"<{len(pcm)//2}h", pcm)
    return math.sqrt(sum(x * x for x in values) / len(values)) / 32768.0

def pcm16_to_mono(pcm: bytes, channels: int) -> bytes:
    if channels == 1:
        return pcm
    if channels < 1:
        raise ValueError("channels must be >= 1")
    return audioop.tomono(pcm, 2, 1.0 / channels, 1.0 / channels)

def validate_pcm16(pcm: bytes) -> None:
    if len(pcm) % 2:
        raise ValueError("Invalid PCM16 buffer length.")

def silence_pcm16(duration_ms: int, sample_rate: int = 16000) -> bytes:
    frames = int(sample_rate * duration_ms / 1000)
    return b"\x00\x00" * frames
