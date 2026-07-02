from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AppConfig
from .io_utils import write_json


@dataclass(frozen=True)
class AgentRole:
    identifier: str
    title: str
    responsibilities: list[str]
    system_prompt: str
    output_format: list[str]


GLOBAL_RULES = [
    "Do not imitate any real living expert, private identity, distinctive voice, or personal brand.",
    "Use methodology-level inspiration only from public and properly licensed sources.",
    "Do not invent data; request missing inputs or mark the gap explicitly.",
    "Separate facts, assumptions, analysis, recommendations, and risks.",
    "Prefer first-party sources, official documentation, analytics exports, crawl data, log files, and reputable third-party sources.",
    "Never publish, deploy, modify CMS/DNS/server settings, or send outreach without explicit human approval.",
    "Never recommend fake reviews, fake mentions, doorway pages, scaled low-quality AI content, or paid link schemes.",
    "Every deliverable must include validation steps, owner, priority, expected impact, effort, and KPI.",
    "When using source material, summarize and cite instead of copying protected text.",
    "Optimize for business outcomes, not vanity SEO rituals.",
]

APPROVAL_GATES = [
    "Before publishing content.",
    "Before changing a production website.",
    "Before sending outreach from the brand.",
    "Before creating CMS drafts in early MVP phases.",
    "When QA marks an artifact as blocked.",
    "When agents disagree on a recommendation with material business or policy risk.",
]


def build_agent_team(config: AppConfig) -> dict[str, Path]:
    output_dir = config.output_dir / config.agent_team.output_dir_name
    agents_dir = output_dir / "agents"
    schemas_dir = output_dir / "json_contracts"
    output_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)

    roles = agent_roles()
    outputs: dict[str, Path] = {
        "team_skill": output_dir / "seo_agent_team_skill.md",
        "workflows": output_dir / "workflows.md",
        "knowledge_structure": output_dir / "knowledge_structure.md",
        "kpi_framework": output_dir / "kpi_framework.md",
        "pilot": output_dir / "pilot_task.md",
        "source_spec_digest": output_dir / "source_spec_digest.md",
        "manifest": output_dir / "agent_team_manifest.json",
    }

    outputs["team_skill"].write_text(build_team_skill(config, roles), encoding="utf-8")
    outputs["workflows"].write_text(build_workflows(config), encoding="utf-8")
    outputs["knowledge_structure"].write_text(build_knowledge_structure(), encoding="utf-8")
    outputs["kpi_framework"].write_text(build_kpi_framework(config), encoding="utf-8")
    outputs["pilot"].write_text(build_pilot_task(config), encoding="utf-8")
    outputs["source_spec_digest"].write_text(build_source_spec_digest(config), encoding="utf-8")

    for role in roles:
        path = agents_dir / f"{role.identifier}.md"
        path.write_text(build_agent_markdown(role), encoding="utf-8")
        outputs[f"agent_{role.identifier}"] = path

    for name, schema in json_contract_schemas().items():
        path = schemas_dir / f"{name}.schema.json"
        write_json(path, schema)
        outputs[f"schema_{name}"] = path

    manifest = build_manifest(config, roles, outputs)
    write_json(outputs["manifest"], manifest)
    return outputs


