---
name: deep-audience-analysis
description: >
  Run a deep, structured target-audience analysis for any niche or product.
  Use when the user wants to understand their customers — why people buy, why
  they don't, what content will land, or how to build an offer, funnel, or
  content plan. Interviews the user in three roles (marketer, sales/interviewer,
  and a stand-in for their audience), then produces an eight-block customer
  profile ending with scored "golden segments" and an optional shareable HTML
  one-pager. Triggers: "analyze my audience", "customer avatar", "target
  audience", "ЦА", "анализ целевой аудитории", "customer research", "who are my
  buyers", "why don't they buy".
---

# Deep Audience Analysis

A repeatable method for producing a deep, usable audience profile — the kind of
document that feeds an offer, a funnel, a content plan, and sales calls for
years. It is built to avoid the two failure modes of "AI audience research":
shallow generic output, and confident fabrication.

## Why this works (and its limits)

Large language models do not reason about your market; they predict plausible
text. So the quality of the profile is bounded by the quality of the context and
the instructions you give. Two consequences drive this whole method:

1. **Front-load context.** Everything meaningful comes from a good intake, not
   from asking "give me my audience's pains" cold.
2. **Treat output as hypotheses, not facts.** Model-generated audience insight
   correlates well with reality but is not a substitute for it. Every block is
   labeled `[HYPOTHESIS]` until the user, or real data (reviews, interviews,
   analytics), validates it. Never present invented specifics — names, numbers,
   quotes, statistics — as observed fact.

## Operating language

Conduct the intake and write the report in the **same language the user speaks
to you in**. Block 7 (Customer language) must preserve the audience's *actual*
words verbatim, in their language — do not translate or sanitize them.

## Workflow

Run these phases in order. Do not skip the intake.

### Phase 1 — Intake interview (three roles)

Before any analysis, interview the user. Act simultaneously as three people and
say so up front:

- a **marketer** who needs positioning-grade context,
- a **sales / customer-development interviewer** in the user's field,
- a **stand-in for the target audience** who reflects the customer's point of view.

Ask for the niche, the product, the price, the promised result, and who it is
for. When the user struggles to answer (experts often can't articulate their own
edge), *offer concrete options* they can accept, reject, or edit — don't leave
them staring at a blank question. Let them answer by voice/free text; they may
skip anything hard. Keep asking follow-ups until you have enough to profile the
buyer, then write a short "what I understood about the product and niche" recap
and confirm it before proceeding. Full protocol and question bank:
`references/intake.md`.

### Phase 2 — Eight-block analysis

Produce the profile block by block, in this order. Each block's required
contents and probing questions are in `references/blocks.md`:

1. **Identity, values & worldview** — who the core customer is, self-image,
   near-religious beliefs, relationship to money, the "deal with the world."
2. **Pains & fears** — concrete real-life situations, how the pain shows up
   emotionally and in the body (sensory detail is content fuel), what they dread.
3. **Barriers, myths & past experience** — what keeps them stuck, where they
   give up, what they've already tried and how it failed, what they refuse.
4. **Desired transformation** — the before → after state they are buying.
5. **Triggers & decision points** — the exact life events that flip a
   background problem into an active search; rational + emotional buy criteria.
6. **Hidden psychology / resistance** — what really blocks the purchase, and the
   secondary gains that make *not* solving the problem attractive.
7. **Customer language** — verbatim words, phrases, slang, filler; terms that
   build trust vs. terms that repel. Raw material for copy and content.
8. **Golden segments** — the segments that buy fastest and pay easiest, each
   with a positioning-ready description, closed by a scoring table (see below).

### Phase 3 — Golden-segment scoring

End block 8 with a comparison table scoring every segment on:

| Segment | Pain acuity (1-5) | Willingness/ability to pay (1-5) | Actively searching (1-5) | Priority score |

`Priority score` = the sum. Rank segments by it and name the top segment as the
primary positioning target. This table is the single most decision-useful output.

### Phase 4 — Validation & depth control

- **Validate.** Ask the user to flag anything that doesn't match reality. Drop
  what they reject; deepen what they confirm. This steers the model toward the
  real market and improves every later block.
- **Depth control.** The model economizes by default. When a block is thin, tell
  it: *"that was a 5/10 for depth — redo it at 9/10"* and it will expand with
  concrete situations, inner monologue, and specifics.

### Phase 5 — Deliverable

Deliver the profile as a long structured Markdown document. On request, also
produce a **self-contained, mobile-friendly HTML one-pager** the user can send
to a team, contractor, or client — copy the profile in full (do not summarize),
using the scaffold in `assets/report-template.html`.

## The prompt formula (how each block instruction is built)

Every strong instruction to the model — including the ones this skill issues —
follows: **Role** (who the model is, with specific skills) → **Context** (who the
user is, the audience, the goal) → **Goal** (the exact task and result) →
**Hints** (examples, guardrails, what to avoid) → **Format** (tone, structure,
output shape). Teach this to the user if they ask why the output is so much
deeper than a one-line prompt. Details: `references/prompt-formula.md`.

## Guardrails

- Label unvalidated claims `[HYPOTHESIS]`; separate facts, assumptions, and
  recommendations.
- Never fabricate reviews, quotes, statistics, names, or numbers.
- Recommend validating the profile against real reviews, customer-development
  interviews, and analytics before betting budget on it.
- Do not imitate any real person's identity or personal brand; this is a
  methodology, not an impersonation.
