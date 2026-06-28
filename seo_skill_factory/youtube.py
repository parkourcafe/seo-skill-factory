from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urlparse

from .models import VideoMetadata
from .retry import retry


LOGGER = logging.getLogger(__name__)


class YouTubeClient:
    def __init__(self, api_key: str) -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError("google-api-python-client is required. Install dependencies with: pip install -r requirements.txt") from exc
        self.service = build("youtube", "v3", developerKey=api_key, cache_discovery=False)

    def fetch_videos(
        self,
        *,
        channel_id: str = "",
        channel_url: str = "",
        playlist_id: str = "",
        playlist_url: str = "",
        max_results: int = 200,
    ) -> list[VideoMetadata]:
        resolved_playlist_id = playlist_id or parse_playlist_id(playlist_url)
        if not resolved_playlist_id:
            resolved_channel_id = self.resolve_channel_id(channel_id=channel_id, channel_url=channel_url)
            resolved_playlist_id = self.uploads_playlist_id(resolved_channel_id)
            LOGGER.info("Resolved channel %s to uploads playlist %s", resolved_channel_id, resolved_playlist_id)

        video_ids = self.playlist_video_ids(resolved_playlist_id, max_results=max_results)
        LOGGER.info("Fetched %s video ids from playlist %s", len(video_ids), resolved_playlist_id)
        return self.video_details(video_ids)

    def resolve_channel_id(self, *, channel_id: str = "", channel_url: str = "") -> str:
        if channel_id:
            return channel_id
        parsed = parse_channel_url(channel_url)
        if parsed.channel_id:
            return parsed.channel_id
        if parsed.handle:
            response = self._execute(
                self.service.channels().list(part="id", forHandle=parsed.handle, maxResults=1)
            )
            items = response.get("items", [])
            if items:
                return items[0]["id"]
        if parsed.username:
            response = self._execute(
                self.service.channels().list(part="id", forUsername=parsed.username, maxResults=1)
            )
            items = response.get("items", [])
            if items:
                return items[0]["id"]
        if parsed.custom_name:
            response = self._execute(
                self.service.search().list(part="snippet", q=parsed.custom_name, type="channel", maxResults=1)
            )
            items = response.get("items", [])
            if items:
                return items[0]["snippet"]["channelId"]
        raise ValueError("Could not resolve channel id. Provide --channel-id or a /channel/UC... URL.")

    def uploads_playlist_id(self, channel_id: str) -> str:
        response = self._execute(
            self.service.channels().list(part="contentDetails", id=channel_id, maxResults=1)
        )
        items = response.get("items", [])
        if not items:
            raise ValueError(f"Channel not found: {channel_id}")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def playlist_video_ids(self, playlist_id: str, *, max_results: int) -> list[str]:
        video_ids: list[str] = []
        page_token: str | None = None
        while len(video_ids) < max_results:
            response = self._execute(
                self.service.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(video_ids)),
                    pageToken=page_token,
                )
            )
            for item in response.get("items", []):
                video_id = item.get("contentDetails", {}).get("videoId")
                if video_id:
                    video_ids.append(video_id)
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return video_ids

    def video_details(self, video_ids: list[str]) -> list[VideoMetadata]:
        videos: list[VideoMetadata] = []
        for chunk in _chunks(video_ids, 50):
            response = self._execute(
                self.service.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=",".join(chunk),
                    maxResults=len(chunk),
                )
            )
            for item in response.get("items", []):
                videos.append(video_from_resource(item))
        return videos

    @retry(attempts=4, initial_delay=1, backoff=2)
    def _execute(self, request):
        return request.execute()


class ParsedChannelUrl:
    def __init__(self, channel_id: str = "", handle: str = "", username: str = "", custom_name: str = "") -> None:
        self.channel_id = channel_id
        self.handle = handle
        self.username = username
        self.custom_name = custom_name


def parse_channel_url(channel_url: str) -> ParsedChannelUrl:
    if not channel_url:
        return ParsedChannelUrl()
    parsed = urlparse(channel_url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return ParsedChannelUrl()
    if parts[0] == "channel" and len(parts) > 1:
        return ParsedChannelUrl(channel_id=parts[1])
    if parts[0].startswith("@"):
        return ParsedChannelUrl(handle=parts[0][1:])
    if parts[0] == "user" and len(parts) > 1:
        return ParsedChannelUrl(username=parts[1])
    if parts[0] in {"c", "channelname"} and len(parts) > 1:
        return ParsedChannelUrl(custom_name=parts[1])
    return ParsedChannelUrl(custom_name=parts[-1])


def parse_playlist_id(playlist_url: str) -> str:
    if not playlist_url:
        return ""
    if re.match(r"^[A-Za-z0-9_-]{10,}$", playlist_url):
        return playlist_url
    query = parse_qs(urlparse(playlist_url).query)
    values = query.get("list", [])
    return values[0] if values else ""


def video_from_resource(item: dict) -> VideoMetadata:
    snippet = item.get("snippet", {})
    content = item.get("contentDetails", {})
    statistics = item.get("statistics", {})
    video_id = item["id"]
    view_count = statistics.get("viewCount")
    return VideoMetadata(
        video_id=video_id,
        title=snippet.get("title", ""),
        description=snippet.get("description", ""),
        published_at=snippet.get("publishedAt", ""),
        duration=content.get("duration", ""),
        duration_seconds=parse_iso8601_duration(content.get("duration", "")),
        url=f"https://www.youtube.com/watch?v={video_id}",
        caption_available=str(content.get("caption", "false")).lower() == "true",
        view_count=int(view_count) if view_count is not None else None,
    )


def parse_iso8601_duration(value: str) -> int:
    if not value:
        return 0
    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?",
        value,
    )
    if not match:
        return 0
    parts = {key: int(val) if val else 0 for key, val in match.groupdict().items()}
    return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def _chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]