def agent_roles() -> list[AgentRole]:
    return [
        AgentRole(
            identifier="seo_chief_orchestrator",
            title="SEO Chief Orchestrator",
            responsibilities=[
                "Turn a business SEO/GEO request into scoped tasks.",
                "Assign tasks to specialist agents and manage dependencies.",
                "Maintain Kanban state, approval gates, conflict logs, and audit trail.",
                "Prevent production actions before human approval.",
            ],
            system_prompt=(
                "You are the SEO Chief Orchestrator. Build a controlled SEO and AI-search workflow. "
                "Break business goals into agent tasks, define inputs and outputs, enforce approval gates, "
                "resolve handoffs, and keep every recommendation tied to evidence, owner, priority, effort, KPI, and validation."
            ),
            output_format=[
                "Executive summary",
                "Task decomposition",
                "Agent assignments",
                "Dependencies and required inputs",
                "Approval gates",
                "Risks and conflict watchlist",
                "Next actions",
            ],
        ),
        AgentRole(
            identifier="audience_intelligence_agent",
            title="Target Audience Intelligence Agent",
            responsibilities=[
                "Define audience segments by outcomes, behavior, psychographics, and Jobs-To-Be-Done, not by demographics alone.",
                "Build evidence-based personas with goals, pains, gains, motivations, triggers, objections, and decision context.",
                "Map each segment to search intents, query fan-out, and answer-engine prompts for SEO and GEO.",
                "Prioritize first-party and zero-party data; mark every assumption and request missing inputs explicitly.",
                "For physical destinations, model real-world intent (visit, call, reservation, directions) plus local and seasonal context.",
                "Hand structured segments, intents, and prompts to intent mapping, content, and GEO agents.",
            ],
            system_prompt=(
                "You are the Target Audience Intelligence Agent. Turn business context, first-party data, and market signals "
                "into actionable audience segments, JTBD-based personas, and per-segment search intent for SEO and AI search. "
                "Segment by outcomes, motivations, context, and behavior, not demographic stereotypes. Tie every segment to "
                "observable evidence and to the queries and AI prompts that segment would actually use. Never invent survey data, "
                "traffic, personas, reviews, or numbers. Separate facts, assumptions, and recommendations, and request missing "
                "first-party data explicitly."
            ),
            output_format=[
                "Segment overview",
                "Persona profiles (identity, goals, JTBD, pains, gains, decision context)",
                "Triggers and decision points (what happens right before the purchase)",
                "Hidden psychology and secondary gains that block the purchase",
                "Customer language captured verbatim (words, phrases, trust vs. repel terms)",
                "Journey stage per segment",
                "Search intents and fan-out queries per segment",
                "AI answer-engine prompts per segment",
                "Preferred channels and content formats",
                "Messaging angles and required proof",
                "Golden-segment scoring table (pain acuity, ability to pay, active search, priority)",
                "Data sources, evidence, assumptions, and missing inputs",
                "Priority, expected impact, KPI, validation method",
                "Optional shareable HTML one-pager and handoff to intent mapping, content, or GEO agents",
            ],
        ),
        AgentRole(
            identifier="relevance_engineer",
            title="Relevance Engineering Agent",
            responsibilities=[
                "Audit crawlability, indexability, rendering, canonicals, internal links, schema, and logs.",
                "Simulate query fan-out, latent intents, entities, attributes, comparisons, and follow-up questions.",
                "Build brand entity graphs and structured data maps.",
                "Validate raw HTML versus rendered HTML for crawler-visible content, links, metadata, and schema.",
                "Evaluate extractable, source-worthy passages for search and AI retrieval.",
            ],
            system_prompt=(
                "You are the Relevance Engineering Agent. Improve discoverability, retrievability, and citability "
                "across Google Search, AI Overviews, AI Mode, Perplexity, ChatGPT-style search, Gemini, and other retrieval systems. "
                "Diagnose technical SEO and information retrieval blockers. Build entity maps, query fan-out maps, schema plans, "
                "and extractability recommendations. Never invent crawl, ranking, traffic, or rendering data."
            ),
            output_format=[
                "Findings",
                "Evidence",
                "Missing inputs",
                "Recommended actions",
                "Priority, effort, owner, expected impact, KPI",
                "Validation method",
            ],
        ),
        AgentRole(
            identifier="search_systems_operator",
            title="Search Systems Operator",
            responsibilities=[
                "Turn findings into a repeatable SEO operating system.",
                "Prioritize by business value, conversion intent, authority gap, effort, and risk.",
                "Build keyword, topic, entity, audience, and commercial-intent maps.",
                "Create execution roadmaps and SOPs for technical fixes, content, internal links, digital PR, and tracking.",
                "For physical destination brands, enforce local-first priority before informational blogging.",
            ],
            system_prompt=(
                "You are the Search Systems Operator. Convert SEO and AI-search findings into an execution system "
                "that can be repeated, measured, and improved. Connect every roadmap item to a business outcome. "
                "For restaurants, hotels, venues, spas, and other physical destinations, prioritize Google Business Profile, "
                "reviews, local pages, maps visibility, entity clarity, events, video assets, then blog content."
            ),
            output_format=[
                "Executive summary",
                "Prioritized roadmap",
                "Required inputs",
                "Task owner",
                "Estimated effort",
                "Expected business impact",
                "KPI",
                "Review cadence",
                "Risks",
            ],
        ),
        AgentRole(
            identifier="ai_visibility_geo_agent",
            title="AI Visibility / GEO Agent",
            responsibilities=[
                "Monitor brand mentions, citations, share of voice, prompt coverage, and entity associations in AI answer engines.",
                "Compare the brand with competitors and cited source ecosystems.",
                "Build multilingual prompt sets for AI visibility monitoring.",
                "Plan pages, PR assets, expert materials, and YouTube assets likely to be retrieved and cited.",
                "Keep answer-engine differences explicit instead of treating AI search as one surface.",
            ],
            system_prompt=(
                "You are the AI Visibility and GEO Agent. Improve how a brand is mentioned, cited, compared, and recommended "
                "in AI answer engines. Distinguish Google AI Overviews, Google AI Mode, Perplexity, ChatGPT Search, Gemini, "
                "Copilot, and other engines. Do not claim any tactic guarantees AI citations. Recommend measurable experiments "
                "using authoritative, crawlable, non-commodity, expert-led source assets."
            ),
            output_format=[
                "Prompt set",
                "Current visibility findings",
                "Competitor and source ecosystem notes",
                "Content, PR, and YouTube asset recommendations",
                "Experiment design",
                "Metrics and validation",
            ],
        ),
        AgentRole(
            identifier="content_architect",
            title="Content Architect",
            responsibilities=[
                "Turn SEO, entity, and AI-visibility research into publishable briefs and draft structures.",
                "Create landing page, comparison, FAQ, local page, press page, expert explainer, and video brief structures.",
                "Design extractable answer blocks, internal links, schema recommendations, and media requirements.",
                "Prevent generic filler, unsupported claims, and page proliferation for every fan-out variation.",
            ],
            system_prompt=(
                "You are the Content Architect. Create content briefs and draft structures that are useful to humans, crawlable, "
                "extractable, source-supported, commercially aligned, and non-commodity. Do not invent quotes, testimonials, "
                "statistics, reviews, awards, menu items, prices, or business claims."
            ),
            output_format=[
                "Page purpose",
                "Target audience",
                "Primary and secondary intents",
                "Entity coverage",
                "Required first-party and third-party evidence",
                "Suggested H1/H2 structure",
                "Extractable answer blocks",
                "Internal links",
                "Schema recommendations",
                "Media assets",
                "CTA",
                "QA checklist",
            ],
        ),
        AgentRole(
            identifier="digital_pr_authority_agent",
            title="Digital PR & Authority Agent",
            responsibilities=[
                "Identify legitimate external visibility opportunities.",
                "Run competitor link intersect and source ecosystem analysis.",
                "Find local directories, hospitality/travel/industry listings, partnerships, and expert commentary angles.",
                "Improve authority, referral traffic, and AI-source ecosystem coverage without manipulative tactics.",
            ],
            system_prompt=(
                "You are the Digital PR and Authority Agent. Identify legitimate external visibility opportunities that improve "
                "brand authority, referral traffic, and source ecosystem coverage. Do not recommend paid link schemes, fake reviews, "
                "synthetic mentions, or mass spam outreach."
            ),
            output_format=[
                "Opportunity",
                "Relevance",
                "Authority signal",
                "Difficulty",
                "Contact path",
                "Suggested pitch angle",
                "Risk",
                "Validation method",
            ],
        ),
        AgentRole(
            identifier="seo_qa_policy_agent",
            title="SEO QA & Policy Agent",
            responsibilities=[
                "Prevent inaccurate, thin, manipulative, legally risky, or strategically weak SEO work.",
                "Review facts, unsupported claims, hallucinated statistics, duplicate content, policy risk, and source quality.",
                "Validate technical readiness, schema recommendations, tracking plans, and human approval requirements.",
                "Record conflicts and produce pass, needs revision, or block decisions.",
            ],
            system_prompt=(
                "You are the SEO QA and Policy Agent. Review every artifact for factual accuracy, unsupported claims, source quality, "
                "search policy risk, user value, technical readiness, brand consistency, and human approval requirements. "
                "Block unverified superlatives, fabricated facts, fake reviews, spam tactics, or production actions without approval."
            ),
            output_format=[
                "Pass / Needs Revision / Block",
                "Critical issues",
                "Minor issues",
                "Missing evidence",
                "Policy risks",
                "Required fixes",
                "Final recommendation",
            ],
        ),
    ]


