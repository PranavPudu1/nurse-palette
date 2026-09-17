"""The poster one-click path reaches the workspace with no access code."""
import os, sys, pathlib, tempfile, warnings
warnings.filterwarnings("ignore")
APP = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, APP)
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="poster_")
from streamlit.testing.v1 import AppTest
import llm, conditions, prompts as P
llm.is_configured = lambda: False


def click(at, label):
    for b in at.button:
        if b.label == label:
            b.click().run(); return True
    return False


at = AppTest.from_file(APP + "/app.py", default_timeout=300)
at.run()
assert click(at, "Capstone Poster"), [b.label for b in at.button]
assert not at.exception, at.exception
ss = at.session_state
assert ss["sb_condition"] == conditions.DEFAULT_ARM, ss["sb_condition"]
assert ss["resp_test"] is True, "poster sessions must be flagged is_test"
click(at, "Continue")
at.selectbox(key="sb_age_input").set_value("9-12").run()
click(at, "Next: two quick questions")
for _w in [w for w in at.text_area if w.key and w.key.startswith("w_sb_rai_")]:
    at.text_area(key=_w.key).set_value("I want her told, gently.").run()
click(at, "Continue")
assert not at.exception, at.exception
assert ss["sb_step_key"] == "themes", ss["sb_step_key"]
body = " ".join(str(getattr(m, "value", "")) for m in at.markdown)
missing = [t["name"] for t in P.KIDS_THEMES if t["name"] not in body]
assert not missing, f"themes missing from the menu: {missing}"
assert click(at, "Write a rule for this"), "cannot open a theme"
assert not at.exception, at.exception
print(f"POSTER PATH PASSED: one click -> menu ({len(P.KIDS_THEMES)} themes) "
      f"-> workspace, arm {ss['sb_condition']}")
