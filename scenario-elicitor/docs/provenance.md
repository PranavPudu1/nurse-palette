# Provenance: what came from where, and what we changed

Min's requirement from the Aug 8 meeting: *"it will be very important for you to
document what exact part of it is from a previous paper, and if we changed or
adapted it, how it was adopted. If not we may unintentionally copy their stuff."*

This is that record. One row per design element: the source, and what we did
differently. Anything not listed here is our own.

**Companion document.** `grounding.md` covers the same material organized by
**pipeline component** rather than by source, and inlines the actual prompt that
runs each step. That is the one to hand someone who asks "what does this tool do
and why"; this one is the attribution ledger.

## Sources

| Short name | Full citation |
|---|---|
| **iRULER** | Bai, Cheong, Muller, Lim. "iRULER: Intelligible Rubric-Based User-Defined LLM Evaluation for Revision." CHI '26. DOI 10.1145/3772318.3790539 |
| **Parents** | Driscoll, Chen, Shi, Vucharatavintara, Yao, Jin. "Understanding Parents' Desires in Moderating Children's Interactions with GenAI Chatbots through LLM-Generated Probes." CHI '26. DOI 10.1145/3772318.3791622 |
| **PolicyPad** | Feng, Kuo, Chen, Cheong, Holstein, Zhang. "PolicyPad: Collaborative Prototyping of LLM Policies." CHI '26. DOI 10.1145/3772318.3791689. CC-BY. Code: github.com/kjfeng/policypad |
| **Botender** | Kuo, Liu, Chen, Seering, Zhang, Zhu, Holstein. "Botender: Supporting Communities in Collaboratively Designing AI Agents through Case-Based Provocations." CHI '26. DOI 10.1145/3772318.3790500. CC-BY |
| **Robinson** | Robinson, O. C. "Probing in qualitative research interviews: Theory and practice." Qualitative Research in Psychology 20, 3 (2023), 382-397. Cited by Parents as their probing method |
| **ICAI** | Findeis, Kaufmann, Hullermeier, Albanie, Mullins. "Inverse Constitutional AI: Compressing Preferences into Principles." ICLR 2025 |
| **GATE / OPEN / Farsight** | Li et al. 2023; Handa et al. 2024; Wang et al. CHI 2024. Motivation and the fan-out idea |

**Important:** PolicyPad's appendix contains **no prompts**; its prompt wording is
in the open-source repo. Cite the paper for technique, the repo for wording.
Botender's prompts **are** in its Appendix A and can be cited directly.

---

## The table