def build_team_skill(config: AppConfig, roles: list[AgentRole]) -> str:
    context = case_context(config)
    lines = [
        "# Controlled SEO/GEO Agent Team Skill",
        "",
        "## Role",
        "You are a controlled SEO and AI-search agent team. You coordinate specialist agents for technical relevance engineering, search operations, AI visibility/GEO, content architecture, digital PR, and QA.",
        "",
        "## Case Context",
        context,
        "",
        "## Global Rules",
    ]
    lines.extend(f"- {rule}" for rule in GLOBAL_RULES)
    lines.extend([
        "",
        "## Team Structure",
    ])
    for role in roles:
        lines.append(f"- `{role.identifier}`: {role.title}")
    lines.extend([
        "",
        "## Operating Protocol",
        "1. Intake the business goal, domain, market, audiences, constraints, and available data.",
        "2. Classify each output item as FACT, ASSUMPTION, RECOMMENDATION, or RISK.",
        "3. Assign specialist agents only when their work creates a measurable quality gain over one combined response.",
        "4. Require each specialist to return evidence, missing inputs, owner, priority, effort, expected impact, KPI, and validation method.",
        "5. Route artifacts through SEO QA before human approval.",
        "6. Stop before publication, production deployment, CMS draft creation, or outreach unless the human explicitly approves that action.",
        "",
        "## Approval Gates",
    ])
    lines.extend(f"- {gate}" for gate in APPROVAL_GATES)
    lines.extend([
        "",
        "## Conflict Protocol",
        "1. QA records the conflicting positions and their evidence.",
        "2. The orchestrator asks each agent for missing evidence and downside risk.",
        "3. Search Systems Operator compares business impact and implementation cost.",
        "4. Human Approver makes the final decision when risk, cost, or publishing consequences are material.",
        "5. The winning recommendation is the one with stronger data, lower risk, clearer KPI, and a testable validation method.",
        "",
        "## Response Format",
        "Use this format for team outputs:",
        "1. Facts",
        "2. Assumptions",
        "3. Analysis",
        "4. Recommendations",
        "5. Owners, priority, effort, impact, KPI",
        "6. Validation steps",
        "7. Risks and approval gates",
        "8. Next agent handoff or final human decision needed",
        "",
        "## Quality Control",
        "- Do not present absent analytics, crawl, ranking, AI-visibility, or conversion data as known.",
        "- Prefer official docs, first-party analytics, crawl exports, logs, GSC/GA4, and reputable third-party sources.",
        "- Treat NotebookLM and project workspaces as research memory, not production RAG infrastructure.",
        "- Keep development tools separate from SEO agents.",
        "- Do not create one thin page for every query fan-out variation.",
        "- Do not promise guaranteed AI citations.",
    ])
    return "\n".join(lines).strip() + "\n"


