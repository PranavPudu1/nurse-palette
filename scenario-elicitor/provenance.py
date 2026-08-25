"""Where every AI-generated thing on screen comes from.

One entry per artifact the model produces, rendered as a small info icon next to
it. Three parts, deliberately in this order:

    what    one plain line, for a participant who just wants to know
    source  why it works this way, in plain words, with the paper named at the
            end rather than at the start
    prompt  a condensed version of the real instruction in prompts.py

The rule for `source` is that a reader learns the idea whether or not they ever
look the citation up. "It comes from Botender" explains nothing to someone who
has not read Botender; "we throw away situations your earlier answers already
settle, because they teach us nothing (Source: Botender 2026)" explains itself
and stays traceable. A participant should be able to repeat any of these to
someone who has never heard of the papers.

The prompt field is a summary, not the live string, so it can drift. The tests
guard the parts that matter: every key is rendered somewhere, every field is
non-empty, the condensed prompt is genuinely shorter than the real one, and no
field leans on jargon or opens with a citation.

The full record lives in docs/grounding.md; this is the in-product version of it.
"""
from __future__ import annotations

import html

INFO: dict[str, dict[str, str]] = {
    "case": {
        "what": "A specific situation your child's AI could really run into.",
        "source": "We write these before you have said anything, so they are not "
                  "just echoing you back. The kind of problem they belong to "
                  "comes from a study that interviewed 24 parents about what "
                  "worried them when children use AI chatbots. We also throw "
                  "away any "
                  "situation your earlier answers would already settle: if you "
                  "would obviously answer it the same way, it teaches us nothing. "
                  "(Sources: Driscoll and colleagues 2026 for the topics, "
                  "Botender 2026 for the throw-away rule.)",
        "prompt": "Write realistic situations where reasonable parents could "
                  "genuinely disagree about what the AI should do. Skip anything "
                  "the person's stated wishes already settle.",
    },
    "probe": {
        "what": "A what-if question, to make you test your own answer before you "
                "commit to it.",
        "source": "In interviews, a good researcher does not just take your first "
                  "answer. They ask a follow-up that changes one detail, to see "
                  "whether your reasoning holds. This is that move, written down "
                  "in advance. Because it is written ahead of time it cannot "
                  "react to you the way a real interviewer would. (Source: the "
                  "interview method used by Driscoll and colleagues 2026.)",
        "prompt": "Ask one short what-if question about this situation: a "
                  "different age, a more serious version, or a less clear reason "
                  "for asking.",
    },
    "reflect_before": {
        "what": "Questions about what you are assuming, before you have written "
                "anything.",
        "source": "There is a long-standing set of five question types designed "
                  "to make someone examine their own thinking rather than defend "
                  "it: what do you mean by that, what are you assuming, how do "
                  "you know, what follows if you are right, and who might see it "
                  "differently. These questions are built from that set. They "
                  "have no right answer and you can skip them. (Source: the Paul "
                  "and Elder question types, catalogued by Ang and colleagues "
                  "2023.)",
        "prompt": "Ask what this person is taking for granted about this "
                  "situation before they answer, and whose view they might be "
                  "missing.",
    },
    "reflect_after": {
        "what": "Questions about the reasoning in what you just wrote.",
        "source": "The same five question types, now pointed at your actual "
                  "words. These are deliberately separate from the score below "
                  "them: the score asks whether your rule is clear enough for an "
                  "AI to follow, while these ask why you want what you wrote. "
                  "Both matter, and they are different questions.",
        "prompt": "Ask about their own wording, quoting the phrase each question "
                  "is about. Do not judge the answer or suggest a rewrite.",
    },
    "baseline_reply": {
        "what": "What the AI says today, before you have told it anything.",
        "source": "This is the starting point, so you can see what actually "
                  "changes once you write a rule. It is not a bare, unguarded "
                  "model: it already behaves the way these products behave for "
                  "children out of the box, which means age-appropriate wording, "
                  "pointing to a trusted adult on serious topics, no graphic "
                  "detail, and a crisis resource if self-harm comes up. We "
                  "rebuilt those defaults from behaviour the companies describe "
                  "publicly; we do not have anyone's real instructions. It is "
                  "deliberately not made more cautious just because a parent is "
                  "watching, and its length is not capped, because a real "
                  "product does not answer in three tidy sentences.",
        "prompt": "Reply the way the product would out of the box, at the length "
                  "a real assistant would use. Apply the ordinary child-mode "
                  "defaults and nothing stricter.",
    },
    "rule_reply": {
        "what": "The same moment answered again, this time following your rule.",
        "source": "Your rule is handed to the AI as its instructions, and it "
                  "answers the same question again so you can compare. Writing a "
                  "rule and immediately seeing what it does is the fastest way to "
                  "find out whether it says what you meant. (Source: PolicyPad "
                  "2026, a tool where experts draft rules for AI and test them "
                  "the same way.)",
        "prompt": "Start from the same out-of-the-box behaviour, then follow the "
                  "parent's instructions on top of it. Where the two disagree, "
                  "the parent wins.",
    },
    "rubric": {
        "what": "A score for your rule on four things, and what would move each "
                "one up.",
        "source": "This is not marking you. It checks one narrow thing: is your "
                  "rule specific enough that an AI could actually follow it. A "
                  "rule can be completely right about what you want and still be "
                  "too vague to act on. The four things it looks at, and the "
                  "levels within each, come from what parents themselves said "
                  "mattered. (Sources: the scoring approach from iRULER 2026, the "
                  "four things from Driscoll and colleagues 2026.)",
        "prompt": "Match the draft against each level description and pick the "
                  "closest fit. Judge only what is written, do not rewrite it, "
                  "and say what the next level up would need.",
    },
    "theme": {
        "what": "One kind of thing that can go wrong, and the cases that show it.",
        "source": "Researchers showed 24 parents real conversations between "
                  "children and AI chatbots and asked what worried them and why. "
                  "They sorted the answers into eight kinds, five about what the "
                  "AI said back and three about what the child had asked in the "
                  "first place. The count on each card is how many of those 24 "
                  "parents raised it, and the wording is taken from what they "
                  "actually said, so none of this is our guess about what "
                  "parents care about. Once you pick one, the cases underneath "
                  "it are written fresh for that kind of problem. (Source: "
                  "Driscoll and colleagues 2026, their Table 3.)",
        "prompt": "Write cases that belong to this one kind of problem, pushing "
                  "into its less obvious corners rather than the obvious version.",
    },
    "comparison": {
        "what": "One moment, and two things the AI could say back, differing in "
                "exactly one way.",
        "source": "Only one thing changes between the two replies, so whichever "
                  "you pick tells us something specific rather than just which "
                  "one sounded nicer. What changes is one of four things parents' "
                  "answers were found to turn on: your child's age, how serious "
                  "it is, how clear their reason for asking is, and where the "
                  "risk is coming from. (Source: Driscoll and colleagues 2026.)",
        "prompt": "Pick the one thing this person's rule is most likely to flip "
                  "on. Write two replies that differ only in that, neither "
                  "obviously better.",
    },
    "policy": {
        "what": "One set of instructions, written from everything you have said "
                "so far, then sharpened as you correct it.",
        "source": "It is built from the rules you wrote for each situation plus "
                  "the choices you made between replies, and every line should "
                  "trace back to something you actually wrote or picked. It is "
                  "never rewritten from scratch; it only gets sharper. The "
                  "underlying idea is that if a set of written instructions "
                  "really captures what you want, an AI following only those "
                  "instructions should make the same choices you did. (Source: "
                  "Inverse Constitutional AI 2025.)",
        "prompt": "Write instructions that capture what THIS person wants. Every "
                  "line must trace to something they wrote or chose. Where their "
                  "choices and their written rules disagree, follow the choices.",
    },
    "model_pick": {
        "what": "Which reply your instructions chose, and which line decided it.",
        "source": "The AI reads only your instructions, not your mind, and picks "
                  "the reply that best follows them. Where it agrees with you, "
                  "your instructions captured what you wanted. Where it does not, "
                  "something is missing from them, and that gap is the useful "
                  "part. This is hidden until after you have picked, so what you "
                  "choose stays your own view rather than a reaction to the AI.",
        "prompt": "Choose which reply better follows the instructions. Judge only "
                  "by the instructions, not by your own view of what is best. Say "
                  "which line decided it.",
    },
}


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def icon(key: str) -> str:
    """Inline HTML for the info icon. Returns "" for an unknown key.

    Opens on hover (desktop), on press (touch, via :active) and on focus (tab
    and most touch browsers). No JavaScript, because Streamlit renders this
    through its markdown pipeline where scripts do not run.
    """
    e = INFO.get(key)
    if not e:
        return ""
    return (
        f'<span class="np-info" tabindex="0" role="button" '
        f'aria-label="How this was made">i'
        f'<span class="np-tip">'
        f'<b>How this was made</b>{_esc(e["what"])}'
        f'<b>Where it comes from</b>{_esc(e["source"])}'
        f'<b>The prompt, condensed</b>'
        f'<i>{_esc(e["prompt"])}</i>'
        f'</span></span>')


def keys() -> list[str]:
    return sorted(INFO)
