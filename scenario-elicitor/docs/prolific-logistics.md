# Prolific logistics for the study

How Prolific works today, what our tool already supports, and the recommended
setup. Researched 2026-08; sources at the end.

## How a Prolific study runs

1. You create a study (dashboard or API) with an **external study URL** (our
   Railway link), a reward, participant count, estimated time, and screeners
   (e.g. parents of children aged 6-18; Prolific has built-in demographic
   filters for parental status and child ages).
2. Prolific sends participants to the URL with their ID attached as a query
   parameter (`PROLIFIC_PID`), plus STUDY_ID and SESSION_ID.
3. Participants finish and confirm completion one of two ways:
   - **Completion URL redirect** (Prolific's recommended default): the site
     sends them back to a Prolific link that auto-registers completion.
   - **Completion code**: they copy a code shown at the end and paste it into
     Prolific. The older method, still fully supported, and the safe fallback
     when a redirect is awkward.
4. You review submissions and **approve or reject**; approval triggers payment.
   Completion codes can carry **automated actions** (auto-approve, hold for
   manual review). An incorrect or NOCODE entry does not automatically mean an
   invalid submission; Prolific tells researchers to verify against their own
   data before rejecting.

## The misuse concern Min raised (shared codes)

Min described the old single-shared-code problem. Current practice solves it
exactly the way she remembered evolving: per-participant verification. Our tool
generates a **unique 8-character completion code per respondent at submission**,
stored with their Prolific ID and timestamp. Verification = match the code the
participant entered on Prolific against our database. A shared or leaked code
matches at most one submission, so freeloading fails.

## What the tool already supports (built)

- Captures `PROLIFIC_PID` automatically from the study URL (no typing); if the
  link says `src=prolific` but no PID arrived, a required Prolific ID field
  appears at entry.
- Unique completion code generated, stored, and displayed at submission with
  return instructions.
- **Admin verification view**: open the app, enter the ADMIN_CODE, and you get
  the sheet Min described - every respondent's Prolific ID, completion code,
  and submission time, plus a CSV download - for click-through approval on
  Prolific. At 48 people this is a few minutes of manual approval; at larger
  scale, the API's automated approve action or a small script over the CSV
  automates it.
- `prolific_setup.py`: creates the DRAFT study via Prolific's API (no official
  CLI exists; the API is the standard route). It never publishes; publishing
  and payment stay in the dashboard. Falls back to printed manual-setup steps
  if no API token is set.

## Platform comparison (short)

- **Prolific** - built for research; strong screeners (incl. parental status /
  child ages), good data quality reputation, per-participant pricing plus ~33%
  platform fee. Recommended, and what Min asked to target.
- **CloudResearch Connect** - similar quality tier, sometimes cheaper/faster
  for US samples; fewer built-in niche screeners than Prolific.
- **MTurk** - cheapest, but requires heavy quality screening yourself
  (attention checks, qualification filters); generally not preferred for HCI
  studies anymore.
- University pools / lab channels - free but slow and small; fine for pilots
  (and no concurrency concerns, per Min's note).

## Recommended setup for our study

1. Pilot with lab members via the normal link first (access code, no Prolific).
2. Run `prolific_setup.py` with a Prolific API token to create the draft study
   pointed at the live URL with PID capture; add screeners in the dashboard
   (parents, child age band, fluent English), set reward for ~25 minutes at a
   fair hourly rate; publish a small batch (e.g. 10) before scaling.
3. Approve via the admin CSV: filter to submitted, match completion codes,
   approve on Prolific. Reject only after checking our data, per Prolific
   guidance.
4. If we later want zero-touch: switch the study to completion-URL redirect
   plus the auto-approve action (both supported by the API; one small change in
   the submit screen to show the redirect link).

## Sources

- [Prolific API: create a draft study](https://docs.prolific.com/api-reference/studies/create-study)
- [Prolific API: the study object (completion codes, actions)](https://docs.prolific.com/api-reference/studies/the-study-object)
- [Custom completion codes](https://researcher-help.prolific.com/en/articles/445170-custom-completion-codes)
- [Data collection (completion URL vs code)](https://researcher-help.prolific.com/en/articles/445127-data-collection)
- [NOCODE / wrong code guidance](https://researcher-help.prolific.com/en/articles/445211-participants-are-completing-my-study-with-nocode-or-the-wrong-completion-code)
