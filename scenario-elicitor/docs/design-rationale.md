# Design rationale

Four components need more than a table row, because the reasoning behind them is
what a reviewer will ask about. Everything else is in
[provenance.md](provenance.md).

Sources are cited there. Current as of v0.4.

---

## 1. Why a rubric at all

**The problem.** A blank box produces vague rules. A pre-filled AI answer
produces agreement: people accept what is in front of them.

**What we do.** The person writes in their own words, and the draft is scored
against four named criteria with four written levels each. The score is not a
judgment of their values. It checks one narrower thing: whether the rule is
specific enough that an agent could follow it. A rule can be exactly right about
what someone wants and still be unusable.

**Where it comes from.** The structure is iRULER's: named criteria, ordinal
levels described in terms of observable evidence, and a why-not-higher
explanation attached to each. Their instrument is three unweighted booleans over
a whole document; ours is four weighted criteria over one rule.

The criteria *content* is ours, synthesised from Driscoll's coded moderation
themes. This is interpretation, not extraction: they coded what parents said
they wanted the AI to do, and we turned recurring shapes in that into four
dimensions a rule can be scored on. Nobody should be able to point at a table in
that paper and find these four.

**What we removed.** iRULER offers a minimal AI revision targeting the weakest
criterion, and we built it. It is gone. Their own participants accepted 100% of
suggestions offered, which makes it a channel for the model's language to become
the person's stated preference. In its place the tool quotes the person's own
earlier answers back when their rule does not mention them.

**One thing found only against the real model.** Feeding the reflection answers
into the scorer inflated it: a draft naming no audience scored level 4 on "Fits
the audience" in two of three runs, because the model credited intent it had
seen in the reflection rather than in the rule. The prompt now fences the draft
as the only scorable text. The offline mock could not have surfaced this, since
it isolates each prompt.

---

## 2. Why comparisons, and why three rounds twice

**The problem.** What someone writes and what they would actually choose are
different things. A rule can sound complete and still fail to decide a real case.

**What we do.** Two candidate replies to one concrete moment, differing in
exactly one respect. The person picks and says why, before seeing anything the
model did.

The single-variable constraint is what makes a pick informative. If two things
differ, a preference for one option says nothing specific. The four dimensions
varied are the child's age or maturity, how serious the situation is, how clear
the child's intent is, and where the risk originates; the first three are named
in Driscoll's future work, the fourth is their system-risk/misuse-risk split.

**Why the rounds run twice.** They test two different claims.

Per theme, right after a rule is written, the model follows *only that rule*. A
disagreement points at a gap in that rule, and round 2 hands the rule box back so
the person closes it in their own words. Round 3 then scores the edited rule,
which measures whether their own revision actually worked.

At the end, the model follows *one policy synthesised from every rule and every
pick*. That is the ICAI claim: if a written policy really captures what someone
wants, a model reading only that policy should reproduce their choices. Round 3
is frozen because agreement means nothing if the thing being measured changes
while it is measured.

**Commit before reveal, everywhere.** The reason is typed before the model's
answer appears. Reversing that would make the reason a reaction rather than a
view, and the agreement number would stop meaning anything.

**Open problem.** Which dimension a comparison varies is chosen by the model
inside the prompt. It is not a selector targeting expected disagreement, and it
does not cycle to guarantee coverage. The choice is recorded per comparison so
coverage can be analysed afterwards, but this is the weakest part of the design
and Min has flagged it as the key one.

**Second open problem.** With small round sizes, agreement can only take a few
values. Three items means 0, 33, 67 or 100 percent, which is too coarse to
separate two participants. Round sizes are constants so they can be raised once
the session has been timed.

---

## 3. Why the case gives so little away

**The problem.** Everything shown before someone writes shapes what they write.

**What we do.** The case card carries a title and what happened. It used to also
carry what was at stake, the values in tension, how it plays out, and who is
affected. All four are gone from the screen, on Min's reading that the card was
answering the question before the participant could.

What is at stake and the competing values are still generated, and are still
passed to the question generator — as material for questions rather than as
prose. The same content arrives as something to think about instead of something
to agree with. What is at stake also survives in the export, because a benchmark
row that says what an agent should do but not what it was deciding between is
not usable.

**The baseline reply is a product, not a model.** The "before" in every
comparison applies the safeguards a mainstream child mode ships with:
age-appropriate wording, pointing to a trusted adult on serious topics, no
graphic detail, a crisis resource if self-harm comes up. It has no length limit.
It was capped at two to four sentences, which made the before-state read as
unrepresentatively terse next to a real product, so any difference a parent saw
after writing a rule was partly an artefact of our own instruction. This layer is
reconstructed from behaviour these products publicly document. We do not have
anyone's real system prompt and should never imply otherwise.

---

## 4. Why the workspace is shaped the way it is

**The problem.** Min's finding on a screen share: while writing a rule, the
rubric and the reflective questions were unreachable. Everything was stacked in
one column, so by the time someone was typing, what they needed had scrolled
away.

**The constraint.** A theme must fit one viewport without the page scrolling.
The case, its conversation, the questions, the rule box and the rubric do not fit
together at any honest font size, so every layout has to earn space somehow.

**Four prototypes**, so the choice is made from seeing rather than describing.
**A** stages the work under a pinned case, one block at a time. **B** shows
everything at once in three columns. **C** gives the case the left half
permanently and steps the work down the right. **D** makes the conversation the
page and docks the work beneath it.

They share every primitive and write the same session keys, so switching cannot
lose work and no layout can pass a check the others fail. A test asserts all four
produce identical state from identical input. The switcher appears only in test
sessions.

**A bug the prototypes exposed.** Streamlit discards widget state as soon as a
widget stops being rendered. In the staged layouts, moving to the next stage
silently emptied the rule box and every answer already typed. Values now live in
plain session keys that nothing unmounts. Worth recording because it would have
destroyed participant work in a way nobody would have reported: the box is simply
empty when they come back to it.

**Answers are collected in text areas, not single-line inputs.** They were
inputs, which showed roughly the first eight words and hid the rest behind the
cursor.
