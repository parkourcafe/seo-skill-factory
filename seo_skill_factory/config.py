from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectConfig:
    output_dir: Path = Path("outputs")
    author_name: str = ""
    niche: str = ""
    output_language: str = "en"


@dataclass
class YouTubeConfig:
    api_key_env: str = "YOUTUBE_API_KEY"
    channel_url: str = ""
    channel_id: str = ""
    playlist_url: str = ""
    playlist_id: str = ""
    max_fetch: int = 200
    require_captions: bool = False
    min_duration_seconds: int = 0
    max_duration_seconds: int | None = None
    year_min: int | None = None
    year_max: int | None = None
    include_keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)


@dataclass
class SelectionConfig:
    max_videos: int = 20


@dataclass
class GeminiConfig:
    api_key_env: str = "GEMINI_API_KEY"
    model: str = "gemini-2.5-pro"
    temperature: float = 0
    request_timeout_seconds: int = 900
    sleep_between_requests_seconds: float = 2


@dataclass
class SynthesisConfig:
    final_skill_filename: str = "skill.md"


@dataclass
class AppConfig:
    project: ProjectConfig = field(default_factory=ProjectConfig)
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    synthesis: SynthesisConfig = field(default_factory=SynthesisConfig)

    @property
    def output_dir(self) -> Path:
        return self.project.output_dir


def load_dotenv_if_available(root: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(root / ".env")


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install dependencies with: pip install -r requirements.txt") from exc

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    root = config_path.parent
    project = _project_config(data.get("project", {}), root)
    return AppConfig(
        project=project,
        youtube=_youtube_config(data.get("youtube", {})),
        selection=_selection_config(data.get("selection", {})),
        gemini=_gemini_config(data.get("gemini", {})),
        synthesis=_synthesis_config(data.get("synthesis", {})),
    )


def apply_overrides(config: AppConfig, overrides: dict[str, Any]) -> AppConfig:
    for key, value in overrides.items():
        if value in (None, ""):
            continue
        if key in {"channel_url", "channel_id", "playlist_url", "playlist_id"}:
            setattr(config.youtube, key, str(value))
        elif key in {"year_min", "year_max", "max_fetch", "min_duration_seconds", "max_duration_seconds"}:
            setattr(config.youtube, key, int(value))
        elif key in {"include_keywords", "exclude_keywords"}:
            setattr(config.youtube, key, _list_value(value))
        elif key == "require_captions":
            config.youtube.require_captions = bool(value)
        elif key == "max_videos":
            config.selection.max_videos = int(value)
        elif key == "author_name":
            config.project.author_name = str(value)
        elif key == "niche":
            config.project.niche = str(value)
        elif key == "output_language":
            config.project.output_language = str(value)
        elif key == "output_dir":
            config.project.output_dir = Path(value).expanduser()
    return config


def get_required_api_key(env_name: str) -> str:
    api_key = os.environ.get(env_name, "").strip()
    if not api_key:
        raise RuntimeError(f"Missing API key. Set {env_name} in the environment or .env.")
    return api_key


def _project_config(data: dict[str, Any], root: Path) -> ProjectConfig:
    output_dir = Path(data.get("output_dir", "outputs")).expanduser()
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    return ProjectConfig(
        output_dir=output_dir,
        author_name=str(data.get("author_name", "")),
        niche=str(data.get("niche", "")),
        output_language=str(data.get("output_language", "en")),
    )


def _youtube_config(data: dict[str, Any]) -> YouTubeConfig:
    return YouTubeConfig(
        api_key_env=str(data.get("api_key_env", "YOUTUBE_API_KEY")),
        channel_url=str(data.get("channel_url", "")),
        channel_id=str(data.get("channel_id", "")),
        playlist_url=str(data.get("playlist_url", "")),
        playlist_id=str(data.get("playlist_id", "")),
        max_fetch=int(data.get("max_fetch", 200)),
        require_captions=bool(data.get("require_captions", False)),
        min_duration_seconds=int(data.get("min_duration_seconds", 0)),
        max_duration_seconds=_optional_int(data.get("max_duration_seconds")),
        year_min=_optional_int(data.get("year_min")),
        year_max=_optional_int(data.get("year_max")),
        include_keywords=_list_value(data.get("include_keywords", [])),
        exclude_keywords=_list_value(data.get("exclude_keywords", [])),
    )


def _selection_config(data: dict[str, Any]) -> SelectionConfig:
    return SelectionConfig(max_videos=int(data.get("max_videos", 20)))


def _gemini_config(data: dict[str, Any]) -> GeminiConfig:
    return GeminiConfig(
        api_key_env=str(data.get("api_key_env", "GEMINI_API_KEY")),
        model=str(data.get("model", "gemini-2.5-pro")),
        temperature=float(data.get("temperature", 0)),
        request_timeout_seconds=int(data.get("request_timeout_seconds", 900)),
        sleep_between_requests_seconds=float(data.get("sleep_between_requests_seconds", 2)),
    )


def _synthesis_config(data: dict[str, Any]) -> SynthesisConfig:
    return SynthesisConfig(final_skill_filename=str(data.get("final_skill_filename", "skill.md")))


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]

