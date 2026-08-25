"""Checks that need no app run: the registry, the themes, the removed features.

These are the guards that stop old copy and dead features creeping back in.
"""
import pathlib, re, sys

APP = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path.insert(0, APP)
import prompts as P, provenance as PR, theme  # noqa: E402

FAILS = []


def check(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c:
        FAILS.append(m)


src = {f: (pathlib.Path(APP) / f).read_text()
       for f in ("steps.py", "llm.py", "prompts.py", "store.py", "export.py",
                 "provenance.py", "README.md",
                 "docs/provenance.md", "docs/design-rationale.md")}

print("=== removed features stay removed ===")
for f, s in src.items():
    for token in ("suggest_revision", "REVISION_SCHEMA", "sb_sugg_", "used_sugg",
                  "_weakest_criterion", "Surface more", "Added by you"):
        check(token not in s, f"{f}: no {token}")
check("revision" not in PR.INFO, "provenance has no revision entry")

print("=== the case card gives nothing away ===")
sys.path.insert(0, APP)
import steps as S  # noqa: E402
FULL = {"id": 0, "title": "T", "situation": "SITUATION-HERE", "kind": "common",
        "at_stake": "ZZ-AT-STAKE", "considerations": ["ZZ-WEIGH"],
        "analysis": "ZZ-ANALYSIS", "affects": "ZZ-AFFECTS"}
html = S._situation_card(FULL)
check("SITUATION-HERE" in html, "the card shows what happens")
for marker in ("ZZ-AT-STAKE", "ZZ-WEIGH", "ZZ-ANALYSIS", "ZZ-AFFECTS"):
    check(marker not in html, f"the card does not render {marker}")
m = P.reflect_before_messages("A", "d", "aud", {"situation": "s",
                                                "at_stake": "ZZSTAKE",
                                                "considerations": ["ZZWEIGH"]})
check("ZZSTAKE" in m[1]["content"] and "ZZWEIGH" in m[1]["content"],
      "both reach the question generator instead")

print("=== questions cannot put words in their mouth ===")
sys_p = m[0]["content"]
check("HARD RULE" in sys_p, "the belief-attribution ban is in the prompt")
for banned in ("why do you assume", "what makes you think"):
    check(banned in sys_p.lower(), f"names {banned!r} as forbidden")

print("=== the baseline is a product default, uncapped ===")
base = P.agent_reply_messages("A", "d", "aud", {"situation": "s"}, None, [])[0]
check("two to four sentences" not in base["content"], "no length cap")
check("child-appropriate mode" in base["content"], "child-safe layer applied")
check("crisis resource" in base["content"], "including self-harm handling")
reply_spec = P._CASE_FIELDS[P._CASE_FIELDS.index("'ai_response'"):]
check("two to four sentences" not in reply_spec, "generated replies uncapped too")
check("two to four sentences" in P._CASE_FIELDS,
      "the situation synopsis keeps its cap, which is correct")

print("=== the themes match Driscoll Table 3 ===")
PAPER = {"Missing Underlying Meaning": 13, "Wrong Approach to Delivery": 10,
         "Developmental Mismatch": 8, "Emotional Impact": 7,
         "Exposure to Unsafe Ideas": 5, "Potentially Harmful Intention": 20,
         "Overdependence": 5, "Skepticism of Technical Safeguards": 5}
check(len(P.KIDS_THEMES) == 8, f"eight themes ({len(P.KIDS_THEMES)})")
check({t["name"] for t in P.KIDS_THEMES} == set(PAPER), "names match the paper")
for t in P.KIDS_THEMES:
    check(t["raised_by"] == PAPER[t["name"]], f"{t['name']}: parent count")
    check(len(t["blurb"]) > 90, f"{t['name']}: the description explains something")
    title_words = {w.lower() for w in t["name"].split() if len(w) > 4}
    check(not title_words <= {w.lower().strip(".,") for w in t["blurb"].split()},
          f"{t['name']}: does not merely restate its title")

print("=== the provenance registry ===")
# Keys used directly. The rest arrive as the info_key argument of
# _render_one_question, which is passed a literal for the probe and a slot-
# dependent value for the two reflection sets, so those are named explicitly
# rather than scraped: a regex over a multi-line call also matches unrelated
# string literals inside it.
literal = set(re.findall(r'provenance\.icon\("([a-z_]+)"\)', src["steps.py"]))
indirect = {"probe", "reflect_before", "reflect_after", "baseline_reply",
            "rule_reply"}
check(not (literal - set(PR.keys())),
      f"no icon references a missing key ({sorted(literal - set(PR.keys()))})")
check(not (set(PR.keys()) - literal - indirect),
      f"every key is rendered ({sorted(set(PR.keys()) - literal - indirect)})")
for k in ("probe", "reflect_before", "reflect_after"):
    check(f'"{k}"' in src["steps.py"], f"{k} is passed as an info key")
for k, e in PR.INFO.items():
    check(all(e.get(f, "").strip() for f in ("what", "source", "prompt")),
          f"{k}: all three fields present")

JARGON = ["CHI '", "ICLR", "EACL", "et al.", "§", "taxonomy", "Socratic",
          "reconstruct", "annotat", "constitution", "rubric-based", "provocation",
          "elicitation", "operationaliz", "instantiat"]
hits = [(k, j) for k, e in PR.INFO.items() for j in JARGON
        for f in ("what", "source", "prompt")
        if j.lower() in re.sub(r"\(Sources?:.*?\)", "", e[f], flags=re.S).lower()]
check(not hits, f"no unexplained jargon in the prose ({hits[:3]})")
early = [k for k, e in PR.INFO.items()
         if "(Source" in e["source"] and e["source"].index("(Source") < 120]
check(not early, f"the idea is explained before any paper is named ({early})")

print("=== the tooltip cannot be clipped ===")
rule = re.search(r"([^{}]*)\{\s*overflow:\s*visible\s*!important;\s*\}",
                 theme.GLOBAL_CSS)
check(rule is not None, "columns are told not to clip")
sel = (rule.group(1).split("*/")[-1] if rule else "")
check("stHorizontalBlock" in sel and "olumn" in sel, "the rule targets columns")
check("stVerticalBlock" not in sel, "and spares the scrolling containers")

print("=== the docs describe the tool as it is ===")
# A doc that documents a feature we removed is worse than no doc: it is what
# Min would be reading when she asks why she cannot find the button.
for doc in ("docs/provenance.md", "docs/design-rationale.md"):
    d = src[doc]
    check("| Decision | Where you see it | Why | Source |" in d or "## " in d,
          f"{doc}: has the expected shape")
    for gone in ("Missing the real meaning", "Risky delivery",
                 "Harmful intention", "seven themes", "Surface more"):
        check(gone not in d, f"{doc}: no stale reference to {gone!r}")
check("Where you see it" in src["docs/provenance.md"],
      "provenance.md uses the four-field form")

print("=== answers survive a widget unmounting ===")
check("_kept_text" in src["steps.py"], "the persistence helper exists")
check('st.text_input("Your thoughts' not in src["steps.py"],
      "answers are not collected in a single-line input")

print()
if FAILS:
    print(f"!!! {len(FAILS)} FAILURES"); [print("   -", f) for f in FAILS]
    sys.exit(1)
print("STATIC TESTS PASSED")
