from __future__ import annotations

import logging

from .config import AppConfig, get_required_api_key
from .io_utils import write_json, write_notebooklm_sources, write_selected_markdown, write_videos_csv
from .scoring import filter_videos, select_top_videos
from .youtube import YouTubeClient


LOGGER = logging.getLogger(__name__)


def discover(config: AppConfig) -> dict[str, object]:
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = get_required_api_key(config.youtube.api_key_env)
    client = YouTubeClient(api_key)
    videos = client.fetch_videos(
        channel_id=config.youtube.channel_id,
        channel_url=config.youtube.channel_url,
        playlist_id=config.youtube.playlist_id,
        playlist_url=config.youtube.playlist_url,
        max_results=config.youtube.max_fetch,
    )
    LOGGER.info("Fetched %s videos", len(videos))
    write_json(output_dir / "raw_videos.json", [video.to_dict() for video in videos])
    write_videos_csv(output_dir / "raw_videos.csv", videos)

    filtered = filter_videos(
        videos,
        year_min=config.youtube.year_min,
        year_max=config.youtube.year_max,
        include_keywords=config.youtube.include_keywords,
        exclude_keywords=config.youtube.exclude_keywords,
        min_duration_seconds=config.youtube.min_duration_seconds,
        max_duration_seconds=config.youtube.max_duration_seconds,
        require_captions=config.youtube.require_captions,
    )
    LOGGER.info("Filtered to %s videos", len(filtered))
    write_json(output_dir / "filtered_videos.json", [video.to_dict() for video in filtered])
    write_videos_csv(output_dir / "filtered_videos.csv", filtered)

    selected = select_top_videos(filtered, config.selection.max_videos)
    LOGGER.info("Selected top %s videos", len(selected))
    write_videos_csv(output_dir / "selected_videos.csv", selected)
    write_selected_markdown(output_dir / "selected_videos.md", selected)
    write_notebooklm_sources(output_dir / "notebooklm_sources.txt", selected)
    return {
        "raw_count": len(videos),
        "filtered_count": len(filtered),
        "selected_count": len(selected),
        "selected_csv": str(output_dir / "selected_videos.csv"),
        "selected_md": str(output_dir / "selected_videos.md"),
        "notebooklm_sources": str(output_dir / "notebooklm_sources.txt"),
    }

