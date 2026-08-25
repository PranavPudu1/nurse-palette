"""Every layout completes a theme, and produces the same state."""
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


def check(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c:
        FAILS.append(m)


def click(at, label):
    for b in at.button:
        if b.label == label:
            b.click().run(); return True
    return False


def run_theme(layout):
    at = AppTest.from_file(APP + "/app.py", default_timeout=300)
    at.run()
    at.text_input(key="gate_code").set_value("TEST").run(); click(at, "Enter")
    at.text_input(key="gate_name").set_value("L").run(); click(at, "Begin")
    click(at, "Continue")
    at.text_input(key="sb_audience_input").set_value("my child, age 10").run()
    click(at, "Continue")
    ss = at.session_state
    click(at, "Write a rule for this")
    # the switcher only exists for test sessions, and this is one
    assert any(r.key == "sb_layout" for r in at.radio), "no layout switcher"
    at.radio(key="sb_layout").set_value(layout).run()
    assert not at.exception, f"{layout}: {at.exception}"
    idx = ss["sb_idx"]

    # walk whatever stages this layout has, answering and writing as they appear
    for _ in range(6):
        for w in list(at.text_area):
            if w.key and w.key.startswith((f"w_sb_rap_{idx}", f"w_sb_rab_{idx}_")):
                if not (str(w.value or "")).strip():
                    at.text_area(key=w.key).set_value(ANS).run()
        if any(w.key == f"w_sb_answer_{idx}" for w in at.text_area):
            if not (str(at.text_area(key=f"w_sb_answer_{idx}").value or "")).strip():
                at.text_area(key=f"w_sb_answer_{idx}").set_value(DRAFT).run()
        if any(b.label == "Save this rule and test it" and not b.disabled
               for b in at.button):
            break
        moved = False
        for b in at.button:
            if b.label.startswith("Next:"):
                if not b.disabled:
                    b.click().run(); moved = True
                break
        if not moved and not any(b.label.startswith("Next:") for b in at.button):
            break
    assert not at.exception, f"{layout}: {at.exception}"
    ok = click(at, "Save this rule and test it")
    return at, ss, idx, ok


print("=== each layout completes a theme ===")
results = {}
for layout in ("A", "B", "C", "D"):
    at, ss, idx, ok = run_theme(layout)
    check(ok, f"{layout}: saved the rule")
    check(not at.exception, f"{layout}: no exception ({at.exception})")
    check(ss["sb_tphase"] == "test", f"{layout}: reached the testing loop")
    ans = [a for a in ss["sb_answers"]][0]
    results[layout] = {"rule": ans["ideal_behavior"], "theme": ans["theme"],
                       "n_reflect": len(ans["reflection"])}
    check(ans["ideal_behavior"] == DRAFT, f"{layout}: the rule saved verbatim")
    check(len(ans["reflection"]) >= 1, f"{layout}: reflection captured "
                                       f"({len(ans['reflection'])})")

print("=== all four produce the same state ===")
base = results["A"]
for layout in ("B", "C", "D"):
    check(results[layout] == base,
          f"{layout} matches A ({results[layout]} vs {base})")

print("=== the switcher is hidden from a real participant ===")
at = AppTest.from_file(APP + "/app.py", default_timeout=300)
at.run()
at.text_input(key="gate_code").set_value(os.environ.get("ACCESS_CODE", "HAILAB25")).run()
click(at, "Enter")
at.text_input(key="gate_name").set_value("Real").run(); click(at, "Begin")
click(at, "Continue")
at.text_input(key="sb_audience_input").set_value("my child, age 10").run()
click(at, "Continue")
click(at, "Write a rule for this")
check(at.session_state["resp_test"] is False, "this is a non-test session")
check(not any(r.key == "sb_layout" for r in at.radio),
      "no layout switcher for a real participant")

print()
if FAILS:
    print(f"!!! {len(FAILS)} FAILURES"); [print("   -", f) for f in FAILS]
    sys.exit(1)
print("LAYOUT TESTS PASSED")