def build_agent_markdown(role: AgentRole) -> str:
    lines = [
        f"# {role.title}",
        "",
        f"Identifier: `{role.identifier}`",
        "",
        "## Responsibilities",
    ]
    lines.extend(f"- {item}" for item in role.responsibilities)
    lines.extend([
        "",
        "## System Prompt",
        role.system_prompt,
        "",
        "## Required Output Format",
    ])
    lines.extend(f"- {item}" for item in role.output_format)
    lines.extend([
        "",
        "## Non-negotiables",
    ])
    lines.extend(f"- {rule}" for rule in GLOBAL_RULES)
    return "\n".join(lines).strip() + "\n"


def build_workflows(config: AppConfig) -> str:
    return f"""# SEO/GEO Agent Team Workflows

## Workflow 0: Target Audience Intelligence
1. Intake business goal, offer, market, location, and any first-party data (GA4 audiences, GSC queries, CRM, reviews, reservations, booking notes). For a full guided intake and profile, run the `deep-audience-analysis` skill in `skills/deep-audience-analysis`.
2. `audience_intelligence_agent` drafts segments by Jobs-To-Be-Done, behavior, and psychographics, not demographics alone.
3. For each segment, build an evidence-based persona; capture triggers, hidden psychology, and verbatim customer language; map its search intents, fan-out queries, and AI answer-engine prompts.
4. Score segments (pain acuity, ability to pay, active search) into a golden-segment priority table, and name the primary focus segment.
5. Mark every assumption and list missing first-party inputs instead of inventing data.
6. Hand segments and intents to `search_systems_operator` (prioritization), `content_architect` (briefs), and `ai_visibility_geo_agent` (prompt sets).
7. `seo_qa_policy_agent` checks for fabricated personas, unsupported claims, and demographic stereotyping before use.

## Workflow 1: Weekly SEO Intelligence
1. Pull GSC data.
2. Pull GA4 landing page and conversion data.
3. Pull crawl, backlink, brand visibility, and log exports when available.
4. Normalize the data into a shared table or warehouse.
5. Send summary to `seo_chief_orchestrator`.
6. Create tasks for technical, content, GEO, PR, tracking, and QA work.
7. Notify the human owner.

## Workflow 2: AI Visibility Monitor
1. Generate multilingual prompt sets for {languages(config)}.
2. Query AI visibility tools, APIs, or reviewed exports.
3. Save mentions, citations, competitors, cited URLs, source domains, and own-domain citation rate.
4. Compare with previous runs.
5. Create recommendations for `ai_visibility_geo_agent`, `content_architect`, and `digital_pr_authority_agent`.
6. Require human review before publishing or outreach.

## Workflow 3: Content Production
1. Start from an approved content idea.
2. `content_architect` creates a brief.
3. `relevance_engineer` checks extractability, entity coverage, schema, internal links, and crawlability.
4. `search_systems_operator` confirms business priority and conversion path.
5. A human or approved writer creates the draft.
6. `seo_qa_policy_agent` reviews evidence, policy risk, thin content, and approval requirements.
7. Human approves publication or requests revision.

## Workflow 4: Technical SEO Fixes
1. Find a crawl, render, index, schema, internal-link, or log issue.
2. `relevance_engineer` diagnoses evidence and affected URLs.
3. `search_systems_operator` prioritizes by impact, effort, risk, and KPI.
4. Developer prepares the fix through normal engineering workflow.
5. `seo_qa_policy_agent` checks safety and validation steps.
6. Human approves.
7. Open PR, deploy, then validate with crawl, rendered HTML, logs, GSC, and analytics.

## Workflow 5: Conversion Tracking & Analytics Setup
1. For each approved page or feature, define conversion events.
2. Configure GA4 events and GTM triggers.
3. QA checks event firing, data accuracy, and PII leakage.
4. Human approves deployment.
5. Validate in GA4 DebugView and GTM Preview.
6. Add metrics to reporting dashboards.

## Standard Conversion Events
- `click_to_call`
- `click_to_whatsapp`
- `menu_click`
- `reservation_click`
- `directions_click`
- `event_interest`
- `spa_booking_click`
- `newsletter_signup`
- `investor_inquiry`
- `tenant_application`
- `video_engagement`
- `gbp_action`
"""


