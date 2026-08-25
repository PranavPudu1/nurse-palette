"""Email the respondent their results via Gmail SMTP.

Requires env vars GMAIL_USER and GMAIL_APP_PASSWORD (a Google app password;
needs 2-step verification on the account). If they are missing, is_configured()
is False and the UI shows a graceful note instead of the email button.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

INSTRUCTIONS = """\
Thanks for building your AI preference profile.

Attached:
- agent_preferences.json: your full profile (the cases, your ideal behaviors,
  and your boundary picks).
- agent_benchmark.jsonl: one line per case with your ideal behavior. You can use
  it to test whether any AI behaves the way you want.

How to use your profile with a commercial AI (ChatGPT, Claude, Gemini):
1. Open a new chat and paste something like: "Here is how I want you to behave
   when acting as my agent. Follow these preferences." Then paste the
   ideal_behavior lines from the JSON.
2. In ChatGPT you can put them in Settings > Personalization > Custom
   Instructions; in Claude, in a Project's instructions; in Gemini, in Saved
   Info. The AI will then apply your preferences across chats.
3. To test an AI instead: give it one "situation" from the benchmark file, ask
   how it would behave, and compare its answer to your ideal_behavior.

This profile was created with the Scenario Elicitor, a research prototype from
the Human-AI Interaction Lab at UT Austin.
"""


def is_configured() -> bool:
    return bool(os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_APP_PASSWORD"))


def send_results(to_email: str, profile_json: str, benchmark_jsonl: str) -> str | None:
    """Send the results email. Returns None on success, else an error string."""
    user = os.environ.get("GMAIL_USER", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not (user and pw):
        return "Email is not configured on this server."
    msg = EmailMessage()
    msg["Subject"] = "Your AI preference profile"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(INSTRUCTIONS)
    msg.add_attachment(profile_json.encode("utf-8"), maintype="application",
                       subtype="json", filename="agent_preferences.json")
    msg.add_attachment(benchmark_jsonl.encode("utf-8"), maintype="application",
                       subtype="jsonl", filename="agent_benchmark.jsonl")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(user, pw)
            s.send_message(msg)
        return None
    except Exception as exc:  # noqa: BLE001, surface the error to the UI
        return str(exc)
