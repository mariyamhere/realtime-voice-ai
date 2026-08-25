from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable

import pyaudio

from app.audio.audio_utils import pcm16_to_mono
from app.config import settings


@dataclass(frozen=True)
class AudioChunk:
    data: bytes
    timestamp_ns: int


class MicrophoneCapture:
    def __init__(
        self,
        on_chunk: Callable[[AudioChunk], None],
        sample_rate: int = settings.sample_rate,
        channels: int = settings.channels,
        chunk_ms: int = settings.chunk_ms,
        device: str | None = settings.input_device,
    ) -> None:
        self.on_chunk = on_chunk
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_ms = chunk_ms
        self.frames_per_buffer = max(1, int(sample_rate * chunk_ms / 1000))
        self.device = self._resolve_device(device)
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._stopped = threading.Event()
        self._errors: queue.Queue[BaseException] = queue.Queue(maxsize=10)

    def _resolve_device(self, device: str | None):
        if device is None:
            return None
        if device.isdigit():
            return int(device)
        pa = pyaudio.PyAudio()
        try:
            for index in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(index)
                if device.lower() in info.get("name", "").lower():
                    return index
        finally:
            pa.terminate()
        raise ValueError(f"Input device not found: {device!r}")

    def _callback(self, in_data, frame_count, time_info, status_flags):
        if status_flags:
            # Non-fatal PortAudio status; the audio stream remains usable.
            pass
        if not self._stopped.is_set():
            try:
                if self.channels != 1:
                    in_data = pcm16_to_mono(in_data, self.channels)
                self.on_chunk(AudioChunk(data=in_data, timestamp_ns=__import__("time").monotonic_ns()))
            except BaseException as exc:
                try:
                    self._errors.put_nowait(exc)
                except queue.Full:
                    pass
        return (None, pyaudio.paContinue)

    def start(self) -> None:
        if self._stream is not None:
            return
        self._stopped.clear()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self._callback,
            start=False,
        )
        self._stream.start_stream()

    def stop(self) -> None:
        self._stopped.set()
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
            finally:
                self._stream.close()
                self._stream = None

    def check_errors(self) -> None:
        try:
            exc = self._errors.get_nowait()
        except queue.Empty:
            return
        raise RuntimeError("Microphone callback failed") from exc

    def close(self) -> None:
        self.stop()
        self._pa.terminate()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
