"""The two-level testing loop: three rounds per theme, then three at the end."""
import os, sys, pathlib, tempfile, warnings
warnings.filterwarnings("ignore")
APP = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, APP)
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="two_")
from streamlit.testing.v1 import AppTest
import llm, prompts as P, wizard, steps as S
llm.is_configured = lambda: False

def click(at, label):
    for b in at.button:
        if b.label == label:
            b.click().run(); return True
    return False

def md(at):
    return " ".join([str(getattr(m, "value", "")) for m in at.markdown] +
                    [str(getattr(c, "value", "")) for c in at.caption])

at = AppTest.from_file(APP + "/app.py", default_timeout=300)
at.run()
at.text_input(key="gate_code").set_value("TEST").run(); click(at, "Enter")
at.text_input(key="gate_name").set_value("T").run(); click(at, "Begin")
click(at, "Continue")
at.text_input(key="sb_audience_input").set_value("my child, age 10").run()
click(at, "Continue")
ss = at.session_state
DRAFT = "Summarize it calmly for my 10-year-old and never repeat graphic detail."
ANS = "She is only ten and gets frightened easily."

def answer_all(idx, slot):
    """Fill every question box on screen for a slot.

    Matched by widget key prefix rather than by calling into steps.py: the app's
    helpers read st.session_state, which outside the script run is not the
    AppTest session.
    """
    pre = (f"w_sb_rap_{idx}", f"w_sb_ra{slot}_{idx}_")
    keys = [w.key for w in at.text_area
            if w.key and w.key.startswith(pre)]
    for k in keys:
        at.text_area(key=k).set_value(ANS).run()
    return keys

for n in range(wizard.N_THEMES):
    assert click(at, "Write a rule for this"), f"open theme {n+1}"
    # Layout B keeps every control on screen at once, so this test can be about
    # the testing loop rather than about stage navigation. test_layouts.py is
    # where the four layouts are compared.
    at.radio(key="sb_layout").set_value("B").run()
    theme, idx = ss["sb_theme"], ss["sb_idx"]
    # the save button must be blocked until every question is answered
    save = [b for b in at.button if b.label == "Save this rule and test it"][0]
    assert save.disabled, "save was enabled with questions unanswered"
    at.text_area(key=f"w_sb_answer_{idx}").set_value(DRAFT).run()
    save = [b for b in at.button if b.label == "Save this rule and test it"][0]
    assert save.disabled, "save enabled with a rule but no answers"
    filled = answer_all(idx, "b")
    assert filled, "no question boxes on screen"
    save = [b for b in at.button if b.label == "Save this rule and test it"][0]
    assert not save.disabled, "save still blocked after answering everything"
    assert click(at, "Save this rule and test it"), "save blocked after answering"
    assert not at.exception, at.exception
    assert ss["sb_tphase"] == "test" and ss["sb_tround"] == 1

    for rnd in (1, 2, 3):
        if ss["sb_tround"] != rnd:
            assert click(at, f"Start round {rnd}"), f"start theme round {rnd}"
        assert not at.exception, at.exception
        cmps = ss["sb_cmp"][f"{theme}:{rnd}"]
        for _ in range(len(cmps)):
            j = ss["sb_tcidx"]
            body = md(at)
            assert "Your rule chose" not in body, f"leak before pick r{rnd}"
            before = ss["sb_tcidx"]
            assert click(at, "Prefer left"), f"pick r{rnd}"
            assert ss["sb_tcidx"] == before, "pick auto-advanced"
            at.text_input(key=f"sb_cnote_{rnd}_{j}").set_value("gentler").run()
            assert click(at, "Continue"), f"continue r{rnd}"
            if rnd == 1:
                assert ss["sb_tcidx"] == before + 1, "round 1 should advance"
            else:
                assert "Your rule" in md(at), f"no reveal r{rnd}"
                if rnd == 2:
                    assert any(w.key == f"w_sb_answer_{idx}" for w in at.text_area), \
                        "round 2 must hand the rule box back"
                    assert click(at, "Save and continue"), "r2 close"
                else:
                    assert not any(b.label == "Save and continue" for b in at.button), \
                        "round 3 must not offer a rule edit"
                    assert click(at, "Next"), "r3 close"
                assert ss["sb_tcidx"] == before + 1
    assert click(at, "Back to the themes"), "return to menu"
    scored = [r for r in ss["sb_confirm"]
              if r.get("theme") == theme and r["round"] == 3]
    assert len(scored) == S.N_THEME_ROUND, scored
    assert all(r.get("model_choice") and "agreed" in r for r in scored)
    print(f"  theme {n+1}: {theme} -> 3 rounds x {S.N_THEME_ROUND}, "
          f"scored {sum(1 for r in scored if r['agreed'])}/{len(scored)}")

theme_picks = [r for r in ss["sb_confirm"] if r.get("level") == "theme"]
assert len(theme_picks) == wizard.N_THEMES * 3 * S.N_THEME_ROUND, len(theme_picks)
assert all(r["theme"] for r in theme_picks), "picks lost their theme"
print(f"theme loops: {len(theme_picks)} picks, all carrying a theme")

assert click(at, "Continue"), "leave the themes step"
assert ss["sb_step_key"] == "confirm", ss["sb_step_key"]
for rnd in (1, 2, 3):
    if ss["sb_round"] != rnd:
        assert click(at, f"Start round {rnd}"), f"start final round {rnd}"
    assert not at.exception, at.exception
    n = len(ss["sb_cmp"][str(rnd)])
    for _ in range(n):
        j = ss["sb_cidx"]
        assert "the agent chose this" not in md(at), f"leak final r{rnd}"
        click(at, "Prefer left")
        at.text_input(key=f"sb_cnote_{rnd}_{j}").set_value("instinct").run()
        click(at, "Continue")
        if rnd == 1:
            continue
        assert "the agent chose this" in md(at), f"no reveal final r{rnd}"
        if rnd == 2:
            at.text_area(key=f"sb_crit_{rnd}_{j}").set_value("").run()
            click(at, "Apply and continue")
        else:
            click(at, "Next")
    print(f"  final round {rnd}: {n} comparisons")

assert ss["sb_policy"], "no policy was written"
final = [r for r in ss["sb_confirm"] if r.get("level") == "final" and r["round"] == 3]
assert len(final) == S.N_ROUND3, len(final)
print(f"policy v{ss['sb_policy']['version']}, "
      f"final agreement {sum(1 for r in final if r['agreed'])}/{len(final)}")
print(f"TOTAL comparisons: {len(ss['sb_confirm'])}")
print("\nTWO-LEVEL PASSED")
