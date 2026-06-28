# seo-skill-factory

Create an SEO AI Skill from a YouTube channel or playlist.

The pipeline:

1. Discovers videos with the YouTube Data API.
2. Filters and scores the videos for SEO, AI Search, GEO, relevance engineering, technical SEO, content engineering, and measurement topics.
3. Exports selected videos for review and NotebookLM.
4. Uses Gemini video understanding on YouTube URLs to produce one JSON analysis file per video.
5. Synthesizes the JSON files into working AI assistant instructions, including `skill.md`.

## Setup

```bash
cd /Users/msnigmatullaeva/Documents/australia/services/seo-skill-factory
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env`:

```text
YOUTUBE_API_KEY=...
GEMINI_API_KEY=...
```

Secrets are read from environment variables and are never hardcoded.

## Configure

Edit `config.yaml` for defaults:

- `project.author_name`
- `project.niche`
- `project.output_language`
- `youtube.channel_url` or `youtube.channel_id`
- `youtube.playlist_url` or `youtube.playlist_id`
- `youtube.year_min`, `youtube.year_max`
- `youtube.include_keywords`, `youtube.exclude_keywords`
- `selection.max_videos`
- `gemini.model` (change this if your Gemini account uses a different video-capable model)

CLI flags override the config file.

## CLI

Discover, filter, score, and select videos:

```bash
python main.py discover --channel-url "https://www.youtube.com/@iPullRank" --config config.yaml
```

Analyze selected videos with Gemini:

```bash
python main.py analyze --input outputs/selected_videos.csv --config config.yaml
```

Synthesize the final skill:

```bash
python main.py synthesize --input outputs/per_video_json --config config.yaml
```

You can also use a playlist:

```bash
python main.py discover --playlist-url "https://www.youtube.com/playlist?list=..." --config config.yaml
```

## Discovery Outputs

`discover` writes:

- `outputs/raw_videos.json`
- `outputs/raw_videos.csv`
- `outputs/filtered_videos.json`
- `outputs/filtered_videos.csv`
- `outputs/selected_videos.csv`
- `outputs/selected_videos.md`
- `outputs/notebooklm_sources.txt`

Metadata includes:

- `video_id`
- `title`
- `description`
- `published_at`
- `duration`
- `duration_seconds`
- `url`
- `caption_available`
- `view_count`
- `score`
- `score_reasons`

## Scoring

The default scoring implements these rules:

- `+3` if published in 2026
- `+2` if published in 2025
- `+3` for AI Search, AI Mode, AI Overviews, GEO, or Generative Engine Optimization
- `+3` for Relevance Engineering, query fan-out, embeddings, RAG, or passage retrieval
- `+2` for case study, audit, roadmap, measurement, visibility, or citations
- `+2` for Technical SEO, Content Engineering, Internal Linking, or structured data
- `-3` if likely promotional only
- `-2` if older than 2023 unless foundational

## Gemini Analysis

Gemini analysis sends public YouTube URLs as video inputs. Each selected video becomes `outputs/per_video_json/<video_id>.json` with this shape:

```json
{
  "video_id": "",
  "title": "",
  "published_at": "",
  "url": "",
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
}
```

Existing per-video JSON files are skipped by default, so failed runs can resume. Use `--force` to re-run Gemini analysis.

Every rule, tactic, workflow step, checklist item, and anti-pattern is prompted to carry one status tag:

- `[VERIFIED]`
- `[OPINION]`
- `[POSSIBLY_OUTDATED + year]`
- `[INTERPRETED]`

The synthesizer also adds `[INTERPRETED]` to untagged rules or tactics as a fallback.

## Synthesis Outputs

`synthesize` writes:

- `outputs/synthesis/knowledge_map.md`
- `outputs/synthesis/principles.md`
- `outputs/synthesis/frameworks.md`
- `outputs/synthesis/checklists.md`
- `outputs/synthesis/anti_patterns.md`
- `outputs/synthesis/evidence_table.md`
- `outputs/synthesis/contradictions_and_evolution.md`
- `outputs/synthesis/skill.md`

The final `skill.md` is written as an operating instruction for an AI assistant, not as a recap.

## Local Validation

```bash
python -m unittest discover -s tests
python -m compileall seo_skill_factory tests main.py
```