| # | Our element | Source (section / figure) | What we adapted or changed |
|---|---|---|---|
| 1 | **Case display: synopsis on top, then the conversation** | PolicyPad §5.2.2, Fig. 5D. Their scenario = background summary + collapsed history + latest user turn + latest AI turn | Same two-layer structure. Ours is generated at fan-out time rather than summarized from a real transcript, uses one exchange rather than 1-5 turns, and ends in an empty authoring box rather than a response to critique. **We dropped their progressive disclosure on the answering screen** (Aug 9): the conversation is always visible there, because it is also the test surface and hiding it hid the thing the person is supposed to react to. The collapsed form is kept on the cases overview, where it is only a preview |
| 2 | **Scenario chat: test the rule, revise, test again** | PolicyPad §5.2.5, Fig. 8. Two testing paths: regenerate the latest reply, or continue the conversation. Responses stamped with the policy version; earlier versions browsable | We implement both paths per case. Differences: PolicyPad replaces the response in place and versions the whole policy document across all scenarios; ours versions **one rule for one case**, and rather than making earlier versions browsable it **stacks every answer in one transcript, newest last, each stamped with the rule that produced it**, so the comparison needs no navigation. Their per-response "what changed" note was cut as clutter (App. B.3); we keep a single short line and no more |
| 3 | **Delivering the rule to the model** | PolicyPad §5.3: *"The policy was fed into the model as a system prompt with some additional scaffolding to ensure the model followed it."* Precedence line modeled on their repo scaffold (`src/lib/backend-utils.ts`) | Technique adopted; wording rewritten in our voice for the parent domain. We also generate an unsteered baseline reply, which PolicyPad does not do |
| 4 | **Rubric criteria structure** (named criteria, weights, 4 ordinal levels of observable evidence) | iRULER §4.1.1, App. B; four criteria not five per their fn.12 and participant R21 | Structure adopted. Content is ours, from Parents (below). iRULER's own instrument is 3 unweighted booleans on a whole document; ours is weighted, leveled, and per answer |
| 5 | **Why / Why-not-higher feedback** | iRULER prompt A.1.1, "Overall-Supporting" shape | Adopted, including the always-visible Why-not since it was their most-used feature (Table 4) |
| 6 | **Minimal targeted revision, apply or ignore** | iRULER A.1.2 minimal-modification directive; §7.3.1 on suggestions requiring user review | Adopted. We target the single weakest criterion. Their 100% acceptance rate is treated as a warning, so ignoring must stay easy |
| 7 | **Rubric criteria content** (action + target, boundaries without seeding ideas, developmental fit, deferral with reasons) | Parents §4.2, §5.3, Table 4 | Derived from their coded moderation themes, generalized beyond parenting. Interpretive synthesis, not a one-to-one mapping; see design-rationale.md |
| 8 | **Case themes** for the kids domain | Parents Table 3 concern taxonomy | Used verbatim as the case categories so each case carries a stated rationale |
| 8b | **The per-case `probe`** ("As you write, consider: ..."), one counterfactual question shown beside the case while the person writes | Parents §3.5 p.7: *"We employed probing techniques [85] to prompt elaboration, comparisons, and consideration of hypothetical variations."* The technique itself is **Robinson 2023**, which Parents cites; credit both. The three variation axes (different age or audience, more serious version, unclear intent) are Parents' context dimensions, the same list the confirm step varies | Our prompt wording is ours; the only textual echo is "consider a variation of this case" against their "consideration of hypothetical variations". **Weaker than theirs by design and worth stating:** their probes are a live interviewer responding to what the parent just said; ours is one line fixed at case-generation time that cannot adapt. The adaptive counterpart in our tool is the separate GATE clarifier round, not this. Placement beside the case rather than after the rubric score was Min's flow feedback, not a paper's |
| 9 | **Injecting a published taxonomy into the generator prompt** | *Not derived from Botender.* We had already put the Parents taxonomy in the case generator during the Aug 7 kids-domain work, before reading Botender on Aug 8. Botender A.2.3 does the same thing with Kraut and Resnick's categories | Listed for honesty in the other direction: this is convergent, not borrowed. What we did take from A.2.3 is the **attribution convention** of citing the technique and the embedded taxonomy separately |
| 10 | **"A case must be worth showing" filter** | Botender A.2.1 evaluator: infer the default outcome, keep the case only if the actual outcome visibly differs | Adopted as our novelty rule: drop a case whose answer is already settled by what the parent has said. This is the mechanism behind "surfaces what you had not considered" |
| 11 | **Anti-triviality and surface self-evidence constraints** | Botender A.2.1-A.2.3 ("Do not list trivial ambiguities...", "apparent to a human without explanation") | Adopted as a reworded quality bar in our case prompts. Phrasing pattern is theirs; wording is ours |
| 12 | **Capability envelope block** | Botender A.2.5 "Bot Capability" | Adopted; ours lists what a content filter can do (allow, soften, add context, decline and explain, bring the parent in) |
| 13 | **Non-action as a valid outcome** | Botender A.1.2 (`"n/a"`) and Fig. 3 ("No Task is Triggered") | Adopted so cases can legitimately resolve to letting content through, avoiding a tool that only elicits restriction |
| 14 | **Set-level selection with diversity and permitted imbalance** | Botender A.2.4 Step 3 | Adopted as an instruction in our generators. We do not run their separate selector module |
| 15 | **Boundary comparisons varying one dimension** | Three dimensions are named in Parents **§7 Future Work** verbatim: *"intent clarity, risk level, developmental cues, and when handover is needed"* -> clarity of intent, severity, age/maturity. The fourth, source of risk, is their **Table 14** (System Risk vs Misuse Risk). ICAI supplies the reason pairwise data is worth collecting (reconstruction accuracy) | The mechanism is ours. Neither PolicyPad nor Botender has a controlled single-variable comparison. **Open problem:** which dimension gets picked is an LLM judgment in the prompt, not a selector targeting expected disagreement or cycling for coverage; recorded in the `dimension` field so coverage is analyzable after the fact. Min called dimension choice "the key" (July 29) |
| 16 | **Structured export** | PolicyPad §4 explicitly defers low-to-high fidelity translation | Ours. Their artifact is a free-text document; ours is a machine-consumable bundle |
| 17 | **Case fan-out itself** | Farsight (Wang et al., CHI 2024) for the fan-out; PolicyPad §9 names taxonomy-scaffolded sessions as future work | Ours generates from an external taxonomy before any rule exists |
| 18 | **`[Empty]` no-op, one idea per statement, abstention when unsure** | PolicyPad repo (`backend-utils.ts`), CC-BY | Prompt techniques adopted; cite the repo, not the paper |

