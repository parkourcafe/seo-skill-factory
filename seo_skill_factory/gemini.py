from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from .config import AppConfig, get_required_api_key
from .io_utils import read_videos_csv, write_json
from .models import VideoMetadata
from .retry import retry


LOGGER = logging.getLogger(__name__)

ANALYSIS_FIELDS = [
    "video_id",
    "title",
    "published_at",
    "url",
    "main_topics",
    "principles",
    "rules_and_heuristics",
    "frameworks",
    "workflows",
    "checklists",
    "examples",
    "anti_patterns",
    "tools_mentioned",
    "evidence",
    "possible_outdated_tactics",
    "quotes_or_timestamps",
]


class GeminiVideoAnalyzer:
    def __init__(self, config: AppConfig) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai is required. Install dependencies with: pip install -r requirements.txt") from exc
        api_key = get_required_api_key(config.gemini.api_key_env)
        self.client = genai.Client(api_key=api_key)
        self.types = types
        self.config = config

    def analyze(self, video: VideoMetadata) -> dict[str, Any]:
        prompt = build_video_prompt(video, self.config)
        try:
            response = self._create_interaction(prompt, video.url)
            text = getattr(response, "output_text", "") or ""
        except AttributeError:
            part = self.types.Part(
                file_data=self.types.FileData(file_uri=video.url, mime_type="video/*")
            )
            response = self._generate_legacy([part, prompt])
            text = getattr(response, "text", "") or ""
        parsed = parse_json_response(text)
        return normalize_analysis(parsed, video)

    @retry(attempts=4, initial_delay=2, backoff=2)
    def _create_interaction(self, prompt: str, video_url: str):
        return self.client.interactions.create(
            model=self.config.gemini.model,
            input=[
                {"type": "text", "text": prompt},
                {"type": "video", "uri": video_url},
            ],
        )

    @retry(attempts=4, initial_delay=2, backoff=2)
    def _generate_legacy(self, contents: list[Any]):
        config = self.types.GenerateContentConfig(
            temperature=self.config.gemini.temperature,
            response_mime_type="application/json",
        )
        return self.client.models.generate_content(
            model=self.config.gemini.model,
            contents=contents,
            config=config,
        )


class GeminiTranscriptAnalyzer(GeminiVideoAnalyzer):
    """Cheaper analyzer: sends the video's text transcript instead of the video."""

    def analyze(self, video: VideoMetadata) -> dict[str, Any]:
        transcript = fetch_transcript(video.video_id, self.config.transcript.languages)
        prompt = build_video_prompt(video, self.config, transcript=transcript)
        response = self._generate_legacy([prompt])
        text = getattr(response, "text", "") or ""
        parsed = parse_json_response(text)
        return normalize_analysis(parsed, video)


def build_analyzer(config: AppConfig, source: str = "video") -> GeminiVideoAnalyzer:
    if source == "transcript":
        return GeminiTranscriptAnalyzer(config)
    if source == "video":
        return GeminiVideoAnalyzer(config)
    raise ValueError(f"Unknown analysis source: {source!r} (expected 'video' or 'transcript')")


def analyze_videos(
    input_csv: Path,
    config: AppConfig,
    *,
    force: bool = False,
    source: str = "video",
) -> list[Path]:
    videos = read_videos_csv(input_csv)
    output_dir = config.output_dir / "per_video_json"
    output_dir.mkdir(parents=True, exist_ok=True)
    analyzer = build_analyzer(config, source)
    written: list[Path] = []
    for index, video in enumerate(videos, 1):
        output_path = output_dir / f"{video.video_id}.json"
        if output_path.exists() and not force:
            LOGGER.info("Skipping %s because %s already exists", video.video_id, output_path)
            written.append(output_path)
            continue
        LOGGER.info("Analyzing %s/%s (%s): %s", index, len(videos), source, video.title)
        try:
            analysis = analyzer.analyze(video)
        except Exception as exc:  # noqa: BLE001 - one bad video must not abort the batch
            LOGGER.warning("Failed to analyze %s: %s", video.video_id, exc)
            continue
        write_json(output_path, analysis)
        written.append(output_path)
        time.sleep(config.gemini.sleep_between_requests_seconds)
    return written


