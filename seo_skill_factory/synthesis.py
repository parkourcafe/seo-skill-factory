from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import AppConfig


STATUS_TAGS = ("[VERIFIED]", "[OPINION]", "[POSSIBLY_OUTDATED", "[INTERPRETED]")


def synthesize(input_dir: Path, config: AppConfig) -> dict[str, Path]:
    records = load_records(input_dir)
    if not records:
        raise RuntimeError(f"No per-video JSON files found in {input_dir}")

    output_dir = config.output_dir / "synthesis"
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "knowledge_map": output_dir / "knowledge_map.md",
        "principles": output_dir / "principles.md",
        "frameworks": output_dir / "frameworks.md",
        "checklists": output_dir / "checklists.md",
        "anti_patterns": output_dir / "anti_patterns.md",
        "evidence_table": output_dir / "evidence_table.md",
        "contradictions_and_evolution": output_dir / "contradictions_and_evolution.md",
        "skill": output_dir / config.synthesis.final_skill_filename,
    }

    outputs["knowledge_map"].write_text(build_knowledge_map(records, config), encoding="utf-8")
    outputs["principles"].write_text(build_principles(records, config), encoding="utf-8")
    outputs["frameworks"].write_text(build_frameworks(records, config), encoding="utf-8")
    outputs["checklists"].write_text(build_checklists(records, config), encoding="utf-8")
    outputs["anti_patterns"].write_text(build_anti_patterns(records, config), encoding="utf-8")
    outputs["evidence_table"].write_text(build_evidence_table(records, config), encoding="utf-8")
    outputs["contradictions_and_evolution"].write_text(build_evolution(records, config), encoding="utf-8")
    outputs["skill"].write_text(build_final_skill(records, config), encoding="utf-8")
    return outputs


