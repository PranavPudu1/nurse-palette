"""SQLite persistence for online data collection.

Three tables:
  respondents - one row per unique respondent (demographics, resume code,
                test flag, submission time).
  events      - append-only log of everything that happens (every draft check,
                save, edit, confirm pick, rubric edit, navigation), so ALL
                iterations are recorded, not just the final answers.
  snapshots   - latest full session state per respondent, for resume-later.

DB path: $DATA_DIR/elicitor.db (defaults to ./data next to the app). On Railway
DATA_DIR points at a mounted volume so data survives deploys.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Unambiguous alphabet for resume codes (no 0/O, 1/I/L).
_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _db_path() -> Path:
    root = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
    root.mkdir(parents=True, exist_ok=True)
    return root / "elicitor.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS respondents (
            id TEXT PRIMARY KEY,
            resume_code TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            name TEXT, age_range TEXT, gender TEXT,
            ai_familiarity INTEGER, occupation TEXT, email TEXT,
            is_test INTEGER NOT NULL DEFAULT 0,
            submitted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            respondent_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            step TEXT, kind TEXT NOT NULL,
            payload TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_events_resp ON events(respondent_id);
        CREATE TABLE IF NOT EXISTS snapshots (
            respondent_id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            state TEXT NOT NULL
        );
        """)
        # Additive migration for columns added after first deploy (safe on
        # existing databases; ALTER fails silently if the column exists).
        for col, decl in (("child_age", "TEXT"), ("prolific_id", "TEXT"),
                          ("completion_code", "TEXT"), ("condition", "TEXT")):
            try:
                c.execute(f"ALTER TABLE respondents ADD COLUMN {col} {decl}")
            except sqlite3.OperationalError:
                pass  # already there


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_respondent(*, name: str, age_range: str = "", gender: str = "",
                      ai_familiarity: int | None = None, occupation: str = "",
                      child_age: str = "", prolific_id: str = "",
                      is_test: bool = False, condition: str = "") -> tuple[str, str]:
    """Returns (respondent_id, resume_code).

    `condition` is the study arm. It is written here rather than derived later
    so the arm survives independently of the session snapshot.
    """
    init_db()
    rid = uuid.uuid4().hex
    code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
    with _conn() as c:
        c.execute(
            "INSERT INTO respondents (id, resume_code, created_at, name, age_range,"
            " gender, ai_familiarity, occupation, child_age, prolific_id, is_test,"
            " condition)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, code, _now(), name, age_range, gender, ai_familiarity,
             occupation, child_age, prolific_id, int(is_test), condition))
    return rid, code


def set_completion_code(rid: str) -> str:
    """Generate, store, and return the Prolific-style completion code."""
    code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
    with _conn() as c:
        c.execute("UPDATE respondents SET completion_code = ? WHERE id = ?",
                  (code, rid))
    return code


def get_respondent(rid: str) -> dict | None:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM respondents WHERE id = ?", (rid,)).fetchone()
    return dict(row) if row else None


def list_respondents() -> list[dict]:
    """All respondents for the admin verification view, newest first."""
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name, prolific_id, resume_code, completion_code, "
            "created_at, submitted_at, is_test, condition, child_age FROM respondents "
            "ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def condition_counts(include_test: bool = False) -> dict[str, int]:
    """How many respondents are in each arm, for balanced assignment.

    Test and poster-demo sessions are excluded by default so they cannot skew
    the real cell sizes.
    """
    init_db()
    sql = ("SELECT condition, COUNT(*) AS n FROM respondents "
           "WHERE condition IS NOT NULL AND condition != ''")
    if not include_test:
        sql += " AND is_test = 0"
    sql += " GROUP BY condition"
    with _conn() as c:
        rows = c.execute(sql).fetchall()
    return {r["condition"]: r["n"] for r in rows}


def get_by_code(code: str) -> dict | None:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM respondents WHERE resume_code = ?",
                        ((code or "").strip().upper(),)).fetchone()
    return dict(row) if row else None


def log_event(rid: str, step: str, kind: str, payload: dict | None = None) -> None:
    if not rid:
        return
    try:
        with _conn() as c:
            c.execute("INSERT INTO events (respondent_id, ts, step, kind, payload) "
                      "VALUES (?,?,?,?,?)",
                      (rid, _now(), step, kind,
                       json.dumps(payload or {}, ensure_ascii=False, default=str)))
    except sqlite3.Error:
        pass  # never break the flow over logging


# Only canonical state is snapshotted. Button/checkbox widget keys must never be
# restored (Streamlit forbids assigning button values via session_state), so we
# allowlist instead of taking every sb_* key.
_SNAPSHOT_KEYS = {
    "sb_step", "sb_step_key", "sb_condition",
    "sb_theme", "sb_tphase", "sb_themes_done", "sb_tcidx", "sb_tround",
    "resp_child_age", "sb_age_input", "sb_name_input",
    "sb_rqi",
    "sb_agent", "sb_frame", "sb_desc", "sb_audience", "sb_scenarios",
    "sb_next_id", "sb_idx", "sb_answers", "sb_examples", "sb_confirm",
    "sb_confirm_cache", "sb_rubric", "sb_submitted",
    "sb_cmp", "sb_revealed",
}
_SNAPSHOT_PREFIXES = ("sb_answer_", "sb_first_", "sb_fb_", "sb_lastfb_",
                      "sb_stage_", "sb_final_",
                      "sb_nrev_", "sb_cnote_",
                      "sb_chat_", "sb_pick_", "sb_vq_", "sb_vcmp_",
                      # reflective questions and the answers to them
                      "sb_rqb_", "sb_rqa_", "sb_rab_", "sb_raa_", "sb_rap_", "sb_rai_",
                      )


def save_snapshot(rid: str, state: dict) -> None:
    """Upsert the latest JSON-serializable session state for resume-later."""
    if not rid:
        return
    clean = {}
    for k, v in state.items():
        if not isinstance(k, str):
            continue
        if k not in _SNAPSHOT_KEYS and not k.startswith(_SNAPSHOT_PREFIXES):
            continue
        try:
            json.dumps(v)
            clean[k] = v
        except (TypeError, ValueError):
            continue
    try:
        with _conn() as c:
            c.execute("INSERT INTO snapshots (respondent_id, ts, state) "
                      "VALUES (?,?,?) ON CONFLICT(respondent_id) "
                      "DO UPDATE SET ts=excluded.ts, state=excluded.state",
                      (rid, _now(), json.dumps(clean, ensure_ascii=False)))
    except sqlite3.Error:
        pass


def load_snapshot(rid: str) -> dict:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT state FROM snapshots WHERE respondent_id = ?",
                        (rid,)).fetchone()
    if not row:
        return {}
    try:
        return json.loads(row["state"])
    except (ValueError, TypeError):
        return {}


def mark_submitted(rid: str) -> None:
    with _conn() as c:
        c.execute("UPDATE respondents SET submitted_at = ? WHERE id = ?",
                  (_now(), rid))


def set_email(rid: str, email: str) -> None:
    with _conn() as c:
        c.execute("UPDATE respondents SET email = ? WHERE id = ?", (email, rid))