def build_knowledge_structure() -> str:
    return """# Knowledge, Grounding, And Memory Structure

```text
/knowledge
  /brand
    brand_positioning.md
    tone_of_voice.md
    products_services.md
    locations.md
    approved_claims.md
    entity_graph.json
    sub_brands/
  /audience
    segments/
    personas/
    jtbd_maps/
    search_intent_maps/
    first_party_data_exports/
    voice_of_customer/
  /seo
    technical_audits/
    keyword_research/
    gsc_exports/
    ga4_exports/
    crawl_exports/
    log_files/
    schema_map/
    rendered_html_snapshots/
  /ai_visibility
    prompt_sets/
    citation_reports/
    competitor_mentions/
    youtube_content_map/
  /content
    approved_briefs/
    published_pages/
    content_inventory.csv
    video_scripts/
  /sources
    public_methodology_notes/
    google_official_docs/
    platform_docs/
  /tracking
    ga4_event_definitions/
    gtm_container_exports/
    conversion_baselines/
    dashboard_configs/
  /decisions
    conflict_logs/
    approval_history/
    rollback_log/
```

## Research Memory
Use NotebookLM, ChatGPT Projects, Claude Projects, and working docs for human research and synthesis.

## Production Memory
Use a production RAG layer with vector database, versioning, logging, API access, and timestamped source records. Do not treat research workspaces as production infrastructure.
"""


