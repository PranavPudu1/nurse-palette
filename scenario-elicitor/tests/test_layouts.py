"""The staged split workspace completes a theme; the stages gate correctly."""
import os, sys, pathlib, tempfile, warnings
warnings.filterwarnings("ignore")
APP = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, APP)
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="lay_")
from streamlit.testing.v1 import AppTest
import llm, steps as S
llm.is_configured = lambda: False

DRAFT = "Summarize it calmly for my 10-year-old and never repeat graphic detail."
ANS = "She is only ten and gets frightened easily."
FAILS = []


def sget(ss, key, default=None):
    return ss[key] if key in ss else default


def check(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c:
        FAILS.append(m)


def click(at, label):
    for b in at.button:
        if b.label == label:
            b.click().run(); return True
    return False


def next_stage(at):
    """Click Next and report whether the stage actually advanced. The button
    is always tappable now (gating happens in the click handler), so blocked
    means the click left the stage where it was."""
    ss = at.session_state
    idx = ss["sb_idx"] if "sb_idx" in ss else 0
    skey = f"sb_stage_{idx}"
    before = ss[skey] if skey in ss else 0
    for b in at.button:
        if b.label.startswith("Next:"):
            b.click().run()
            after = at.session_state[skey] if skey in at.session_state else 0
            return "moved" if after > before else "blocked"
    return "none"


print("=== the staged workspace completes a theme ===")
at = AppTest.from_file(APP + "/app.py", default_timeout=300)
at.run()
at.text_input(key="gate_code").set_value("TEST").run(); click(at, "Enter")
at.text_input(key="gate_name").set_value("L").run(); click(at, "Begin")
click(at, "Continue")
at.selectbox(key="sb_age_input").set_value("9-12").run()
for w in [w for w in at.text_area if w.key and w.key.startswith("w_sb_rai_")]:
    at.text_area(key=w.key).set_value("Gently.").run()
click(at, "Continue")
ss = at.session_state
click(at, "Write a rule for this")
check(not any(r.key == "sb_layout" for r in at.radio),
      "no layout switcher anywhere (split is the only layout)")
idx = ss["sb_idx"]

# Stage 0: Consider + write. Rule box present on the SAME stage as questions.
check(any(w.key == f"w_sb_answer_{idx}" for w in at.text_area),
      "stage 0 has the rule box below the questions")
check(next_stage(at) == "blocked", "Next blocked with questions unanswered")
for w in [w for w in at.text_area
          if w.key and w.key.startswith((f"w_sb_rap_{idx}", f"w_sb_rab_{idx}_"))]:
    at.text_area(key=w.key).set_value(ANS).run()
check(next_stage(at) == "blocked", "Next still blocked with no rule written")
at.text_area(key=f"w_sb_answer_{idx}").set_value(DRAFT).run()
check(next_stage(at) == "moved", "Next opens once questions + first draft exist")
check((ss[f"sb_first_{idx}"] or "").strip() == DRAFT,
      "leaving Consider captured the first draft")
check(sget(ss, f"sb_vers_{idx}") == [DRAFT], "the first draft was saved as v1")
check(any(w.key == f"w_sb_vsel_{idx}" for w in at.selectbox),
      "the version dropdown is on the Score + revise box")

# Stage 1: Score + revise. Rubric + reflections accordion.
labels = [e.label for e in at.get("expander")]
check(any("reflections" in (l or "").lower() for l in labels),
      "stage 1 shows the reflections accordion")
check(any("rubric" in (l or "").lower() for l in labels),
      "the rubric is viewable on the score stage")
click(at, "Check my answer")
check(not at.exception, f"check ran ({at.exception})")

# Still on Score + revise: edit the rule and save it as a new version.
at.text_area(key=f"w_sb_answer_{idx}").set_value(DRAFT + " Ask me on close calls.").run()
click(at, "Save as new version")
check(len(sget(ss, f"sb_vers_{idx}") or []) == 2, "the edit saved as v2")
check(sget(ss, f"sb_vsel_{idx}") == "v2", "the dropdown selected v2")
check(next_stage(at) == "moved", "onward to Sharpen")

# Stage 2: Sharpen. Rule card, questions, then the editable box; never blocks.
check(any(w.key == f"w_sb_answer_{idx}" for w in at.text_area),
      "Sharpen keeps the rule box on screen")
check("The rule you wrote" in " ".join(str(getattr(m, "value", ""))
                                       for m in at.markdown),
      "Sharpen shows the written rule read-only above the questions")
_qs_before = sget(ss, f"sb_rqa_{idx}")
click(at, "New questions from my current rule")
check(not at.exception, f"regenerate ran ({at.exception})")
check(bool(sget(ss, f"sb_rqa_{idx}")), "regenerate produced questions")
check(next_stage(at) == "moved", "Sharpen never blocks")

# Stage 3: Test. Final dropdown + three compare columns.
check(any(w.key == f"w_sb_final_{idx}" for w in at.selectbox),
      "the final-version picker is on the test stage")
check(sget(ss, f"sb_final_{idx}") == "v2", "final defaults to the newest version")
cols = [w for w in at.selectbox if w.key and w.key.startswith(f"w_sb_cmpv_{idx}_")]
check(len(cols) == 3, f"three compare columns ({len(cols)})")
at.selectbox(key=f"w_sb_cmpv_{idx}_0").select("v1").run()
click(at, "Ask the case's question")
check(not at.exception, f"asked v1 the case question ({at.exception})")
turns = (sget(ss, f"sb_chats_{idx}") or {}).get("v1", {}).get("turns", [])
check(len(turns) >= 2 and turns[-1].get("version") == "v1",
      "the reply landed in v1's own thread, stamped v1")
at.selectbox(key=f"w_sb_cmpv_{idx}_1").select("Original").run()
oturns = (sget(ss, f"sb_chats_{idx}") or {}).get("Original", {}).get("turns", [])
check(len(oturns) >= 1, "Original seeds its baseline thread without a call")
at.selectbox(key=f"w_sb_cmpv_{idx}_0").select("v2").run()
turns = (sget(ss, f"sb_chats_{idx}") or {}).get("v1", {}).get("turns", [])
check(len(turns) >= 2, "v1's thread persisted after switching the column away")
save = [b for b in at.button if b.label == "Save this rule and test it"]
check(bool(save) and not save[0].disabled,
      "save enabled once a final version is marked (defaults to newest)")
click(at, "Save this rule and test it")
check(ss["sb_tphase"] == "test", "saving leads into the theme rounds")
ans = ss["sb_answers"][0]
check(ans["ideal_behavior"] == DRAFT + " Ask me on close calls.",
      "the marked version (v2) is what saved")
check(ans["rule_versions"] == [{"label": "v1", "rule": DRAFT},
                               {"label": "v2",
                                "rule": DRAFT + " Ask me on close calls."}],
      "the export carries the version trajectory")
check(ans.get("final_version", "") != "", "the final version label was recorded")
check(len(ans["reflection"]) >= 1, "reflections captured")

print("=== resume returns to the same stage ===")
code = ss["resp_code"]
at2 = AppTest.from_file(APP + "/app.py", default_timeout=300)
at2.run()
at2.text_input(key="gate_code").set_value("TEST").run(); click(at2, "Enter")
at2.text_input(key="gate_resume").set_value(code).run(); click(at2, "Resume")
check(not at2.exception, f"resume raised nothing ({at2.exception})")
check(at2.session_state[f"sb_stage_{idx}"] == 3, "stage survived the resume")

print()
if FAILS:
    print(f"!!! {len(FAILS)} FAILURES"); [print("   -", f) for f in FAILS]
    sys.exit(1)
print("WORKSPACE TESTS PASSED")
