# Evaluation metrics: survey and proposal

Part 1 surveys the metrics used by the two anchor papers (as Min asked,
especially iRULER's). Part 2 proposes the metric set for evaluating the Scenario
Elicitor, mapping each metric to what the deployed tool already logs.

Citations: iRULER = Bai et al., CHI '26 (10.1145/3772318.3790539); Parents =
Driscoll et al., CHI '26 (10.1145/3772318.3791622); ICAI = Findeis et al.,
ICLR 2025.

---

## Part 1a. iRULER's evaluation metrics

Study portfolio (§5, p.9): two between-subjects controlled experiments (Writing
Revision N=48, Rubric Creation N=36; three conditions each: Text-LLM, Rubric-LLM,
iRULER), one qualitative end-to-end study (N=6), and a validation of the metric
itself against human experts.

1. **Artifact quality via LLM-as-a-judge, validated.** Final scores and score
   improvement (dScore) from a Text-based LLM judge and their Rubric-based LLM
   judge (§5.2.3, p.10). The judge was validated twice: (a) intra-model
   reliability on 640 expert-scored ICNALE essays, five runs each, Krippendorff
   alpha .82-.95 and expert agreement QWK = .68 (§4.4, pp.8-9); (b) against two
   expert writing tutors on 96 study essays: expert inter-rater alpha .96, and
   Rubric-LLM vs experts **QWK = .88** (vs .76 for the text judge) (§5.5 p.11;
   §6.5 p.15; Table 3). Stance: the judge is "a consistent, rubric-aligned
   proxy," not a replacement for humans (p.9).
2. **Skill transfer.** Pre-task and post-task revisions done WITHOUT AI; skill
   transfer = post-task gain minus pre-task gain (§5.2.3, p.10). iRULER
   produced the largest transfer (Fig. 12, p.13).
3. **Efficiency.** Task time and number of iterations from usage logs (§5.2.3).
   iRULER needed the fewest writing iterations (M = 2.09 vs 3.38 for Text-LLM,
   §6.1.2 p.12); no time difference.
4. **Feature usage.** Click counts per intelligibility feature: Why (M = 3.69),
   Why-Not (M = 5.03, the most used), How-To (M = 2.78) per session, with
   per-feature helpfulness ratings (Table 4, p.25).
5. **Perceived qualities.** 7-point Likert (-3..+3) on helpfulness,
   correctness, and sense of control after each revision (§5.2.3). Note the
   null: no significant control effect in either experiment (§6.1.3, §6.2.3).
   Also: scores without explanations (Rubric-LLM) sometimes rated BELOW the
   plain text baseline (§6.2.3, p.13).
6. **Confidence pre/post.** Self-rated confidence in writing, reviewing,
   revising, using rubrics, before and after (§5.2.3); Text-LLM DECREASED
   confidence on some skills (§6.1.4, p.13).
7. **Statistics.** Linear mixed-effects models (Feedback Type + iterations as
   fixed effects; participant and task as random effects), post-hoc contrasts,
   Bonferroni-corrected alpha = .002 (§6, p.11).

## Part 1b. Parents paper's evaluation metrics

1. **Probe quality scales.** Every generated scenario rated by a small parent
   panel on two 7-point scales: realism ("How realistic, if at all, is this
   scenario...") and concern (Appendix E, p.26, including their note that both
   scales should run negative-to-positive for intuitive rating).
2. **Case selection by disagreement.** Keep scenarios with median realism > 4
   AND concern-rating variance > 1.0 ("scenarios that parents found
   controversial"), drop ones nobody was concerned by (§3.3, p.6). This is an
   operational definition of a good gray-area case.
3. **Diversity control.** LLM dedup agent plus SentenceTransformer
   (all-MiniLM-L6-v2) cosine similarity, threshold 0.85, treated as a heuristic
   filter (§3.2, p.5).
4. **Coding + saturation.** Grounded-theory coding (initial, focused, axial),
   four coders, six rounds, stopping at saturation (§3.6, p.7); frequencies
   reported with a fixed verbal scale (none / a few / many / majority / most /
   all, Fig. 4, p.8).
5. **Coverage visualizations.** Per-participant binary block maps and per-case
   heatmaps of which codes appeared (Figs. 5-10) - the per-user consistency
   view and the per-case discrimination view.

## Part 1c. ICAI's metric

**Annotation reconstruction accuracy**: compress pairwise preferences into
natural-language principles, then measure whether an LLM applying only those
principles reproduces the original pairwise choices (ICAI Abstract, Fig. 1).
Their use cases include "generating personal constitutions for customized model
behaviour."

---

## Part 2. Proposed metrics for the Scenario Elicitor

The tool now logs, per respondent: every draft at every Check (including the
pre-feedback first draft), per-criterion rubric levels and weighted score per
check, suggestion apply/ignore, every saved and revised answer, every confirm
pick with its varied dimension, timestamps for all of it (events table), and
demographics. That makes the following measurable with no extra instrumentation:

1. **Rubric effect on specification quality** (iRULER dScore analogue): change
   in weighted rubric score and per-criterion levels from the FIRST checked
   draft to the saved answer, per case and per person. Caveat logged per answer:
   `levels_current` is false when the saved text changed after the last check.
2. **Priming bound** (Parents §6.2 limitation): compare first drafts (written
   before any feedback) with final answers to quantify how much the rubric
   steered content, e.g. how often "boundary" language appears only after
   feedback flagged it.
3. **Behavior-choice agreement** (ICAI reconstruction, per person): does the
   authored ideal behavior predict the person's confirm-step pick for the same
   case? Report percent agreement overall and by varied `dimension`. A later,
   stronger version: give an LLM only the authored behaviors and measure
   reconstruction accuracy on the confirm picks.
4. **Case quality panel** (Parents §3.3): before a real study, run a small
   panel rating generated cases on the two 7-point scales and keep cases with
   median realism > 4 and concern/response variance > 1.0.
5. **Effort and reliance**: n_revisions (checks per case), used_suggestion
   rate, edit-before-submit rate, per-step time from event timestamps (iRULER
   efficiency + feature-usage analogues).
6. **Perceived measures** (if we add an exit survey): 7-point helpfulness and
   correctness following iRULER; do NOT expect or claim a sense-of-control
   effect (their null result).
7. **Coverage views**: per-respondent block map of which rubric criteria
   reached level 3+ across cases; per-case heatmap of confirm-pick splits
   across respondents (the Parents Figs. 5-10 pattern) - the per-case split
   also identifies which cases are good discriminators.