def build_kpi_framework(config: AppConfig) -> str:
    return f"""# KPI Framework

## SEO KPI
- Indexed pages
- Crawl errors
- Pages with impressions
- Non-branded impressions
- Branded impressions
- CTR by page type
- Ranking distribution
- Internal link depth
- Core commercial pages with traffic

## AI Visibility KPI
- AI mentions
- AI citations
- Citation share versus competitors
- Prompt coverage
- Entity associations
- Cited source domains
- Own-domain citation rate
- Third-party citation rate

## Business KPI
- Leads or reservations relevant to {business_name(config)}
- Investor inquiries
- Tenant or partner applications
- Event inquiries
- Press mentions
- Google Business Profile actions after launch
- Newsletter growth
- Branded search growth
- AI referral traffic segment in GA4

## Agent System KPI
- QA pass rate
- Handoff quality
- Conflict rate
- Human override rate
- Time to recommendation
- False positive rate
"""


def build_pilot_task(config: AppConfig) -> str:
    name = business_name(config)
    domain = config.agent_team.domain or "example.com"
    return f"""# Pilot Task

## Goal
Analyze {name}'s readiness for Google Search, Google AI Overviews, AI Mode, Perplexity, ChatGPT Search, Gemini, and relevant local/travel discovery surfaces.

## Domain
{domain}

## Context
{config.agent_team.case_context or "Add business context, launch stage, target markets, and audiences."}

## Required Outputs
1. Target audience analysis: segments, JTBD personas, and per-segment search intent.
2. Technical SEO audit, including JS rendering validation.
3. Entity graph and local SEO audit.
4. Schema map for relevant page and business types.
5. AI visibility baseline.
6. Multilingual prompt set for monitoring.
7. YouTube AI visibility content map.
8. Content roadmap.
9. Digital PR and citation plan.
10. Conversion tracking plan.
11. 90-day implementation roadmap.

## Agent Assignment
- `audience_intelligence_agent`: audience segments, JTBD personas, per-segment search intents and AI prompts, first-party data gaps, real-world local intent.
- `relevance_engineer`: crawlability, indexability, sitemap, robots, schema, raw/rendered HTML, entity graph, schema map, extractable answer blocks.
- `search_systems_operator`: audience strategy, local-first prioritization, commercial page priorities, conversion event plan, 90-day roadmap.
- `ai_visibility_geo_agent`: prompt set, AI answer baseline, competitors, cited sources, YouTube visibility map.
- `content_architect`: priority briefs, video briefs, entity coverage, schema recommendations.
- `digital_pr_authority_agent`: directories, travel/hospitality/media opportunities, pitch angles.
- `seo_qa_policy_agent`: fact checking, unsupported-claim blocking, schema validation, tracking validation, approval gates.
"""


def build_source_spec_digest(config: AppConfig) -> str:
    source = config.agent_team.source_spec.strip()
    if not source:
        return "# Source Spec Digest\n\nNo source spec path was provided.\n"
    path = Path(source).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Source spec not found: {path}")
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    headings = [line.strip() for line in text.splitlines() if line.startswith("#")]
    lines = [
        "# Source Spec Digest",
        "",
        f"- Source path: `{path}`",
        f"- SHA256: `{digest}`",
        f"- Line count: {len(text.splitlines())}",
        "",
        "## Headings",
    ]
    lines.extend(f"- {heading}" for heading in headings[:120])
    return "\n".join(lines).strip() + "\n"


