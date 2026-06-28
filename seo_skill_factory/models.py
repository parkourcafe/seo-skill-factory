from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    description: str
    published_at: str
    duration: str
    duration_seconds: int
    url: str
    caption_available: bool
    view_count: int | None = None
    score: int = 0
    score_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoMetadata":
        value = dict(data)
        value["caption_available"] = bool(value.get("caption_available", False))
        view_count = value.get("view_count")
        value["view_count"] = int(view_count) if view_count not in (None, "") else None
        value["duration_seconds"] = int(value.get("duration_seconds") or 0)
        value["score"] = int(value.get("score") or 0)
        reasons = value.get("score_reasons") or []
        if isinstance(reasons, str):
            reasons = [item.strip() for item in reasons.split(";") if item.strip()]
        value["score_reasons"] = reasons
        return cls(**value)


CSV_FIELDS = [
    "video_id",
    "title",
    "description",
    "published_at",
    "duration",
    "duration_seconds",
    "url",
    "caption_available",
    "view_count",
    "score",
    "score_reasons",
]

