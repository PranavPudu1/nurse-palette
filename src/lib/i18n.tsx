/**
 * Lightweight English / Korean translations.
 *
 * One dictionary, key -> {en, ko}, mirroring streamlit-prefs/i18n.py so the
 * two apps use the same Korean nursing terminology (주간/저녁/야간/휴무 etc).
 * `t(key)` falls back to English, then to the key itself, so a missing entry
 * can never blank out the UI. The choice persists in localStorage.
 *
 * Not translated: optimizer violation messages (built with interpolated
 * sentences in lib/schedule-constraints.ts) and data values like nurse or
 * option names.
 */
import { createContext, useContext, useState } from "react";

export type Lang = "en" | "ko";

const T: Record<string, { en: string; ko: string }> = {
  // === Shared chrome ===
  "app.title": { en: "Nurse Scheduler", ko: "간호사 근무표" },
  "app.signOut": { en: "Sign Out", ko: "로그아웃" },
  "app.loading": { en: "Loading…", ko: "불러오는 중…" },
  "app.noRole": {
    en: "No role assigned. Ask a manager to invite you.",
    ko: "배정된 역할이 없습니다. 관리자에게 초대를 요청해 주세요.",
  },

  // === Tabs ===
  "tab.schedule": { en: "Schedule", ko: "근무표" },
  "tab.nurses": { en: "Nurses", ko: "간호사" },
  "tab.wardConfig": { en: "Ward Config", ko: "병동 설정" },
  "tab.rules": { en: "Scheduling Rules", ko: "근무 규칙" },
  "tab.mySchedule": { en: "My Schedule", ko: "내 근무표" },
  "tab.team": { en: "Team Schedule", ko: "팀 근무표" },
  "tab.preferences": { en: "Preferences", ko: "선호도" },

  // === Shifts ===
  "shift.D": { en: "Day", ko: "주간" },
  "shift.E": { en: "Evening", ko: "저녁" },
  "shift.N": { en: "Night", ko: "야간" },
  "shift.X": { en: "Off", ko: "휴무" },

  // === Month selector ===
  "month.prev": { en: "Previous month", ko: "이전 달" },
  "month.next": { en: "Next month", ko: "다음 달" },

  // === Schedule tab ===
  "sched.generate": { en: "Auto-Generate", ko: "자동 생성" },
  "sched.generating": { en: "Generating…", ko: "생성 중…" },
  "sched.exportCsv": { en: "Export CSV", ko: "CSV 내보내기" },
  "sched.loading": { en: "Loading schedule…", ko: "근무표 불러오는 중…" },
  "sched.addFirst": {
    en: "Add nurses in the Nurses tab first.",
    ko: "먼저 간호사 탭에서 간호사를 추가해 주세요.",
  },
  "sched.nErrors": { en: "{n} errors", ko: "오류 {n}건" },
  "sched.nWarnings": { en: "{n} warnings", ko: "경고 {n}건" },
  "toast.notEnough.title": { en: "Not enough nurses", ko: "간호사가 부족합니다" },
  "toast.notEnough.desc": {
    en: "You have {have} accepted nurse(s) but your ward config requires {need} per day ({detail}). Accept more nurse invites or lower the ward requirements.",
    ko: "수락된 간호사는 {have}명인데 병동 설정은 하루 {need}명을 요구합니다 ({detail}). 간호사 초대를 더 수락하거나 병동 필요 인원을 줄여 주세요.",
  },
  "toast.infeasible.title": { en: "No feasible schedule", ko: "가능한 근무표가 없습니다" },
  "toast.infeasible.desc": {
    en: "The optimizer couldn't satisfy all constraints. Try: reducing required nurses per shift, accepting more nurse invites, or removing some unavailability entries.",
    ko: "모든 제약을 만족하는 근무표를 찾지 못했습니다. 근무조별 필요 인원을 줄이거나, 간호사 초대를 더 수락하거나, 근무 불가 날짜를 줄여 보세요.",
  },
  "toast.notConfigured.title": { en: "Scheduler not configured", ko: "스케줄러가 설정되지 않았습니다" },
  "toast.notConfigured.desc": {
    en: "The schedule optimizer service URL hasn't been set up yet. Contact your administrator.",
    ko: "근무표 최적화 서비스 URL이 아직 설정되지 않았습니다. 관리자에게 문의해 주세요.",
  },
  "toast.genFailed": { en: "Generation failed", ko: "생성에 실패했습니다" },
  "toast.applyFailed": { en: "Apply failed", ko: "적용에 실패했습니다" },
  "toast.applied.title": { en: "Schedule applied", ko: "근무표가 적용되었습니다" },
  "toast.applied.desc": {
    en: "The generated schedule has been saved.",
    ko: "생성된 근무표가 저장되었습니다.",
  },

  // === Grid ===
  "grid.nurse": { en: "Nurse", ko: "간호사" },
  "grid.newNurse": { en: "New nurse name…", ko: "새 간호사 이름…" },
  "grid.addNurse": { en: "Add Nurse", ko: "간호사 추가" },
  "grid.remove": { en: "Remove {name}", ko: "{name} 삭제" },

  // === Nurses panel ===
  "nurses.title": { en: "Nurses ({n})", ko: "간호사 ({n}명)" },
  "nurses.loading": { en: "Loading nurses…", ko: "간호사 불러오는 중…" },
  "nurses.none": { en: "No nurses yet. Add one above.", ko: "아직 간호사가 없습니다. 위에서 추가해 주세요." },
  "nurses.name": { en: "Name", ko: "이름" },
  "nurses.nameReq": { en: "Name *", ko: "이름 *" },
  "nurses.email": { en: "Email", ko: "이메일" },
  "nurses.phone": { en: "Phone", ko: "전화번호" },
  "nurses.dept": { en: "Department", ko: "부서" },
  "nurses.deptShort": { en: "Dept", ko: "부서" },
  "nurses.level": { en: "Level:", ko: "레벨:" },
  "nurses.lvl": { en: "Lvl", ko: "레벨" },
  "nurses.status": { en: "Status", ko: "상태" },
  "nurses.active": { en: "Active", ko: "활동 중" },
  "nurses.pending": { en: "Pending", ko: "대기 중" },
  "nurses.save": { en: "Save", ko: "저장" },
  "nurses.cancel": { en: "Cancel", ko: "취소" },
  "nurses.confirmRemove": { en: "Remove {name}?", ko: "{name}님을 삭제할까요?" },

  // === Ward config ===
  "ward.title": { en: "Ward Staffing Configuration", ko: "병동 인력 설정" },
  "ward.subtitle": {
    en: "Set required nurses per shift and the seniority level mix.",
    ko: "근무조별 필요 간호사 수와 연차(레벨) 구성을 설정합니다.",
  },
  "ward.loading": { en: "Loading ward config…", ko: "병동 설정 불러오는 중…" },
  "ward.shiftCard": { en: "{shift} Shift ({code})", ko: "{shift} 근무 ({code})" },
  "ward.required": { en: "Required Nurses", ko: "필요 간호사 수" },
  "ward.levelMix": { en: "Level Mix (nurses per level)", ko: "레벨 구성 (레벨별 인원)" },
  "ward.levelN": { en: "Level {n}:", ko: "레벨 {n}:" },
  "ward.save": { en: "Save", ko: "저장" },

  // === Scheduling rules ===
  "rules.title": { en: "Scheduling Rules", ko: "근무 규칙" },
  "rules.subtitle": {
    en: "Configure the hard constraint parameters used by the optimizer.",
    ko: "최적화에 사용되는 필수 규칙 값을 설정합니다.",
  },
  "rules.loading": { en: "Loading…", ko: "불러오는 중…" },
  "rules.save": { en: "Save Rules", ko: "규칙 저장" },
  "rules.max_shifts_per_day": { en: "Max shifts per nurse per day", ko: "간호사별 하루 최대 근무 수" },
  "rules.night_window_max": { en: "Max night shifts in sliding window", ko: "기간 내 최대 야간 근무 수" },
  "rules.night_window_k": { en: "Night sliding window size (days)", ko: "야간 근무 계산 기간 (일)" },
  "rules.days_off_after_night_block": { en: "Days off after consecutive nights", ko: "연속 야간 근무 후 휴무 일수" },
  "rules.max_consecutive_workdays": { en: "Max consecutive workdays", ko: "최대 연속 근무 일수" },
  "rules.consec_trigger": { en: "Consecutive days trigger for rest", ko: "휴식이 필요한 연속 근무 기준" },
  "rules.days_off_after_consec": { en: "Days off after consecutive trigger", ko: "기준 초과 후 휴무 일수" },
  "rules.penalty.title": { en: "Level-Based Night Penalty", ko: "레벨별 야간 근무 패널티" },
  "rules.penalty.subtitle": {
    en: "Set penalty weights per nurse level for night shift assignments. Higher = stronger aversion.",
    ko: "레벨별 야간 근무 배정 패널티 가중치입니다. 높을수록 야간 근무를 더 피합니다.",
  },
  "rules.penalty.save": { en: "Save Level Penalties", ko: "레벨 패널티 저장" },
  "rules.levelN": { en: "Level {n}", ko: "레벨 {n}" },

  // === Schedule comparison ===
  "cmp.title": { en: "Compare Generated Schedules", ko: "생성된 근무표 비교" },
  "cmp.cancel": { en: "Cancel", ko: "취소" },
  "cmp.best": { en: "Best", ko: "최고" },
  "cmp.cost": { en: "Cost", ko: "비용" },
  "cmp.costHelp": {
    en: "Lower staffing cost scores higher (nights & overtime cost more).",
    ko: "인건비가 낮을수록 점수가 높습니다 (야간·초과 근무는 비용이 큽니다).",
  },
  "cmp.fairness": { en: "Fairness", ko: "공정성" },
  "cmp.fairnessHelp": {
    en: "How evenly total shifts are spread across nurses — 100 = everyone works the same number.",
    ko: "근무가 간호사들에게 얼마나 고르게 배분되는지입니다. 100이면 모두 같은 횟수로 일합니다.",
  },
  "cmp.violations": { en: "Violations", ko: "규칙 위반" },
  "cmp.violationsHelp": {
    en: "Fewer rule breaks scores higher (each error −15, each warning −5).",
    ko: "규칙 위반이 적을수록 점수가 높습니다 (오류당 −15점, 경고당 −5점).",
  },
  "cmp.nErrorsHard": { en: "{n} errors (hard)", ko: "오류(필수) {n}건" },
  "cmp.nWarningsSoft": { en: "{n} warnings (soft)", ko: "경고(선호) {n}건" },
  "cmp.score": { en: "Score: {n}", ko: "점수: {n}" },
  "cmp.scoreHelp": {
    en: "Overall 0–100, higher is better = 25% Cost + 35% Fairness + 40% Violations.",
    ko: "0–100점, 높을수록 좋습니다. 비용 25% + 공정성 35% + 규칙 위반 40%로 계산합니다.",
  },
  "cmp.preview": { en: "{label} — Preview", ko: "{label} 미리보기" },
  "cmp.apply": { en: "Apply {label}", ko: "{label} 적용" },

  // === Violations ===
  "viol.title": { en: "Schedule Issues", ko: "근무표 문제" },
  "viol.all": { en: "All ({n})", ko: "전체 ({n})" },
  "viol.errorsHard": { en: "Errors — hard ({n})", ko: "오류·필수 ({n})" },
  "viol.warningsSoft": { en: "Warnings — soft ({n})", ko: "경고·선호 ({n})" },
  "viol.noneIssues": { en: "No issues found", ko: "문제가 없습니다" },
  "viol.noneErrors": { en: "No errors found", ko: "오류가 없습니다" },
  "viol.noneWarnings": { en: "No warnings found", ko: "경고가 없습니다" },
  "viol.staffingGap": { en: "Staffing Gap", ko: "인력 부족" },
  "viol.errorPrefix": { en: "Error (hard rule): ", ko: "오류 (필수 규칙): " },
  "viol.warningPrefix": { en: "Warning (soft): ", ko: "경고 (선호): " },
  "viol.legendError": { en: "Error (hard rule)", ko: "오류 (필수 규칙)" },
  "viol.legendErrorDesc": { en: "— must not be broken", ko: "· 위반하면 안 됩니다" },
  "viol.legendWarning": { en: "Warning (soft)", ko: "경고 (선호)" },
  "viol.legendWarningDesc": { en: "— a preference / recommendation", ko: "· 선호·권장 사항입니다" },

  // === Nurse info dialog ===
  "info.levelN": { en: "Level {n}", ko: "레벨 {n}" },
  "info.level.1": { en: "Junior", ko: "신입" },
  "info.level.2": { en: "Mid-level", ko: "중견" },
  "info.level.3": { en: "Senior", ko: "선임" },
  "info.level.4": { en: "Specialist", ko: "전문" },
  "info.level.5": { en: "Lead", ko: "책임" },
  "info.contact": { en: "Contact", ko: "연락처" },

  // === Nurse preferences ===
  "pref.title": { en: "Shift Preferences", ko: "근무 선호도" },
  "pref.weekend": { en: "Prefers working weekends", ko: "주말 근무 선호" },
  "pref.weekday": { en: "Prefers working weekdays", ko: "평일 근무 선호" },
  "pref.night": { en: "Prefers night shifts", ko: "야간 근무 선호" },
  "pref.unavail": { en: "Unavailable Dates", ko: "근무 불가 날짜" },
  "pref.date": { en: "Date", ko: "날짜" },
  "pref.reason": { en: "Reason (optional)", ko: "사유 (선택)" },
  "pref.reasonPh": { en: "e.g. vacation", ko: "예: 휴가" },
  "pref.add": { en: "Add", ko: "추가" },
  "pref.noUnavail": { en: "No unavailable dates set.", ko: "설정된 근무 불가 날짜가 없습니다." },

  // === Soft constraints ===
  "soft.title": { en: "Soft Constraints", ko: "소프트 제약" },
  "soft.type": { en: "Type", ko: "유형" },
  "soft.day": { en: "Day #", ko: "일" },
  "soft.slot": { en: "Slot", ko: "근무조" },
  "soft.maxNights": { en: "Max Nights", ko: "최대 야간" },
  "soft.weight": { en: "Weight", ko: "가중치" },
  "soft.add": { en: "Add", ko: "추가" },
  "soft.none": { en: "No soft constraints set.", ko: "설정된 소프트 제약이 없습니다." },
  "soft.dayN": { en: "Day {n}", ko: "{n}일" },
  "soft.slotN": { en: "Slot {n}", ko: "근무조 {n}" },
  "soft.cap": { en: "Cap: {n}", ko: "상한: {n}" },
  "soft.allSlots": { en: "All slots", ko: "모든 근무조" },
  "soft.slotDay": { en: "Day (1)", ko: "주간 (1)" },
  "soft.slotEvening": { en: "Evening (2)", ko: "저녁 (2)" },
  "soft.slotNight": { en: "Night (3)", ko: "야간 (3)" },
  "soft.t.soft_unavail": { en: "Soft Unavailability", ko: "소프트 근무 불가" },
  "soft.t.soft_prefer_work": { en: "Prefer Working", ko: "근무 선호" },
  "soft.t.soft_prefer_shift": { en: "Prefer Specific Shift", ko: "특정 근무조 선호" },
  "soft.t.prefer_night": { en: "Prefer Night Shifts", ko: "야간 근무 선호" },
  "soft.t.avoid_night": { en: "Avoid Night Shifts", ko: "야간 근무 기피" },
  "soft.t.soft_max_nights": { en: "Soft Max Nights Cap", ko: "야간 근무 상한 (소프트)" },
  "soft.t.maximize_shifts": { en: "Maximize Shifts", ko: "근무 최대화" },

  // === Auth ===
  "auth.signInSub": { en: "Sign in to manage schedules", ko: "로그인하여 근무표를 관리하세요" },
  "auth.signUpSub": { en: "Create an account", ko: "계정 만들기" },
  "auth.email": { en: "Email", ko: "이메일" },
  "auth.password": { en: "Password", ko: "비밀번호" },
  "auth.role": { en: "Role", ko: "역할" },
  "auth.nurse": { en: "Nurse", ko: "간호사" },
  "auth.manager": { en: "Manager", ko: "관리자" },
  "auth.signIn": { en: "Sign In", ko: "로그인" },
  "auth.signUp": { en: "Sign Up", ko: "회원가입" },
  "auth.wait": { en: "Please wait…", ko: "잠시만 기다려 주세요…" },
  "auth.or": { en: "or", ko: "또는" },
  "auth.demo": { en: "Demo Accounts", ko: "데모 계정" },
  "auth.demoManager": { en: "Manager:", ko: "관리자:" },
  "auth.demoNurse": { en: "Nurse:", ko: "간호사:" },
  "auth.demoPassword": { en: "Password:", ko: "비밀번호:" },
  "auth.noAccount": { en: "Don't have an account?", ko: "계정이 없으신가요?" },
  "auth.hasAccount": { en: "Already have an account?", ko: "이미 계정이 있으신가요?" },
  "auth.signedIn": { en: "Signed in!", ko: "로그인되었습니다!" },
  "auth.created": { en: "Account created! You're now signed in.", ko: "계정이 생성되어 로그인되었습니다." },
  "auth.failed": { en: "Auth failed", ko: "인증에 실패했습니다" },

  // === Pending invite ===
  "invite.title": { en: "You've been invited!", ko: "초대를 받으셨습니다!" },
  "invite.subtitle": {
    en: "A manager has added you to the nurse schedule",
    ko: "관리자가 근무표에 회원님을 추가했습니다",
  },
  "invite.name": { en: "Name", ko: "이름" },
  "invite.dept": { en: "Department", ko: "부서" },
  "invite.email": { en: "Email", ko: "이메일" },
  "invite.accept": { en: "Accept Invite", ko: "초대 수락" },
  "invite.accepting": { en: "Accepting…", ko: "수락 중…" },
  "invite.none": { en: "No pending invites found.", ko: "대기 중인 초대가 없습니다." },
  "invite.accepted": { en: "Invite accepted! Welcome aboard.", ko: "초대를 수락했습니다. 환영합니다!" },
  "invite.acceptFailed": { en: "Failed to accept invite", ko: "초대 수락에 실패했습니다" },

  // === Nurse view ===
  "nv.noSchedule": { en: "No schedule assigned yet.", ko: "아직 배정된 근무표가 없습니다." },
  "nv.noTeam": { en: "No team members yet.", ko: "아직 팀원이 없습니다." },
  "nv.noProfile": { en: "No nurse profile found.", ko: "간호사 프로필을 찾을 수 없습니다." },
  "nv.nurse": { en: "Nurse", ko: "간호사" },
};

export const MONTH_NAMES_EN = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export const DAY_ABBR: Record<Lang, string[]> = {
  en: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
  ko: ["일", "월", "화", "수", "목", "금", "토"],
};

export function monthLabel(lang: Lang, year: number, month: number): string {
  return lang === "ko" ? `${year}년 ${month + 1}월` : `${MONTH_NAMES_EN[month]} ${year}`;
}

type Vars = Record<string, string | number>;

interface LangContext {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Vars) => string;
}

function translate(lang: Lang, key: string, vars?: Vars): string {
  let s = T[key]?.[lang] ?? T[key]?.en ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
  }
  return s;
}

const Ctx = createContext<LangContext>({
  lang: "en",
  setLang: () => {},
  t: (key, vars) => translate("en", key, vars),
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    try {
      return localStorage.getItem("np_lang") === "ko" ? "ko" : "en";
    } catch {
      return "en";
    }
  });
  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem("np_lang", l);
    } catch {
      // private mode; the choice just won't persist
    }
  };
  const t = (key: string, vars?: Vars) => translate(lang, key, vars);
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useLang(): LangContext {
  return useContext(Ctx);
}
