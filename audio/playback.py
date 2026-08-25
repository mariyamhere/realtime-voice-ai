from __future__ import annotations

import queue
import threading

import pyaudio

from app.config import settings


class AudioPlayer:
    def __init__(
        self,
        sample_rate: int = settings.tts_sample_rate,
        channels: int = settings.tts_channels,
        sample_width_bytes: int = settings.tts_sample_width_bytes,
        device: str | None = settings.output_device,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width_bytes = sample_width_bytes
        self.device = self._resolve_device(device)
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._queue: queue.Queue[bytes | None] = queue.Queue(maxsize=100)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

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
        raise ValueError(f"Output device not found: {device!r}")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._stream = self._pa.open(
            format=self._pa.get_format_from_width(self.sample_width_bytes),
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.device,
            frames_per_buffer=max(1, int(self.sample_rate * 0.02)),
        )
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                data = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if data is None:
                break
            try:
                self._stream.write(data, exception_on_underflow=False)
            except Exception:
                if not self._stop.is_set():
                    raise

    def play(self, data: bytes) -> None:
        if not data:
            return
        self._queue.put(data)

    def clear(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def stop(self) -> None:
        self._stop.set()
        self.clear()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        self._thread = None

    def close(self) -> None:
        self.stop()
        self._pa.terminate()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
