"""Create a DRAFT Prolific study for the Scenario Elicitor via the Prolific API.

Prolific has no official CLI; this is the standard route (docs.prolific.com).
The script only ever creates a DRAFT: you review and publish it in the Prolific
dashboard, where payment happens. Nothing is spent by running this.

Usage:
    export PROLIFIC_API_TOKEN=...   # prolific.com -> settings -> API tokens
    python3 prolific_setup.py [--places 10] [--reward-cents 900] [--minutes 25]

Reads nothing else from the repo; edit STUDY below to taste. If no token is
set, it prints manual setup instructions instead of failing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

API = "https://api.prolific.com/api/v1"
STUDY_URL = ("https://scenario-elicitor-production.up.railway.app/"
             "?src=prolific&PROLIFIC_PID={{%PROLIFIC_PID%}}"
             "&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}")

STUDY = {
    "name": "Teach an AI content filter how you want it to behave (parents)",
    "description": (
        "You will set up preferences for an AI that curates news and content "
        "for your child. You will review concrete situations, write how the AI "
        "should behave in each, get feedback, and confirm your preferences with "
        "a few comparisons. At the end you receive a completion code to enter "
        "here, and you can optionally email yourself your results."),
    "external_study_url": STUDY_URL,
    "prolific_id_option": "url_parameters",
    "completion_option": "code",
    # Participants finish on our site, get their unique code, and enter it on
    # Prolific. We verify codes against our database (admin view) and approve.
    "completion_codes": [{
        "code": "SCENARIO-DONE",
        "code_type": "COMPLETED",
        "actions": [{"action": "MANUALLY_REVIEW"}],
    }],
    "device_compatibility": ["desktop"],
    # Filters can be tightened in the dashboard (e.g. parents of children 6-18).
}


def manual_instructions() -> str:
    return (
        "No PROLIFIC_API_TOKEN set. Manual setup:\n"
        "1. prolific.com -> New study -> External study.\n"
        f"2. Study URL: {STUDY_URL}\n"
        "3. Record Prolific IDs: choose 'via URL parameters'.\n"
        "4. Completion: participants enter a code; choose manual review.\n"
        "5. Add screeners (e.g. parents of children aged 6-18), set reward,\n"
        "   places, and estimated time, then preview before publishing.\n"
        "Verification: open the app with the ADMIN_CODE to download the\n"
        "respondents CSV (prolific_id + unique completion_code + submitted_at)\n"
        "and approve matching submissions on Prolific."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", type=int, default=10)
    ap.add_argument("--reward-cents", type=int, default=900,
                    help="payment per participant in cents (Prolific units)")
    ap.add_argument("--minutes", type=int, default=25,
                    help="estimated completion time")
    args = ap.parse_args()

    token = os.environ.get("PROLIFIC_API_TOKEN", "").strip()
    if not token:
        print(manual_instructions())
        return 0

    body = dict(STUDY)
    body["total_available_places"] = args.places
    body["reward"] = args.reward_cents
    body["estimated_completion_time"] = args.minutes

    req = urllib.request.Request(
        f"{API}/studies/",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Token {token}",
                 "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("Prolific API error:", e.code, e.read().decode()[:800])
        return 1

    sid = data.get("id", "?")
    print("Draft study created (NOT published).")
    print("  id:    ", sid)
    print("  status:", data.get("status"))
    print(f"  review it at: https://app.prolific.com/researcher/studies/{sid}")
    print("Publish from the dashboard when ready; payment happens there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