def build_video_prompt(video: VideoMetadata, config: AppConfig, transcript: str | None = None) -> str:
    source_line = (
        "Analyze this YouTube video transcript as source material for an SEO AI Skill."
        if transcript
        else "Analyze this YouTube video as source material for an SEO AI Skill."
    )
    prompt = f"""
{source_line}

Author or channel context: {config.project.author_name}
Niche: {config.project.niche}
Output language: {config.project.output_language}

Return only valid JSON with this exact top-level shape:
{{
  "video_id": "{video.video_id}",
  "title": "{_json_safe(video.title)}",
  "published_at": "{video.published_at}",
  "url": "{video.url}",
  "main_topics": [],
  "principles": [],
  "rules_and_heuristics": [],
  "frameworks": [],
  "workflows": [],
  "checklists": [],
  "examples": [],
  "anti_patterns": [],
  "tools_mentioned": [],
  "evidence": [],
  "possible_outdated_tactics": [],
  "quotes_or_timestamps": []
}}

Extraction rules:
- Focus on SEO, AI Search, AI Overviews, GEO, relevance engineering, retrieval, content engineering, technical SEO, measurement, and workflows.
- Every rule, tactic, workflow step, checklist item, and anti-pattern must begin with one status tag:
  - [VERIFIED] if the author gives case/data/result/demo.
  - [OPINION] if it is a claim without proof.
  - [POSSIBLY_OUTDATED + year] if tied to old tools, SERP features, old algorithms, old screenshots, or dated tactical advice.
  - [INTERPRETED] if synthesized from several parts of the video rather than stated directly.
- Evidence items should mention what kind of support exists: case, metric, demo, screenshot, example, or timestamp.
- Preserve concrete numbers, tool names, examples, and timestamps when available.
- Do not invent timestamps or quotes. If uncertain, omit them.
- Keep each array item concise but useful for a downstream assistant instruction.
""".strip()
    if transcript:
        prompt += (
            "\n\nTranscript (each line is prefixed with a [m:ss] timestamp; "
            "use these for quotes_or_timestamps and cite them where relevant):\n"
            + transcript
        )
    return prompt


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise RuntimeError(
            "youtube-transcript-api is required for transcript mode. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from exc
    langs = list(languages) if languages else ["en"]
    segments = _fetch_transcript_segments(YouTubeTranscriptApi, video_id, langs)
    text = _format_transcript(segments)
    if not text:
        raise RuntimeError(f"No transcript text available for {video_id}")
    return text


def _fetch_transcript_segments(api_cls: Any, video_id: str, languages: list[str]) -> list[dict[str, Any]]:
    # youtube-transcript-api < 1.0 exposes a get_transcript classmethod that
    # returns a list of dicts; >= 1.0 uses an instance .fetch() returning a
    # FetchedTranscript. Support both so the pipeline is not pinned to one line.
    getter = getattr(api_cls, "get_transcript", None)
    if callable(getter):
        raw = getter(video_id, languages=languages)
    else:
        fetched = api_cls().fetch(video_id, languages=languages)
        to_raw = getattr(fetched, "to_raw_data", None)
        raw = to_raw() if callable(to_raw) else fetched
    segments: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            text = item.get("text", "")
            start = item.get("start", 0)
        else:
            text = getattr(item, "text", "")
            start = getattr(item, "start", 0)
        segments.append({"text": text, "start": start})
    return segments


def _format_transcript(segments: list[dict[str, Any]]) -> str:
    lines = []
    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        lines.append(f"[{_format_timestamp(segment.get('start', 0))}] {text}")
    return "\n".join(lines)


def _format_timestamp(seconds: Any) -> str:
    try:
        total = int(float(seconds or 0))
    except (TypeError, ValueError):
        total = 0
    minutes, secs = divmod(max(total, 0), 60)
    return f"{minutes}:{secs:02d}"


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def normalize_analysis(data: dict[str, Any], video: VideoMetadata) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for field in ANALYSIS_FIELDS:
        if field in {"video_id", "title", "published_at", "url"}:
            normalized[field] = str(data.get(field) or getattr(video, field))
        else:
            value = data.get(field, [])
            normalized[field] = value if isinstance(value, list) else [value]
    normalized["video_id"] = video.video_id
    normalized["title"] = video.title
    normalized["published_at"] = video.published_at
    normalized["url"] = video.url
    return normalized


def _json_safe(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