def build_manifest(config: AppConfig, roles: list[AgentRole], outputs: dict[str, Path]) -> dict[str, Any]:
    return {
        "name": "controlled-seo-geo-agent-team",
        "business_name": business_name(config),
        "domain": config.agent_team.domain,
        "languages": config.agent_team.languages,
        "roles": [role.identifier for role in roles],
        "approval_gates": APPROVAL_GATES,
        "outputs": {key: str(path) for key, path in outputs.items()},
    }


def json_contract_schemas() -> dict[str, dict[str, Any]]:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "technical_audit_output": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["project", "domain", "audit_date", "findings", "missing_inputs", "next_agent"],
            "properties": {
                "project": {"type": "string"},
                "domain": {"type": "string"},
                "audit_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "findings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["issue", "category", "evidence", "affected_urls", "severity", "business_impact", "recommended_fix", "validation_method"],
                        "properties": {
                            "issue": {"type": "string"},
                            "category": {"enum": ["crawlability", "indexability", "rendering", "js_rendering", "internal_links", "schema", "structured_data", "entity_graph", "content_accessibility", "performance", "duplication", "logs"]},
                            "evidence": string_array,
                            "affected_urls": string_array,
                            "severity": {"enum": ["critical", "high", "medium", "low"]},
                            "business_impact": {"type": "string"},
                            "recommended_fix": {"type": "string"},
                            "validation_method": {"type": "string"},
                        },
                    },
                },
                "missing_inputs": string_array,
                "next_agent": {"const": "search_systems_operator"},
            },
        },
        "audience_analysis_output": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["project", "business_context", "segments", "missing_inputs", "next_agent"],
            "properties": {
                "project": {"type": "string"},
                "business_context": {"type": "string"},
                "analysis_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["segment_name", "segment_basis", "jobs_to_be_done", "persona", "journey_stage", "search_intents", "evidence", "assumptions", "priority", "kpi", "validation_method"],
                        "properties": {
                            "segment_name": {"type": "string"},
                            "segment_basis": {"enum": ["jobs_to_be_done", "behavioral", "psychographic", "contextual", "demographic", "mixed"]},
                            "jobs_to_be_done": string_array,
                            "persona": {
                                "type": "object",
                                "required": ["label", "goals", "pains", "gains", "triggers", "objections", "decision_context"],
                                "properties": {
                                    "label": {"type": "string"},
                                    "goals": string_array,
                                    "pains": string_array,
                                    "gains": string_array,
                                    "triggers": string_array,
                                    "objections": string_array,
                                    "decision_context": {"type": "string"},
                                },
                            },
                            "journey_stage": {"enum": ["awareness", "consideration", "conversion", "retention", "advocacy"]},
                            "search_intents": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["query", "intent", "stage"],
                                    "properties": {
                                        "query": {"type": "string"},
                                        "intent": {"enum": ["informational", "commercial", "transactional", "local", "navigational"]},
                                        "stage": {"enum": ["awareness", "consideration", "conversion", "retention"]},
                                    },
                                },
                            },
                            "triggers": string_array,
                            "hidden_psychology": string_array,
                            "secondary_gains": string_array,
                            "customer_language": string_array,
                            "ai_prompts": string_array,
                            "channels": string_array,
                            "content_formats": string_array,
                            "messaging_angles": string_array,
                            "proof_needed": string_array,
                            "evidence": string_array,
                            "assumptions": string_array,
                            "golden_segment_score": {
                                "type": "object",
                                "required": ["pain_acuity", "ability_to_pay", "actively_searching", "priority_score"],
                                "properties": {
                                    "pain_acuity": {"type": "integer", "minimum": 1, "maximum": 5},
                                    "ability_to_pay": {"type": "integer", "minimum": 1, "maximum": 5},
                                    "actively_searching": {"type": "integer", "minimum": 1, "maximum": 5},
                                    "priority_score": {"type": "integer", "minimum": 3, "maximum": 15},
                                },
                            },
                            "priority": {"enum": ["high", "medium", "low"]},
                            "expected_impact": {"type": "string"},
                            "kpi": {"type": "string"},
                            "validation_method": {"type": "string"},
                        },
                    },
                },
                "missing_inputs": string_array,
                "next_agent": {"enum": ["search_systems_operator", "content_architect", "ai_visibility_geo_agent"]},
            },
        },
        "intent_map_output": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["seed_topic", "audiences", "primary_intents", "fan_out_queries", "entities", "content_gaps", "recommended_pages"],
            "properties": {
                "seed_topic": {"type": "string"},
                "audiences": string_array,
                "primary_intents": {"type": "array", "items": {"enum": ["informational", "commercial", "transactional", "local", "navigational"]}},
                "fan_out_queries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["query", "intent", "stage", "content_asset_needed", "priority"],
                        "properties": {
                            "query": {"type": "string"},
                            "intent": {"type": "string"},
                            "stage": {"enum": ["awareness", "consideration", "conversion", "retention"]},
                            "content_asset_needed": {"type": "string"},
                            "priority": {"enum": ["high", "medium", "low"]},
                        },
                    },
                },
                "entities": string_array,
                "content_gaps": string_array,
                "recommended_pages": string_array,
            },
        },
        "content_brief_output": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["page_type", "target_query_cluster", "audience", "business_goal", "h1", "sections", "internal_links", "schema", "cta", "qa_checklist"],
            "properties": {
                "page_type": {"enum": ["landing_page", "guide", "comparison", "faq", "local_page", "press_page", "video_script", "youtube_brief"]},
                "target_query_cluster": {"type": "string"},
                "audience": {"type": "string"},
                "business_goal": {"type": "string"},
                "h1": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["h2", "purpose", "required_evidence", "extractable_answer"],
                        "properties": {
                            "h2": {"type": "string"},
                            "purpose": {"type": "string"},
                            "required_evidence": string_array,
                            "extractable_answer": {"type": "string"},
                        },
                    },
                },
                "internal_links": string_array,
                "external_sources_needed": string_array,
                "schema": string_array,
                "media_assets": string_array,
                "video_assets": {
                    "type": "object",
                    "properties": {
                        "youtube_videos": string_array,
                        "each_video_requires": {"type": "string"},
                    },
                },
                "entity_graph_reference": string_array,
                "conversion_events": string_array,
                "cta": {"type": "string"},
                "qa_checklist": string_array,
            },
        },
        "qa_review_output": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["artifact_id", "artifact_type", "source_agent", "verdict", "critical_issues", "minor_issues", "missing_evidence", "policy_risks", "required_fixes", "recommendation"],
            "properties": {
                "artifact_id": {"type": "string"},
                "artifact_type": {"enum": ["audit", "intent_map", "brief", "draft", "pr_plan", "tracking_plan", "roadmap"]},
                "source_agent": {"type": "string"},
                "verdict": {"enum": ["pass", "needs_revision", "block"]},
                "critical_issues": string_array,
                "minor_issues": string_array,
                "missing_evidence": string_array,
                "policy_risks": string_array,
                "required_fixes": string_array,
                "recommendation": {"type": "string"},
            },
        },
        "conflict_report_output": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["conflict_id", "date", "agents_involved", "topic", "position_a", "position_b", "business_impact_comparison", "qa_assessment", "requires_human_decision"],
            "properties": {
                "conflict_id": {"type": "string"},
                "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "agents_involved": string_array,
                "topic": {"type": "string"},
                "position_a": position_schema(),
                "position_b": position_schema(),
                "business_impact_comparison": {"type": "string"},
                "qa_assessment": {"type": "string"},
                "requires_human_decision": {"type": "boolean"},
            },
        },
    }


def position_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["agent", "recommendation", "evidence", "category"],
        "properties": {
            "agent": {"type": "string"},
            "recommendation": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "category": {"enum": ["fact", "assumption", "recommendation", "risk"]},
        },
    }


def case_context(config: AppConfig) -> str:
    name = business_name(config)
    domain = config.agent_team.domain or "domain not provided"
    context = config.agent_team.case_context or "No specific pilot context provided."
    return f"Business: {name}. Domain: {domain}. Context: {context}"


def business_name(config: AppConfig) -> str:
    return config.agent_team.business_name or "the target brand"


def languages(config: AppConfig) -> str:
    return ", ".join(config.agent_team.languages) if config.agent_team.languages else "the configured target languages"

