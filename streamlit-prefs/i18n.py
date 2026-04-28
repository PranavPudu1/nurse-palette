"""Lightweight English / Korean translations.

Use ``t("key")`` after :func:`set_lang` has been called once. Falls back to
English if a key is missing.
"""
from __future__ import annotations
import streamlit as st

LANGUAGES = {"en": "English", "ko": "한국어"}
DEFAULT = "en"

# Each entry: key -> {"en": ..., "ko": ...}
_T: dict[str, dict[str, str]] = {
    # === App / sidebar ===
    "app.title":        {"en": "Nurse preferences",
                         "ko": "간호사 선호도"},
    "app.subtitle":     {"en": "Help us learn what makes a great schedule for you.",
                         "ko": "당신에게 좋은 근무표를 함께 만들어 봅시다."},
    "app.your_name":    {"en": "Your name", "ko": "이름"},
    "app.language":     {"en": "Language", "ko": "언어"},

    # === Tabs ===
    "tab.welcome":    {"en": "Welcome",         "ko": "시작하기"},
    "tab.background": {"en": "1 · Background",  "ko": "1 · 사전 질문"},
    "tab.compare":    {"en": "2 · Compare",     "ko": "2 · 비교"},
    "tab.rank":       {"en": "3 · Rank",        "ko": "3 · 순위"},
    "tab.ideal":      {"en": "4 · Ideal",       "ko": "4 · 이상적인 일정"},
    "tab.tradeoffs":  {"en": "5 · Trade-offs",  "ko": "5 · 절충점"},
    "tab.day_prefs":  {"en": "6 · Day prefs",   "ko": "6 · 요일별 선호도"},

    # === Shifts ===
    "shift.D": {"en": "Day",     "ko": "주간"},
    "shift.E": {"en": "Evening", "ko": "저녁"},
    "shift.N": {"en": "Night",   "ko": "야간"},
    "shift.X": {"en": "Off",     "ko": "휴무"},

    # === Welcome ===
    "welcome.title": {"en": "Welcome", "ko": "환영합니다"},
    "welcome.body":  {
        "en": "Five short exercises to capture what matters most when we build "
              "your schedule. Use the tabs above in any order.",
        "ko": "당신의 근무표를 만들 때 가장 중요한 것들을 다섯 가지 짧은 활동으로 "
              "확인합니다. 위쪽 탭을 원하는 순서로 진행해 주세요.",
    },
    "welcome.card.background.title": {"en": "Tell us in your own words",
                                      "ko": "본인의 이야기 들려주기"},
    "welcome.card.background.body":  {
        "en": "A few open questions about how you think about your schedule.",
        "ko": "근무에 대한 본인의 생각을 묻는 몇 가지 자유 질문입니다."},
    "welcome.card.compare.title": {"en": "Compare schedules",
                                   "ko": "근무표 비교"},
    "welcome.card.compare.body":  {
        "en": "Two example months side by side — pick the one you'd rather work.",
        "ko": "예시 근무표 두 가지 중 더 일하고 싶은 쪽을 선택합니다."},
    "welcome.card.rank.title":    {"en": "Rank what matters",
                                   "ko": "중요도 순위"},
    "welcome.card.rank.body":     {
        "en": "Order the rules by how much they affect your quality of life.",
        "ko": "규칙들이 일상에 미치는 영향에 따라 순서를 정합니다."},
    "welcome.card.ideal.title":   {"en": "Build your ideal month",
                                   "ko": "이상적인 한 달 만들기"},
    "welcome.card.ideal.body":    {
        "en": "Fill a blank calendar with shifts — show us your dream month.",
        "ko": "빈 달력에 직접 근무를 채워서 이상적인 한 달을 보여 주세요."},
    "welcome.card.tradeoffs.title": {"en": "Trade-offs",
                                     "ko": "절충점"},
    "welcome.card.tradeoffs.body":  {
        "en": "Sliders for the hard questions: how many nights for a free weekend?",
        "ko": "어려운 질문들을 슬라이더로 답해 주세요. 주말을 위해 몇 번의 야간 근무까지 받아들일 수 있나요?"},
    "welcome.card.day_prefs.title": {"en": "Day-by-day preference",
                                     "ko": "요일별 선호도"},
    "welcome.card.day_prefs.body":  {
        "en": "Rate every shift / weekday combination on a quick heatmap.",
        "ko": "요일과 근무 조합 각각에 대한 선호도를 표로 평가합니다."},
    "welcome.minutes.3": {"en": "≈ 3 min", "ko": "약 3분"},
    "welcome.minutes.2": {"en": "≈ 2 min", "ko": "약 2분"},
    "welcome.minutes.5": {"en": "≈ 5 min", "ko": "약 5분"},
    "welcome.privacy": {
        "en": "Your responses are stored locally in this session only — each tab "
              "has a download button to export your answers as JSON.",
        "ko": "응답은 현재 세션에만 저장됩니다. 각 탭의 다운로드 버튼으로 JSON 파일로 내보낼 수 있습니다."},

    # === Background (preliminary questions) ===
    "bg.title":    {"en": "Tell us in your own words",
                    "ko": "본인의 이야기를 들려 주세요"},
    "bg.subtitle": {
        "en": "A few open questions before the structured exercises. "
              "Skip anything that doesn't apply.",
        "ko": "구조화된 활동을 시작하기 전에 몇 가지 자유 질문을 드립니다. "
              "해당하지 않는 항목은 건너뛰셔도 됩니다."},
    "bg.notes_label": {"en": "Notes (optional)",
                       "ko": "메모 (선택)"},
    "bg.download": {"en": "Download my answers (JSON)",
                    "ko": "내 답변 다운로드 (JSON)"},

    # Format toggle (A vs B)
    "bg.format.label": {"en": "Question format",
                        "ko": "질문 형식"},
    "bg.format.a":     {"en": "A · Sliders & options",
                        "ko": "A · 슬라이더·선택지"},
    "bg.format.b":     {"en": "B · Rank statements (agree most → least)",
                        "ko": "B · 동의하는 순서대로 정렬"},
    "bg.format.c":     {"en": "C · Recommended mix (best per question)",
                        "ko": "C · 추천 혼합 (질문별 최적 형식)"},
    "bg.format.help":  {"en": "Try whichever feels easiest. C is our "
                              "recommended mix — each question uses the "
                              "format that fits its underlying feature.",
                        "ko": "가장 편한 형식으로 답변해 주세요. "
                              "C는 질문별로 가장 적합한 형식을 조합한 추천 형식입니다."},

    # Version C extras
    "bg.c.q5.rank_label":  {"en": "Rank shifts from hardest to easiest",
                            "ko": "근무를 힘든 순서대로 정렬"},
    "bg.c.q7.factors_label": {"en": "Which factors matter for a good day at work? (pick all that apply)",
                              "ko": "좋은 근무를 위해 중요한 요소는? (해당하는 모두 선택)"},
    "bg.c.q7.factor.coworkers": {"en": "Working with my preferred coworkers",
                                 "ko": "마음 맞는 동료와 함께 일하기"},
    "bg.c.q7.factor.charge":    {"en": "A good charge nurse / lead",
                                 "ko": "좋은 책임 간호사"},
    "bg.c.q7.factor.culture":   {"en": "Shift culture / vibe",
                                 "ko": "근무 분위기·문화"},
    "bg.c.q7.factor.handoff":   {"en": "Handoff / handover quality",
                                 "ko": "인수인계의 질"},
    "bg.c.q7.factor.breaks":    {"en": "Break culture",
                                 "ko": "휴식 문화"},
    "bg.c.q7.factor.workload":  {"en": "Fair workload distribution",
                                 "ko": "공정한 업무 분담"},
    "bg.b.howto":      {"en": "Use ▲ / ▼ to put the statement you agree with most at the top.",
                        "ko": "▲ / ▼ 버튼으로 가장 동의하는 문장을 맨 위로 옮겨 주세요."},

    # Q3 — night-shift placement (added to version A)
    "bg.q3.placement":     {"en": "Preferred placement of night shifts",
                            "ko": "야간 근무의 배치 방식"},
    "bg.q3.placement.a1":  {"en": "Spread out across the month",
                            "ko": "한 달 동안 고르게 분산"},
    "bg.q3.placement.a2":  {"en": "Clumped in one block",
                            "ko": "한 블록으로 모아서"},
    "bg.q3.placement.a3":  {"en": "Mixed with evenings (Day → Evening → Night rotation)",
                            "ko": "저녁과 함께 회전 (주간 → 저녁 → 야간)"},
    "bg.q3.placement.a4":  {"en": "No strong preference",
                            "ko": "특별한 선호 없음"},

    # === Version B — rankable agree-statements ===
    # Q1 (5 statements)
    "bg.b.q1.s1": {"en": "I strongly prefer weekday shifts",
                   "ko": "주중 근무를 매우 선호함"},
    "bg.b.q1.s2": {"en": "I'd rather work weekdays if possible",
                   "ko": "가능하면 주중에 일하고 싶음"},
    "bg.b.q1.s3": {"en": "I'm equally happy with weekday or weekend work",
                   "ko": "주중·주말 모두 괜찮음"},
    "bg.b.q1.s4": {"en": "I'd rather work weekends if possible",
                   "ko": "가능하면 주말에 일하고 싶음"},
    "bg.b.q1.s5": {"en": "I strongly prefer weekend shifts",
                   "ko": "주말 근무를 매우 선호함"},

    # Q2 (3 — rank shift types directly)
    "bg.b.q2.intro": {"en": "Rank the shift types from most to least preferred.",
                      "ko": "선호하는 근무 유형을 순서대로 정렬해 주세요."},

    # Q3 (5 statements)
    "bg.b.q3.s1": {"en": "I'd rather avoid night shifts entirely if possible",
                   "ko": "가능하면 야간 근무를 완전히 피하고 싶음"},
    "bg.b.q3.s2": {"en": "Some nights are okay, ideally spread across the month",
                   "ko": "야간 근무는 어느 정도 괜찮지만, 분산되는 것이 좋음"},
    "bg.b.q3.s3": {"en": "I prefer my nights clumped into one block",
                   "ko": "야간 근무는 한 블록으로 모아 주는 게 좋음"},
    "bg.b.q3.s4": {"en": "I prefer rotating Day → Evening → Night together",
                   "ko": "주간 → 저녁 → 야간 순으로 함께 회전하는 것이 좋음"},
    "bg.b.q3.s5": {"en": "I want more night shifts (e.g., for the pay)",
                   "ko": "야간 근무를 늘리고 싶음 (예: 수당)"},

    # Q4 (3 statements)
    "bg.b.q4.s1": {"en": "Stick strictly to the required number of shifts",
                   "ko": "정해진 근무 횟수만 채우고 싶음"},
    "bg.b.q4.s2": {"en": "A few extra shifts are fine, but not many",
                   "ko": "조금 더 일할 수는 있지만 많이는 어려움"},
    "bg.b.q4.s3": {"en": "Maximize total shifts to maximize income",
                   "ko": "수입을 위해 가능한 한 많이 일하고 싶음"},

    # Q5 (4 statements about which shift is hardest)
    "bg.b.q5.s1": {"en": "Day shifts are the hardest",
                   "ko": "주간 근무가 가장 힘듦"},
    "bg.b.q5.s2": {"en": "Evening shifts are the hardest",
                   "ko": "저녁 근무가 가장 힘듦"},
    "bg.b.q5.s3": {"en": "Night shifts are the hardest",
                   "ko": "야간 근무가 가장 힘듦"},
    "bg.b.q5.s4": {"en": "All three are about the same difficulty",
                   "ko": "세 가지 모두 비슷함"},

    # Q6 (4 statements)
    "bg.b.q6.s1": {"en": "Following circadian rhythm is very important to me",
                   "ko": "생체 리듬을 따르는 것이 매우 중요함"},
    "bg.b.q6.s2": {"en": "I'd prefer Day → Evening → Night order",
                   "ko": "주간 → 저녁 → 야간 순서를 선호함"},
    "bg.b.q6.s3": {"en": "I'd prefer Night → Evening → Day order",
                   "ko": "야간 → 저녁 → 주간 순서를 선호함"},
    "bg.b.q6.s4": {"en": "Circadian rhythm doesn't matter much to me",
                   "ko": "생체 리듬은 그렇게 중요하지 않음"},

    # Q7 (4 statements)
    "bg.b.q7.s1": {"en": "Working with my preferred coworkers matters a lot",
                   "ko": "마음 맞는 동료와 일하는 것이 매우 중요함"},
    "bg.b.q7.s2": {"en": "The shift culture / vibe matters to me",
                   "ko": "근무의 분위기·문화가 중요함"},
    "bg.b.q7.s3": {"en": "Having a good charge nurse on shift is important",
                   "ko": "좋은 책임 간호사와 함께 일하는 것이 중요함"},
    "bg.b.q7.s4": {"en": "Team dynamics don't really affect my shift preferences",
                   "ko": "팀 분위기는 근무 선호에 별로 영향 없음"},

    # Q1 — weekday vs weekend
    "bg.q1.title": {"en": "Weekdays vs. weekends",
                    "ko": "주중 vs 주말 근무"},
    "bg.q1.help":  {"en": "Some prefer weekend work; others prefer weekdays.",
                    "ko": "주말 근무를 선호하시는 분도, 주중 근무를 선호하시는 분도 있습니다."},
    "bg.q1.scale": {"en": "Where do you sit on this?",
                    "ko": "본인은 어느 쪽에 가까운가요?"},
    "bg.q1.s1": {"en": "Strongly prefer weekdays", "ko": "주중을 매우 선호"},
    "bg.q1.s2": {"en": "Prefer weekdays",          "ko": "주중을 선호"},
    "bg.q1.s3": {"en": "No preference",            "ko": "차이 없음"},
    "bg.q1.s4": {"en": "Prefer weekends",          "ko": "주말을 선호"},
    "bg.q1.s5": {"en": "Strongly prefer weekends", "ko": "주말을 매우 선호"},
    "bg.q1.notes_ph": {"en": "Why? (optional)",
                       "ko": "이유는 무엇인가요? (선택)"},

    # Q2 — shift type ranking
    "bg.q2.title": {"en": "Shift type preference",
                    "ko": "근무 유형 선호도"},
    "bg.q2.help":  {"en": "Some prefer night shifts (higher pay); others don't.",
                    "ko": "수당이 높아 야간 근무를 선호하는 분도, 그렇지 않은 분도 있습니다."},
    "bg.q2.most":  {"en": "Most preferred shift type",
                    "ko": "가장 선호하는 근무 유형"},
    "bg.q2.least": {"en": "Least preferred shift type",
                    "ko": "가장 기피하는 근무 유형"},
    "bg.q2.notes_ph": {"en": "Why? — pay, body clock, family time, etc.",
                       "ko": "이유는 무엇인가요? — 수당, 생체 리듬, 가족 시간 등"},

    # Q3 — night shifts
    "bg.q3.title": {"en": "Night shifts",
                    "ko": "야간 근무"},
    "bg.q3.help":  {"en": "How comfortable are you with night work?",
                    "ko": "야간 근무는 어느 정도까지 괜찮으신가요?"},
    "bg.q3.stance":     {"en": "Your stance",
                         "ko": "야간 근무에 대한 입장"},
    "bg.q3.stance.a1":  {"en": "Avoid as much as possible",
                         "ko": "가능한 한 줄이고 싶음"},
    "bg.q3.stance.a2":  {"en": "Don't love them, okay in moderation",
                         "ko": "그리 좋아하진 않지만 적당히는 괜찮음"},
    "bg.q3.stance.a3":  {"en": "Neutral",
                         "ko": "보통"},
    "bg.q3.stance.a4":  {"en": "Actively prefer them (e.g. for the pay)",
                         "ko": "오히려 선호함 (예: 수당)"},
    "bg.q3.max_label":  {"en": "Maximum night shifts per month I'd accept",
                         "ko": "한 달 최대 야간 근무 수"},
    "bg.q3.notes_ph":   {"en": "Anything else? Spread, blocks, exceptions…",
                         "ko": "추가로 알려주실 점이 있나요? 배치 방식, 블록, 예외 등"},

    # Q4 — monthly volume
    "bg.q4.title": {"en": "Monthly shift volume",
                    "ko": "월 근무 횟수"},
    "bg.q4.help":  {"en": "Your floor / ceiling per month, plus how you "
                          "weigh income vs. just hitting the required count.",
                    "ko": "한 달 최소·최대 근무 횟수와, 수입을 늘리는 것과 "
                          "정해진 횟수만 채우는 것 중 어느 쪽을 선호하시는지 알려 주세요."},
    "bg.q4.min":   {"en": "Minimum shifts per month",
                    "ko": "월 최소 근무 횟수"},
    "bg.q4.max":   {"en": "Maximum shifts per month",
                    "ko": "월 최대 근무 횟수"},
    "bg.q4.stance":      {"en": "Your stance on volume",
                          "ko": "근무 횟수에 대한 입장"},
    "bg.q4.stance.a1":   {"en": "Stick strictly to the required count",
                          "ko": "정해진 횟수만 채우고 싶음"},
    "bg.q4.stance.a2":   {"en": "Somewhere in between",
                          "ko": "중간 정도"},
    "bg.q4.stance.a3":   {"en": "Maximize total to maximize income",
                          "ko": "수입을 위해 최대한 많이"},

    # Q5 — difficulty
    "bg.q5.title": {"en": "Tasks & difficulty by shift",
                    "ko": "근무 유형별 업무·난이도 차이"},
    "bg.q5.help":  {"en": "Do tasks or workload differ noticeably across day, "
                          "evening, and night?",
                    "ko": "주간·저녁·야간 근무 사이에 업무 내용이나 난이도에 차이가 있다고 느끼시나요?"},
    "bg.q5.differ":      {"en": "Do tasks/difficulty differ?",
                          "ko": "차이가 있나요?"},
    "bg.q5.differ.a1":   {"en": "Yes, substantially",
                          "ko": "예, 많이 다릅니다"},
    "bg.q5.differ.a2":   {"en": "Somewhat",
                          "ko": "다소 다릅니다"},
    "bg.q5.differ.a3":   {"en": "Not really",
                          "ko": "별로 다르지 않습니다"},
    "bg.q5.hardest":     {"en": "Which feels hardest?",
                          "ko": "어떤 근무가 가장 힘드신가요?"},
    "bg.q5.hardest.equal":{"en": "Roughly equal", "ko": "비슷합니다"},
    "bg.q5.affects":      {"en": "Does this affect which shift you prefer?",
                           "ko": "이 차이가 선호 근무 유형에 영향을 주나요?"},
    "bg.q5.affects.a1":   {"en": "Yes",        "ko": "예"},
    "bg.q5.affects.a2":   {"en": "A little",   "ko": "조금"},
    "bg.q5.affects.a3":   {"en": "No",         "ko": "아니요"},
    "bg.q5.notes_ph":    {"en": "What's different? — task volume, acuity, staffing…",
                          "ko": "구체적으로 어떤 점이 다른가요? 업무량, 환자 중증도, 인력 등"},

    # Q6 — circadian
    "bg.q6.title": {"en": "Circadian rhythm",
                    "ko": "생체 리듬"},
    "bg.q6.help":  {"en": "Research suggests rotating Day → Evening → Night fits "
                          "the body clock better.",
                    "ko": "주간 → 저녁 → 야간 순으로 근무가 바뀌는 것이 몸에 더 잘 맞는다는 연구가 있습니다."},
    "bg.q6.importance":  {"en": "How important is following this to you?",
                          "ko": "이 부분이 본인에게 얼마나 중요한가요?"},
    "bg.q6.imp.a1":      {"en": "Not at all",        "ko": "전혀 중요하지 않음"},
    "bg.q6.imp.a2":      {"en": "Slightly",          "ko": "약간"},
    "bg.q6.imp.a3":      {"en": "Moderately",        "ko": "보통"},
    "bg.q6.imp.a4":      {"en": "Quite",             "ko": "꽤 중요"},
    "bg.q6.imp.a5":      {"en": "Very important",    "ko": "매우 중요"},
    "bg.q6.direction":    {"en": "Preferred rotation",
                           "ko": "선호하는 로테이션"},
    "bg.q6.direction.a1": {"en": "Day → Evening → Night",
                           "ko": "주간 → 저녁 → 야간"},
    "bg.q6.direction.a2": {"en": "Night → Evening → Day",
                           "ko": "야간 → 저녁 → 주간"},
    "bg.q6.direction.a3": {"en": "Doesn't matter",
                           "ko": "상관없음"},
    "bg.q6.notes_ph":     {"en": "How would you arrange shifts for this?",
                           "ko": "이 부분을 고려한다면 스케줄을 어떻게 구성하시겠습니까?"},

    # Q7 — interpersonal
    "bg.q7.title": {"en": "Team & social dynamics",
                    "ko": "팀 및 인간관계"},
    "bg.q7.help":  {"en": "Do interpersonal dynamics influence which shifts you'd rather work?",
                    "ko": "동료 관계나 근무 분위기 같은 사회적 요소가 근무 선호에 영향을 주나요?"},
    "bg.q7.importance":   {"en": "How much do team relationships affect your shift preferences?",
                           "ko": "팀 관계가 근무 선호에 얼마나 영향을 주나요?"},
    "bg.q7.imp.a1":       {"en": "Not at all", "ko": "전혀 영향 없음"},
    "bg.q7.imp.a5":       {"en": "A great deal", "ko": "매우 많이"},
    "bg.q7.notes_ph":     {"en": "What kinds of dynamics matter? Coworkers, "
                                  "charge nurse, shift culture…",
                           "ko": "어떤 부분이 중요한가요? 동료, 책임 간호사, 근무 분위기 등"},

    # === Compare ===
    "compare.title":    {"en": "Compare two schedules",
                         "ko": "두 가지 근무표 비교"},
    "compare.subtitle": {
        "en": "Imagine each is your next month. Which would you rather work?",
        "ko": "각각이 당신의 다음 달 근무표라고 가정해 보세요. 어느 쪽을 더 일하고 싶나요?"},
    "compare.option_a": {"en": "Option A", "ko": "선택지 A"},
    "compare.option_b": {"en": "Option B", "ko": "선택지 B"},
    "compare.your_pick":{"en": "Your pick", "ko": "당신의 선택"},
    "compare.prefer_a": {"en": "← Prefer A",     "ko": "← A가 좋음"},
    "compare.tie":      {"en": "No preference",  "ko": "차이 없음"},
    "compare.prefer_b": {"en": "Prefer B →",     "ko": "B가 좋음 →"},
    "compare.why":      {"en": "Optional: in one phrase, why?",
                         "ko": "선택 사항: 한 문장으로 이유를 알려 주세요"},
    "compare.why_ph":   {"en": "e.g. 'too many night shifts in B'",
                         "ko": "예: 'B는 야간 근무가 너무 많아요'"},
    "compare.recorded": {"en": "{n} comparisons recorded",
                         "ko": "{n}개의 비교 기록됨"},
    "compare.your_responses": {"en": "Your responses", "ko": "응답 기록"},
    "compare.empty":    {"en": "No comparisons yet — pick A or B above.",
                         "ko": "아직 비교가 없습니다 — 위에서 A 또는 B를 선택하세요."},
    "compare.col.round":  {"en": "Round",      "ko": "회차"},
    "compare.col.a":      {"en": "A pattern",  "ko": "A 패턴"},
    "compare.col.b":      {"en": "B pattern",  "ko": "B 패턴"},
    "compare.col.picked": {"en": "Picked",     "ko": "선택"},
    "compare.download":   {"en": "Download responses (JSON)",
                           "ko": "응답 다운로드 (JSON)"},

    # === Rank ===
    "rank.title": {"en": "Rank what matters most",
                   "ko": "가장 중요한 것을 순위로 매겨 주세요"},
    "rank.subtitle": {
        "en": "Use the arrows to reorder. #1 affects your quality of life the most.",
        "ko": "화살표로 순서를 바꿔 주세요. 1번이 일상에 가장 큰 영향을 줍니다."},
    "rank.ranked":   {"en": "Ranked", "ko": "순위"},
    "rank.dropped":  {"en": "Doesn't matter ({n})", "ko": "중요하지 않음 ({n})"},
    "rank.up":       {"en": "▲", "ko": "▲"},
    "rank.down":     {"en": "▼", "ko": "▼"},
    "rank.drop":     {"en": "Drop", "ko": "제외"},
    "rank.restore":  {"en": "Restore", "ko": "복원"},
    "rank.empty_drop":  {"en": "Move items here if you don't care about them.",
                         "ko": "관심 없는 항목은 이곳으로 이동시킵니다."},
    "rank.freeform_label": {"en": "Anything else? (free text)",
                            "ko": "추가로 알려주실 점이 있나요? (자유 입력)"},
    "rank.freeform_ph": {
        "en": "e.g. I prefer to keep Wednesdays free for school pickup.",
        "ko": "예: 수요일은 아이 등하원 때문에 비워 두고 싶어요."},
    "rank.download": {"en": "Download my ranking (JSON)",
                      "ko": "내 순위 다운로드 (JSON)"},

    # Rank feature labels
    "rank.feat.no_consec_nights": {
        "en": "No more than 2 nights in a row",
        "ko": "야간 근무 연속 2일 이내"},
    "rank.feat.weekends_off":     {
        "en": "At least every other weekend off",
        "ko": "최소 2주에 한 번은 주말 휴무"},
    "rank.feat.long_blocks":      {
        "en": "Long work block + long off block (4 on / 4 off)",
        "ko": "근무·휴무를 긴 블록으로 묶기 (4일 근무 / 4일 휴무)"},
    "rank.feat.no_quick_turn":    {
        "en": "No quick turnarounds (night → day next morning)",
        "ko": "야간 후 다음 날 아침 주간 근무 없음"},
    "rank.feat.predictable":      {
        "en": "Predictable, repeating weekly pattern",
        "ko": "주 단위로 반복되는 예측 가능한 패턴"},
    "rank.feat.self_pick_off":    {
        "en": "I can pick my off days each month",
        "ko": "매달 휴무일을 직접 선택"},
    "rank.feat.balanced_shifts":  {
        "en": "Even mix of day / evening / night",
        "ko": "주간·저녁·야간이 고르게 섞임"},
    "rank.feat.partner_aligned":  {
        "en": "Aligned with a coworker's schedule",
        "ko": "동료와 일정 맞춤"},

    # === Ideal ===
    "ideal.title":  {"en": "Build your ideal month",
                     "ko": "이상적인 한 달 만들기"},
    "ideal.subtitle": {
        "en": "Sketch the perfect month. Click a cell to pick Day, Evening, "
              "Night, or Off.",
        "ko": "이상적인 한 달을 직접 그려 주세요. 셀을 눌러 주간·저녁·야간·휴무를 선택하세요."},
    "ideal.edit_label":   {"en": "Edit by week", "ko": "주 단위 편집"},
    "ideal.editor_hint":  {
        "en": "Each row holds 7 days; the calendar pads to the real month layout.",
        "ko": "한 행은 7일이며, 달력은 실제 월의 형태에 맞춰 정렬됩니다."},
    "ideal.totals":   {"en": "Totals", "ko": "합계"},
    "ideal.preview":  {"en": "Calendar preview", "ko": "달력 미리보기"},
    "ideal.note_label":{"en": "Add a note about why this is your ideal",
                        "ko": "왜 이상적인지 간단히 적어 주세요 (선택)"},
    "ideal.note_ph":  {
        "en": "e.g. 'I love front-loading nights so the back half is family time.'",
        "ko": "예: '야간을 앞쪽에 몰면 후반부는 가족과 보낼 수 있어요.'"},
    "ideal.download":  {"en": "Download my ideal month (JSON)",
                        "ko": "내 이상적인 한 달 다운로드 (JSON)"},

    # === Trade-offs ===
    "trade.title":     {"en": "Trade-offs", "ko": "절충점"},
    "trade.subtitle":  {
        "en": "Real schedules force compromises. Tell us where your line is.",
        "ko": "실제 근무표에는 타협이 필요합니다. 당신의 기준선을 알려 주세요."},
    "trade.value_label": {"en": "Value", "ko": "값"},
    "trade.forced":    {"en": "Forced choices", "ko": "양자택일"},
    "trade.freeform_label":{"en": "Anything else?",  "ko": "추가로 알려 주실 점은?"},
    "trade.freeform_ph": {
        "en": "e.g. 'I can do back-to-back nights but not after a holiday weekend.'",
        "ko": "예: '연속 야간은 가능하지만 연휴 다음에는 어렵습니다.'"},
    "trade.download":  {"en": "Download my trade-offs (JSON)",
                        "ko": "내 절충점 다운로드 (JSON)"},
    # Slider items
    "trade.q.consec_nights_max":   {"en": "Max nights in a row",
                                    "ko": "연속 야간 최대 일수"},
    "trade.q.consec_nights_max.h": {
        "en": "Beyond this, fatigue / safety becomes a concern.",
        "ko": "이 이상이면 피로·안전 문제가 생깁니다."},
    "trade.q.weekend_off_freq":    {"en": "Weekends off per month (min)",
                                    "ko": "월 최소 주말 휴무 수"},
    "trade.q.weekend_off_freq.h":  {"en": "Out of ~4 weekends.",
                                    "ko": "보통 4번의 주말 중에서."},
    "trade.q.extra_nights_for_weekend": {
        "en": "Extra nights I'd trade for one extra weekend off",
        "ko": "주말 하루를 더 얻기 위해 추가로 받아들일 야간 수"},
    "trade.q.extra_nights_for_weekend.h": {
        "en": "How many more nights would you accept to free a weekend?",
        "ko": "주말을 비우기 위해 야간 근무를 얼마까지 더 받을 수 있나요?"},
    "trade.q.min_rest_hours":      {"en": "Minimum rest between shifts (hrs)",
                                    "ko": "근무 사이 최소 휴식 (시간)"},
    "trade.q.min_rest_hours.h":    {
        "en": "Below this you'd push back, even if legal.",
        "ko": "이보다 짧으면 법적으로 가능해도 거절합니다."},
    "trade.q.predictability_vs_choice": {
        "en": "Predictable rotation  ←→  Pick-your-own each month",
        "ko": "예측 가능한 로테이션  ←→  매달 직접 선택"},
    "trade.q.predictability_vs_choice.h": {
        "en": "0 = fixed cycle. 100 = bid every month.",
        "ko": "0 = 고정 주기. 100 = 매달 직접 신청."},
    "trade.q.team_alignment_weight": {
        "en": "Aligning shifts with a teammate",
        "ko": "팀 동료와 시간 맞추기"},
    "trade.q.team_alignment_weight.h": {
        "en": "0 = doesn't matter; 100 = strongly prefer.",
        "ko": "0 = 상관없음, 100 = 매우 선호."},
    "trade.q.overtime_appetite":   {"en": "Voluntary OT hours/month",
                                    "ko": "월 자발적 초과 근무 시간"},
    "trade.q.overtime_appetite.h": {"en": "Capacity, not a commitment.",
                                    "ko": "약속이 아닌 가능 범위입니다."},
    # Forced choices
    "trade.f.holiday.q": {
        "en": "Christmas Day or New Year's Eve — which would you work?",
        "ko": "성탄절과 새해 전야 중 어느 쪽에 근무하시겠습니까?"},
    "trade.f.holiday.a1": {"en": "Christmas Day", "ko": "성탄절"},
    "trade.f.holiday.a2": {"en": "New Year's Eve", "ko": "새해 전야"},
    "trade.f.holiday.a3": {"en": "I'd swap with someone",
                           "ko": "다른 사람과 바꾸겠습니다"},
    "trade.f.double.q":   {
        "en": "12-hour double-shift OR two split 6-hour shifts the same day?",
        "ko": "12시간 연속 근무 또는 같은 날 6시간씩 나눠 두 번?"},
    "trade.f.double.a1":  {"en": "12-hour double", "ko": "12시간 연속"},
    "trade.f.double.a2":  {"en": "Two 6-hour splits", "ko": "6시간 두 번"},
    "trade.f.double.a3":  {"en": "Neither", "ko": "둘 다 거절"},
    "trade.f.notice.q":   {"en": "How short is too short for a shift-change request?",
                           "ko": "근무 변경 요청은 얼마나 빨리 알려 줘야 하나요?"},
    "trade.f.notice.a1":  {"en": "< 24 hrs",  "ko": "24시간 미만"},
    "trade.f.notice.a2":  {"en": "< 48 hrs",  "ko": "48시간 미만"},
    "trade.f.notice.a3":  {"en": "< 1 week",  "ko": "1주 미만"},
    "trade.f.notice.a4":  {"en": "Anything is fine", "ko": "언제든 괜찮음"},

    # === Day prefs ===
    "day.title": {"en": "Day-by-day preferences",
                  "ko": "요일별 선호도"},
    "day.subtitle": {
        "en": "Rate every shift × weekday combination. We use this as soft cost.",
        "ko": "각 근무 × 요일 조합에 대한 선호도를 매겨 주세요. 소프트 제약으로 사용됩니다."},
    "day.editor_label": {
        "en": "Set your ratings (-2 avoid · 0 neutral · +2 love)",
        "ko": "점수 설정 (-2 기피 · 0 보통 · +2 선호)"},
    "day.preview_label": {"en": "Heatmap preview", "ko": "히트맵 미리보기"},
    "day.legend.m2": {"en": "-2 · Avoid",    "ko": "-2 · 기피"},
    "day.legend.m1": {"en": "-1 · Mild no",  "ko": "-1 · 다소 싫음"},
    "day.legend.z":  {"en": "0 · Neutral",   "ko": "0 · 보통"},
    "day.legend.p1": {"en": "+1 · Mild yes", "ko": "+1 · 다소 좋음"},
    "day.legend.p2": {"en": "+2 · Love it",  "ko": "+2 · 매우 좋음"},
    "day.weekday.Mon": {"en": "Mon", "ko": "월"},
    "day.weekday.Tue": {"en": "Tue", "ko": "화"},
    "day.weekday.Wed": {"en": "Wed", "ko": "수"},
    "day.weekday.Thu": {"en": "Thu", "ko": "목"},
    "day.weekday.Fri": {"en": "Fri", "ko": "금"},
    "day.weekday.Sat": {"en": "Sat", "ko": "토"},
    "day.weekday.Sun": {"en": "Sun", "ko": "일"},
    "day.freeform_label": {"en": "Anything special about a particular day?",
                           "ko": "특정 요일에 대해 특별한 점이 있나요?"},
    "day.freeform_ph": {
        "en": "e.g. 'Tuesdays I'd rather not have a night shift, kids' "
              "activities run late.'",
        "ko": "예: '화요일은 아이 일정 때문에 야간 근무를 피하고 싶습니다.'"},
    "day.download": {"en": "Download my preferences (JSON)",
                     "ko": "내 선호도 다운로드 (JSON)"},
}


def set_lang(code: str) -> None:
    if code in LANGUAGES:
        st.session_state["lang"] = code


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT)


def t(key: str, **kwargs) -> str:
    """Look up a translation. ``**kwargs`` are str.format-style substitutions."""
    entry = _T.get(key)
    if not entry:
        return key
    text = entry.get(get_lang()) or entry.get(DEFAULT) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def language_picker(label_visibility: str = "collapsed") -> None:
    """Render a language selectbox; updates session_state['lang']."""
    codes = list(LANGUAGES.keys())
    current = st.session_state.get("lang", DEFAULT)
    idx = codes.index(current) if current in codes else 0
    choice = st.selectbox(
        t("app.language"),
        options=codes,
        index=idx,
        format_func=lambda c: LANGUAGES[c],
        key="lang_picker",
        label_visibility=label_visibility,
    )
    if choice != current:
        st.session_state["lang"] = choice
        st.rerun()
