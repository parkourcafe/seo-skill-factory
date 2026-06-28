from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import CSV_FIELDS, VideoMetadata


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_videos_csv(path: Path, videos: list[VideoMetadata]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for video in videos:
            row = video.to_dict()
            row["score_reasons"] = "; ".join(video.score_reasons)
            writer.writerow(row)


def read_videos_csv(path: Path) -> list[VideoMetadata]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [VideoMetadata.from_dict(row) for row in reader]


def write_selected_markdown(path: Path, videos: list[VideoMetadata]) -> None:
    lines = [
        "# Selected Videos",
        "",
        "| Rank | Score | Published | Title | URL | Reasons |",
        "| ---: | ---: | --- | --- | --- | --- |",
    ]
    for index, video in enumerate(videos, 1):
        title = _escape_table(video.title)
        reasons = _escape_table("; ".join(video.score_reasons))
        lines.append(f"| {index} | {video.score} | {video.published_at[:10]} | {title} | {video.url} | {reasons} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_notebooklm_sources(path: Path, videos: list[VideoMetadata]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(video.url for video in videos) + "\n", encoding="utf-8")


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()