def load_records(input_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(input_dir.glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return sorted(records, key=lambda item: item.get("published_at", ""))


def build_knowledge_map(records: list[dict[str, Any]], config: AppConfig) -> str:
    topics: dict[str, list[str]] = defaultdict(list)
    for record in records:
        for topic in list_items(record, "main_topics"):
            topics[topic].append(video_ref(record))
    lines = [f"# Knowledge Map: {config.project.author_name}", ""]
    for topic, videos in sorted(topics.items(), key=lambda item: item[0].casefold()):
        lines.append(f"## {topic}")
        for video in videos:
            lines.append(f"- {video}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_principles(records: list[dict[str, Any]], config: AppConfig) -> str:
    lines = [f"# Principles: {config.project.author_name}", ""]
    lines.extend(section("Principles", collect_tagged(records, "principles")))
    lines.extend(section("Rules And Heuristics", collect_tagged(records, "rules_and_heuristics")))
    return "\n".join(lines).strip() + "\n"


def build_frameworks(records: list[dict[str, Any]], config: AppConfig) -> str:
    lines = [f"# Frameworks: {config.project.author_name}", ""]
    lines.extend(section("Frameworks", collect_tagged(records, "frameworks")))
    lines.extend(section("Workflows", collect_tagged(records, "workflows")))
    return "\n".join(lines).strip() + "\n"


def build_checklists(records: list[dict[str, Any]], config: AppConfig) -> str:
    lines = [f"# Checklists: {config.project.author_name}", ""]
    lines.extend(section("Checklist Items", collect_tagged(records, "checklists")))
    return "\n".join(lines).strip() + "\n"


def build_anti_patterns(records: list[dict[str, Any]], config: AppConfig) -> str:
    lines = [f"# Anti-patterns: {config.project.author_name}", ""]
    lines.extend(section("Anti-patterns", collect_tagged(records, "anti_patterns")))
    lines.extend(section("Possibly Outdated Tactics", collect_tagged(records, "possible_outdated_tactics", default_tag="[POSSIBLY_OUTDATED + unknown year]")))
    return "\n".join(lines).strip() + "\n"


def build_evidence_table(records: list[dict[str, Any]], config: AppConfig) -> str:
    lines = [
        f"# Evidence Table: {config.project.author_name}",
        "",
        "| Video | Published | Evidence | Examples | Quotes Or Timestamps |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        evidence = "<br>".join(escape_table(item) for item in list_items(record, "evidence")) or "-"
        examples = "<br>".join(escape_table(item) for item in list_items(record, "examples")) or "-"
        quotes = "<br>".join(escape_table(item) for item in list_items(record, "quotes_or_timestamps")) or "-"
        lines.append(f"| {escape_table(video_ref(record))} | {record.get('published_at', '')[:10]} | {evidence} | {examples} | {quotes} |")
    return "\n".join(lines).strip() + "\n"


def build_evolution(records: list[dict[str, Any]], config: AppConfig) -> str:
    lines = [f"# Contradictions And Evolution: {config.project.author_name}", ""]
    lines.append("## Evolution Timeline")
    for record in records:
        items = list_items(record, "possible_outdated_tactics")
        if items:
            lines.append(f"### {record.get('published_at', '')[:10]} - {record.get('title', '')}")
            for item in items:
                lines.append(f"- {ensure_tag(item, '[POSSIBLY_OUTDATED + unknown year]')}")
            lines.append("")
    lines.append("## Contradiction Review Queue")
    lines.append("- [INTERPRETED] Review principles that conflict with possibly outdated tactics before applying them to current SERPs.")
    lines.append("- [INTERPRETED] Prefer items with [VERIFIED] evidence when older and newer videos disagree.")
    return "\n".join(lines).strip() + "\n"


def build_final_skill(records: list[dict[str, Any]], config: AppConfig) -> str:
    principles = collect_tagged(records, "principles") + collect_tagged(records, "rules_and_heuristics")
    frameworks = collect_tagged(records, "frameworks")
    workflows = collect_tagged(records, "workflows")
    checklists = collect_tagged(records, "checklists")
    anti_patterns = collect_tagged(records, "anti_patterns") + collect_tagged(
        records, "possible_outdated_tactics", default_tag="[POSSIBLY_OUTDATED + unknown year]"
    )
    evidence = collect_plain(records, "evidence")
    tools = collect_plain(records, "tools_mentioned")

    lines = [
        f"# {config.project.author_name} SEO AI Skill",
        "",
        "## Role",
        f"You are an SEO strategy assistant trained on {config.project.author_name}'s public video material for {config.project.niche}. Your job is to turn user goals into practical SEO workflows, especially for AI Search, relevance engineering, technical SEO, content engineering, and measurement.",
        "",
        "## Core Philosophy",
        "Treat SEO as an evidence-seeking engineering discipline. Prefer retrieval, relevance, information architecture, content quality, and measurable search visibility over generic traffic advice. Label certainty clearly when recommending tactics.",
        "",
        "## Operating Principles",
    ]
    lines.extend(bullets(unique(principles), fallback="- [INTERPRETED] Start with the user's search surface, evidence, constraints, and measurement plan before recommending tactics."))
    lines.extend([
        "",
        "## AI Search Workflow",
    ])
    lines.extend(bullets(select_matching(workflows + frameworks + principles, ["ai search", "ai overview", "geo", "generative", "citation", "visibility"]), fallback="- [INTERPRETED] Map target queries, identify answer surfaces, inspect cited sources, compare competitors, and build content that can be retrieved, trusted, and cited."))
    lines.extend([
        "",
        "## Relevance Engineering Workflow",
    ])
    lines.extend(bullets(select_matching(workflows + frameworks + principles, ["relevance", "query", "fan-out", "embedding", "rag", "retrieval", "passage"]), fallback="- [INTERPRETED] Expand seed queries into intent clusters, map passages to user needs, improve entity clarity, and test whether content answers each query variant."))
    lines.extend([
        "",
        "## Technical SEO Workflow",
    ])
    lines.extend(bullets(select_matching(workflows + frameworks + principles, ["technical", "crawl", "index", "structured data", "internal link", "schema"]), fallback="- [INTERPRETED] Audit crawlability, indexability, internal links, structured data, rendering, page templates, and technical blockers before scaling content."))
    lines.extend([
        "",
        "## Content Engineering Workflow",
    ])
    lines.extend(bullets(select_matching(workflows + frameworks + principles, ["content", "passage", "topic", "entity", "brief", "editorial"]), fallback="- [INTERPRETED] Engineer content from search intent, source evidence, entity coverage, passage-level usefulness, internal links, and update cadence."))
    lines.extend([
        "",
        "## Measurement Workflow",
    ])
    lines.extend(bullets(select_matching(workflows + frameworks + principles + evidence, ["measurement", "metric", "visibility", "citation", "result", "case", "audit"]), fallback="- [INTERPRETED] Define baseline visibility, target queries, AI citation presence, organic rankings, technical health, content coverage, and post-change evidence before judging impact."))
    lines.extend([
        "",
        "## Checklists",
    ])
    lines.extend(bullets(unique(checklists), fallback="- [INTERPRETED] For each recommendation, document objective, evidence, implementation steps, measurement, owner, and review date."))
    lines.extend([
        "",
        "## Anti-patterns",
    ])
    lines.extend(bullets(unique(anti_patterns), fallback="- [INTERPRETED] Do not present unverified tactics as facts; mark them as opinion or hypotheses and ask for data."))
    lines.extend([
        "",
        "## Tools Mentioned",
    ])
    lines.extend(bullets(unique(tools), fallback="- Use the user's available crawling, analytics, rank tracking, log, and content tools; avoid assuming a specific stack unless the user names it."))
    lines.extend([
        "",
        "## Response Format",
        "When answering SEO questions, use this structure unless the user asks for another format:",
        "1. Diagnosis: restate the search surface, constraints, and evidence available.",
        "2. Recommendation: give prioritized actions with status tags such as [VERIFIED], [OPINION], [POSSIBLY_OUTDATED + year], or [INTERPRETED].",
        "3. Workflow: provide concrete steps, owner assumptions, and required inputs.",
        "4. Measurement: define metrics, baseline, validation method, and expected observation window.",
        "5. Risks: call out outdated tactics, missing evidence, and dependencies.",
        "",
        "## Quality Control",
        "- Do not fabricate data, citations, or quotes.",
        "- Preserve uncertainty tags on rules and tactics.",
        "- Prefer [VERIFIED] tactics when the source includes case data, demos, metrics, or concrete examples.",
        "- Mark synthesized advice as [INTERPRETED].",
        "- Mark tool-specific or old-algorithm advice as [POSSIBLY_OUTDATED + year] until revalidated.",
        "- Ask for site type, target market, analytics access, technical stack, and target search surface when those details affect the recommendation.",
    ])
    return "\n".join(lines).strip() + "\n"


def list_items(record: dict[str, Any], field: str) -> list[str]:
    values = record.get(field) or []
    if not isinstance(values, list):
        values = [values]
    return [stringify(item) for item in values if stringify(item)]


def collect_tagged(records: list[dict[str, Any]], field: str, default_tag: str = "[INTERPRETED]") -> list[str]:
    return [ensure_tag(item, default_tag) for record in records for item in list_items(record, field)]


def collect_plain(records: list[dict[str, Any]], field: str) -> list[str]:
    return [item for record in records for item in list_items(record, field)]


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        preferred = value.get("text") or value.get("claim") or value.get("name") or value.get("item")
        if preferred:
            extras = [f"{key}: {val}" for key, val in value.items() if key not in {"text", "claim", "name", "item"} and val]
            return f"{preferred} ({'; '.join(extras)})" if extras else str(preferred)
        return "; ".join(f"{key}: {val}" for key, val in value.items() if val)
    return str(value).strip()


def ensure_tag(item: str, default_tag: str = "[INTERPRETED]") -> str:
    stripped = item.strip()
    if stripped.startswith(STATUS_TAGS):
        return stripped
    return f"{default_tag} {stripped}"


def section(title: str, items: list[str]) -> list[str]:
    lines = [f"## {title}"]
    if not items:
        lines.append("- [INTERPRETED] No source items extracted.")
    else:
        lines.extend(f"- {item}" for item in unique(items))
    lines.append("")
    return lines


def bullets(items: list[str], fallback: str) -> list[str]:
    if not items:
        return [fallback]
    return [f"- {item}" for item in unique(items)]


def unique(items: list[str], limit: int = 80) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def select_matching(items: list[str], terms: list[str], limit: int = 30) -> list[str]:
    matches = [item for item in unique(items) if any(term.casefold() in item.casefold() for term in terms)]
    return matches[:limit]


def video_ref(record: dict[str, Any]) -> str:
    title = record.get("title", "")
    url = record.get("url", "")
    return f"[{title}]({url})" if url else title


def escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()

