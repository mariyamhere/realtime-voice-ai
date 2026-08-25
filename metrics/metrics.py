from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.metrics.latency import LatencyRecorder


@dataclass
class TurnMetric:
    turn_id: int
    user_text: str
    assistant_text: str
    interrupted: bool
    timestamps: dict


class MetricsStore:
    def __init__(self, output_dir: Path = settings.metrics_dir) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.latency = LatencyRecorder()
        self.turns: list[TurnMetric] = []

    def save(self, filename: str = "latest_metrics.json") -> Path:
        path = self.output_dir / filename
        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "turns": [asdict(turn) for turn in self.turns],
            "latency_summary": self.latency.summary(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
