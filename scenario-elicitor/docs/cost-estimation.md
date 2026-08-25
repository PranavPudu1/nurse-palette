# Cost estimation: online data collection

What it costs to collect data with the deployed Scenario Elicitor, per
respondent and per study size. Numbers marked MEASURED come from instrumented
live runs against the real OpenAI API (token counts captured per call); the
rest are listed assumptions.

Last measured: 2026-08-04, current app version (rubric v2, confirm step,
opt-in reference response).

## Assumptions

- Model: gpt-4o-mini at $0.15 per 1M input tokens, $0.60 per 1M output tokens
  (OpenAI list pricing at time of writing; re-check before budgeting).
- A "typical" respondent: 6 generated cases, one rubric check per case, a
  couple of minimal-revision requests, all 6 confirms, no theme drill-down, no
  GATE round, never opens the reference response.
- A "heavy" respondent: everything on: Surface more (+3 cases), a GATE round
  (+3 cases), a check on every case, suggest+apply on the first 9, 12 confirms.
- Hosting: Railway Hobby plan; one small Streamlit service; SQLite on a
  mounted volume (no separate database service).
- Email: Gmail SMTP via app password (free, ~500 recipients/day cap).
- Respondents arrive mostly sequentially (recruitment through the lab's
  channels, not a crowdsourcing platform burst; Min's assumption).

## Per-respondent API cost (MEASURED)

Heavy respondent, live run: **37 calls, 22,788 input + 8,553 output tokens =
$0.00855** (about 0.9 cents). Breakdown:

| call | n | input | output |
|---|--:|--:|--:|
| scenarios (generate + drill-down + GATE) | 3 | 2,718 | 2,128 |
| rubric_feedback (Check) | 12 | 11,190 | 3,885 |
| confirm_pairwise | 12 | 5,305 | 1,594 |
| revision (Suggest) | 9 | 3,461 | 911 |
| agent_frame | 1 | 114 | 35 |

Typical respondent (scaled from the measured per-call averages): ~10K input +
3.7K output = **about $0.004**. Practical planning number: **$0.005-0.01 per
respondent**; the rubric check is the dominant cost and scales with how often
people click Check.

For reference, the pre-rubric-v2 app measured $0.00797 heavy; v2 is nearly
unchanged because the reference-response call became opt-in (12 saved calls)
while rubric feedback grew.

## Hosting cost

- Railway Hobby plan: **$5/month**, includes $5 of usage.
- A single small Streamlit service (0.1-0.3 vCPU, 300-500 MB RAM typical for
  this app) lands around **$3-8/month** of usage, i.e. usually inside the
  included credit.
- Volume for SQLite: $0.15/GB/month. Each respondent stores roughly 50-200 KB
  (events + snapshots), so even 1,000 respondents is under 0.2 GB: pennies.
- Email: $0 (Gmail), up to ~500 sends/day.

## Study-size totals

| | 100 respondents | 1,000 respondents |
|---|---|---|
| API (typical..heavy) | $0.40 - $0.86 | $4 - $8.60 |
| Hosting (2-month study window) | ~$10 - $16 | ~$10 - $16 |
| Email | $0 | $0 |
| **Total** | **~$11 - $17** | **~$15 - $25** |

The API is effectively free at this scale; hosting duration dominates. Even
tripling every assumption keeps 1,000 respondents under ~$75.

## What changes at 5,000 respondents

- **API**: still small (~$25-45 total), but request-rate limits matter if a
  crowdsourcing platform sends bursts; OpenAI tier limits on requests/minute
  would need a queue or backoff. Unlikely off-platform (Min's point that
  simultaneous access mostly happens with crowdsourcing recruitment).
- **Database**: move SQLite to Railway Postgres (~$5-10/month). SQLite on one
  volume is fine for sequential traffic but is the first thing to break under
  concurrent writers and prevents running more than one app replica.
- **App capacity**: one Streamlit process comfortably handles a handful of
  simultaneous sessions (LLM calls are I/O waits); for bursts, scale the
  service up (more RAM/CPU, ~$10-20/month) or run replicas behind Railway's
  router, which requires the Postgres move first.
- **Email**: Gmail's ~500/day cap becomes the bottleneck; switch to SendGrid
  (free 100/day, paid ~$20/month) or Amazon SES (~$0.10 per 1,000 emails).
- **Ops**: add automated DB backups (a scheduled dump of the volume or
  Postgres backups) and basic monitoring before any large run.

## Not included

Crowdsourcing platform participant payments (out of scope per Min), IRB costs,
and researcher time. If respondents are paid (e.g. $8-12 on Prolific), payments
dwarf every technical cost above by two orders of magnitude.