---

## Scope note: how much of this is Botender

Botender's entire footprint in our tool is one prompt block, `_CASE_QUALITY`
in `prompts.py`, injected into all three case generators. None of it is
visible in the UI. Within that block, the **"not already settled"** rule
(row 10) is the substantive borrowing; the capability envelope and non-action
outcome (rows 12-13) are real but small; the anti-triviality, self-evidence,
and diversity constraints (rows 11, 14) are close to generic prompt hygiene
that Botender happens to codify, and are cited as phrasing patterns rather
than as ideas we would not otherwise have had.

## Line-level phrasing

We do not copy sentences from either paper into our prompts. Two patterns are close
enough to name explicitly:

- The **"do not include trivial / style-only / obvious"** constraint stack is
  modeled on Botender A.2.1-A.2.3, reworded for content filtering.
- The **precedence line** in our system prompt ("if being brief would conflict with
  the instructions, follow the instructions") is modeled on PolicyPad's repo
  scaffold, reworded.

## Clearly ours

Taxonomy-conditioned cold-start case generation; free-text authoring of an ideal
behavior per case in an empty box; the weighted leveled rubric applied per answer
with next-level guidance; boundary comparisons varying exactly one dimension;
structured export; and the single-parent, single-session deployment with resume
codes and full revision history.

## Two corrections to earlier assumptions

Recorded so they are not repeated:

1. **Botender's cases are machine-generated**, not proposed by people (95% of the
   800 saved cases came from its algorithm). The "people propose the cases"
   description belongs to **PolicyCraft** (CHI '25), which Botender supersedes.
   Our actual difference is **conditioning**: Botender's detectors read a rule the
   user already wrote and critique it, so it cannot start from nothing; ours
   generates from a published taxonomy before any rule exists.
2. **PolicyPad has no side-by-side before/after.** It replaces the response and
   versions it. Our side-by-side comparison of the previous version against the
   new one is our own variation.

## Positioning (useful, and honest)

Parents §7 asks for *"scenario-based tools that measure these factors at scale"*
for exactly the factors our confirm step varies, and their §6.2 limitation about
priming is what our pre-feedback first-draft logging addresses.

PolicyPad's own future work names this population: *"parents who are concerned
about their children interacting with AI companions"* (§8.2). It also names
taxonomy-scaffolded sessions (§9) and low-to-high fidelity translation (§4) as
open. Botender names rubric-style refinement suggestions (§7.2.2) and adaptive
probing (§7.1.2) as open. Several of our contributions sit exactly in those gaps,
which is a strength, but it should be stated as *instantiating their stated future
work*, not as an idea nobody had considered.
