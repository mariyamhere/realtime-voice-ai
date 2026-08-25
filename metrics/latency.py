from __future__ import annotations

import statistics
from dataclasses import dataclass, field


@dataclass
class TurnTimestamps:
    speech_start_ns: int | None = None
    speech_end_ns: int | None = None
    stt_first_partial_ns: int | None = None
    stt_final_ns: int | None = None
    llm_start_ns: int | None = None
    llm_first_token_ns: int | None = None
    tts_start_ns: int | None = None
    tts_first_audio_ns: int | None = None
    playback_start_ns: int | None = None
    playback_end_ns: int | None = None

    def duration_ms(self, start: int | None, end: int | None) -> float | None:
        if start is None or end is None:
            return None
        return (end - start) / 1_000_000

    def as_dict(self) -> dict:
        return {
            "speech_to_stt_final_ms": self.duration_ms(self.speech_start_ns, self.stt_final_ns),
            "speech_to_llm_first_token_ms": self.duration_ms(self.speech_start_ns, self.llm_first_token_ns),
            "speech_to_tts_first_audio_ms": self.duration_ms(self.speech_start_ns, self.tts_first_audio_ns),
            "speech_to_playback_ms": self.duration_ms(self.speech_start_ns, self.playback_start_ns),
            "stt_final_to_llm_first_token_ms": self.duration_ms(self.stt_final_ns, self.llm_first_token_ns),
            "llm_first_token_to_tts_audio_ms": self.duration_ms(self.llm_first_token_ns, self.tts_first_audio_ns),
        }


@dataclass
class LatencyRecorder:
    turns: list[TurnTimestamps] = field(default_factory=list)

    def new_turn(self) -> TurnTimestamps:
        turn = TurnTimestamps()
        self.turns.append(turn)
        return turn

    def summary(self) -> dict:
        values: dict[str, list[float]] = {}
        for turn in self.turns:
            for key, value in turn.as_dict().items():
                if value is not None:
                    values.setdefault(key, []).append(value)

        summary = {}
        for key, samples in values.items():
            samples.sort()
            summary[key] = {
                "count": len(samples),
                "p50_ms": _percentile(samples, 50),
                "p95_ms": _percentile(samples, 95),
                "p99_ms": _percentile(samples, 99),
                "mean_ms": statistics.fmean(samples),
            }
        return summary


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * percentile / 100
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    fraction = rank - lower
    return values[lower] + (values[upper] - values[lower]) * fraction
