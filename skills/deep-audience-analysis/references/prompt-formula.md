# The Prompt Formula

Why a one-line prompt ("give me my audience's pains") returns generic mush, and a
structured instruction returns something usable: the model matches your prompt
against its training and returns the most probable continuation. A thin prompt
has thin, average continuations. A precise, example-rich prompt lets it retrieve
the specific, valuable material.

Build every strong instruction — including the ones this skill issues internally
— in this order:

1. **Role.** Who the model should be, with *named skills*, not just a title.
   Not "act as a marketer" but "act as a marketer who can get inside a customer's
   values, beliefs, fears and pains, and put themselves in the buyer's place."

2. **Context (Information).** Everything around the task: who the user is, who the
   audience is, what they sell, why, and what the end result should serve. This
   is the single biggest lever. Reuse the intake here; store it in project/long-
   term memory so it doesn't have to be re-entered.

3. **Goal.** The concrete task and the exact result wanted — what to do and what
   not to do.

4. **Hints.** Examples, reference outputs, constraints, and things to avoid. If
   you have a sample of the desired result, give it to the model so it can match
   the shape.

5. **Format.** Tone, style, structure, and output shape (chat text, document,
   table, HTML page…).

A real instruction built this way is not one sentence — it is several paragraphs
covering role, context, examples, constraints, and format. That length is the
point: it is what pulls the specific answer out of a generic model. Don't pad it,
but don't shrink a hard task into a single line either.

**User-facing tip:** the user can hand you their rough request and this formula
and ask you to *rewrite* the request into a full structured prompt before running
it. Offer this when their ask is one vague line.
