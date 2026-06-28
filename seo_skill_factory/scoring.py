from __future__ import annotations

import re
from datetime import datetime

from .models import VideoMetadata


AI_SEARCH_TERMS = [
    "ai search",
    "ai mode",
    "ai overviews",
    "geo",
    "generative engine optimization",
]

RELEVANCE_TERMS = [
    "relevance engineering",
    "query fan-out",
    "query fanout",
    "embeddings",
    "rag",
    "passage retrieval",
]

PRACTICAL_TERMS = [
    "case study",
    "audit",
    "roadmap",
    "measurement",
    "visibility",
    "citations",
]

TECHNICAL_TERMS = [
    "technical seo",
    "content engineering",
    "internal linking",
    "structured data",
]

FOUNDATIONAL_TERMS = [
    "foundational",
    "foundation",
    "fundamentals",
    "basics",
    "core concepts",
    "information retrieval",
    "crawling",
    "indexing",
    "ranking systems",
    "search architecture",
]

PROMOTIONAL_TERMS = [
    "register now",
    "sign up",
    "tickets",
    "limited offer",
    "coupon",
    "discount",
    "sponsored",
    "use code",
    "buy now",
    "product launch",
    "launch event",
]

EDUCATIONAL_TERMS = [
    "how to",
    "guide",
    "tutorial",
    "framework",
    "workflow",
    "case study",
    "audit",
    "analysis",
    "explained",
    "lesson",
    "strategy",
]


def score_video(video: VideoMetadata) -> VideoMetadata:
    text = _search_text(video)
    year = published_year(video.published_at)
    score = 0
    reasons: list[str] = []

    if year == 2026:
        score += 3
        reasons.append("+3 published in 2026")
    elif year == 2025:
        score += 2
        reasons.append("+2 published in 2025")

    if contains_any(text, AI_SEARCH_TERMS):
        score += 3
        reasons.append("+3 AI Search/GEO topic")

    if contains_any(text, RELEVANCE_TERMS):
        score += 3
        reasons.append("+3 relevance engineering/retrieval topic")

    if contains_any(text, PRACTICAL_TERMS):
        score += 2
        reasons.append("+2 practical case/audit/measurement topic")

    if contains_any(text, TECHNICAL_TERMS):
        score += 2
        reasons.append("+2 technical/content engineering topic")

    if is_promotional_only(text):
        score -= 3
        reasons.append("-3 likely promotional only")

    if year is not None and year < 2023 and not is_foundational(text):
        score -= 2
        reasons.append("-2 older than 2023 and not foundational")

    video.score = score
    video.score_reasons = reasons
    return video


def filter_videos(
    videos: list[VideoMetadata],
    *,
    year_min: int | None,
    year_max: int | None,
    include_keywords: list[str],
    exclude_keywords: list[str],
    min_duration_seconds: int,
    max_duration_seconds: int | None,
    require_captions: bool,
) -> list[VideoMetadata]:
    result: list[VideoMetadata] = []
    for video in videos:
        text = _search_text(video)
        year = published_year(video.published_at)
        if year_min is not None and year is not None and year < year_min:
            continue
        if year_max is not None and year is not None and year > year_max:
            continue
        if include_keywords and not contains_any(text, include_keywords):
            continue
        if exclude_keywords and contains_any(text, exclude_keywords):
            continue
        if video.duration_seconds < min_duration_seconds:
            continue
        if max_duration_seconds is not None and video.duration_seconds > max_duration_seconds:
            continue
        if require_captions and not video.caption_available:
            continue
        result.append(video)
    return result


def select_top_videos(videos: list[VideoMetadata], max_videos: int) -> list[VideoMetadata]:
    scored = [score_video(video) for video in videos]
    return sorted(scored, key=lambda item: (item.score, item.published_at, item.view_count or 0), reverse=True)[:max_videos]


def contains_any(text: str, terms: list[str]) -> bool:
    haystack = text.casefold()
    return any(_contains_phrase(haystack, term.casefold()) for term in terms)


def published_year(published_at: str) -> int | None:
    if not published_at:
        return None
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00")).year
    except ValueError:
        match = re.match(r"^(\d{4})", published_at)
        return int(match.group(1)) if match else None


def is_foundational(text: str) -> bool:
    return contains_any(text, FOUNDATIONAL_TERMS)


def is_promotional_only(text: str) -> bool:
    promotional = contains_any(text, PROMOTIONAL_TERMS)
    educational = contains_any(text, EDUCATIONAL_TERMS + AI_SEARCH_TERMS + RELEVANCE_TERMS + PRACTICAL_TERMS + TECHNICAL_TERMS)
    return promotional and not educational


def _search_text(video: VideoMetadata) -> str:
    return f"{video.title}\n{video.description}"


def _contains_phrase(text: str, phrase: str) -> bool:
    if phrase.isalnum():
        return re.search(rf"\b{re.escape(phrase)}\b", text) is not None
    return phrase in text

