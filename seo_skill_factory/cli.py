from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .config import apply_overrides, load_config, load_dotenv_if_available
from .agent_team import build_agent_team
from .discovery import discover
from .gemini import analyze_videos
from .logging_utils import configure_logging
from .synthesis import synthesize


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an SEO AI Skill from YouTube videos.")
    parser.add_argument("--version", action="version", version=f"seo-skill-factory {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser("discover", help="Fetch, filter, score, and export YouTube videos.")
    add_common(discover_parser)
    discover_parser.add_argument("--channel-url", default="")
    discover_parser.add_argument("--channel-id", default="")
    discover_parser.add_argument("--playlist-url", default="")
    discover_parser.add_argument("--playlist-id", default="")
    discover_parser.add_argument("--author-name", default="")
    discover_parser.add_argument("--niche", default="")
    discover_parser.add_argument("--year-min", type=int)
    discover_parser.add_argument("--year-max", type=int)
    discover_parser.add_argument("--include-keywords", default="")
    discover_parser.add_argument("--exclude-keywords", default="")
    discover_parser.add_argument("--max-videos", type=int)
    discover_parser.add_argument("--max-fetch", type=int)
    discover_parser.add_argument("--min-duration-seconds", type=int)
    discover_parser.add_argument("--max-duration-seconds", type=int)
    discover_parser.add_argument("--require-captions", action=argparse.BooleanOptionalAction, default=None)
    discover_parser.add_argument("--output-language", default="")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze selected videos with Gemini video understanding.")
    add_common(analyze_parser)
    analyze_parser.add_argument("--input", required=True, help="Path to selected_videos.csv")
    analyze_parser.add_argument("--force", action="store_true", help="Re-analyze videos even if JSON exists.")
    analyze_parser.add_argument(
        "--source",
        choices=["video", "transcript"],
        default="video",
        help="Analyze the full video via Gemini video understanding, or its text transcript (far cheaper).",
    )
    analyze_parser.add_argument(
        "--transcript-languages",
        default="",
        help="Comma-separated preferred transcript languages, e.g. en,ru. Transcript source only.",
    )

    synthesize_parser = subparsers.add_parser("synthesize", help="Synthesize per-video JSON into skill documents.")
    add_common(synthesize_parser)
    synthesize_parser.add_argument("--input", required=True, help="Directory containing per-video JSON files.")

    agent_team_parser = subparsers.add_parser("agent-team", help="Generate a controlled SEO/GEO multi-agent skill pack.")
    add_common(agent_team_parser)
    agent_team_parser.add_argument("--source-spec", default="", help="Optional source engineering spec markdown path.")
    agent_team_parser.add_argument("--business-name", default="", help="Business or pilot case name.")
    agent_team_parser.add_argument("--domain", default="", help="Business domain for the pilot case.")
    agent_team_parser.add_argument("--case-context", default="", help="Short pilot context string.")
    agent_team_parser.add_argument("--languages", default="", help="Comma-separated prompt/market languages.")

    args = parser.parse_args()
    config_path = Path(args.config).expanduser()
    load_dotenv_if_available(config_path.parent)
    config = load_config(config_path)
    overrides = vars(args)
    config = apply_overrides(config, overrides)
    configure_logging(config.output_dir, verbose=args.verbose)

    if args.command == "discover":
        payload = discover(config)
        print(json.dumps(payload, indent=2))
        return

    if args.command == "analyze":
        written = analyze_videos(
            Path(args.input).expanduser(),
            config,
            force=args.force,
            source=args.source,
        )
        print(json.dumps({"json_files": [str(path) for path in written]}, indent=2))
        return

    if args.command == "synthesize":
        outputs = synthesize(Path(args.input).expanduser(), config)
        print(json.dumps({key: str(path) for key, path in outputs.items()}, indent=2))
        return

    if args.command == "agent-team":
        outputs = build_agent_team(config)
        print(json.dumps({key: str(path) for key, path in outputs.items()}, indent=2))
        return


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--output-dir", default="", help="Override output directory")
    parser.add_argument("--verbose", action="store_true")


if __name__ == "__main__":
    main()
