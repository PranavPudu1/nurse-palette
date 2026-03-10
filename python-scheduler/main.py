"""
FastAPI wrapper for the OR-Tools nurse schedule optimizer.
Deploy this as a standalone Python service (Cloud Run, Railway, Render, etc.)

Install deps:  pip install fastapi uvicorn ortools pydantic
Run locally:   uvicorn main:app --reload --port 8080
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ortools.sat.python import cp_model
from typing import Optional

app = FastAPI(title="Nurse Schedule Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Request / Response models
# ──────────────────────────────────────────────
class NurseInput(BaseModel):
    id: str
    name: str
    level: int  # 1 = junior, 2 = senior


class WardConfigInput(BaseModel):
    shift_type: str  # "D", "E", "N"
    required_nurses: int
    min_high: int  # minimum level-2 nurses for this shift


class PreferenceInput(BaseModel):
    nurse_id: str
    prefers_weekend: bool
    prefers_night: bool
    prefers_weekday: bool


class UnavailInput(BaseModel):
    nurse_id: str
    day: int  # 1-indexed day of month


class ExclusionInput(BaseModel):
    nurse_id_1: str
    nurse_id_2: str


class ScheduleRequest(BaseModel):
    year: int
    month: int  # 0-indexed (JS convention) — we convert internally
    days_in_month: int
    nurses: list[NurseInput]
    ward_configs: list[WardConfigInput]
    preferences: list[PreferenceInput]
    unavailability: list[UnavailInput]
    exclusions: list[ExclusionInput]
    num_options: int = 3
    time_limit_seconds: float = 15.0


class ScheduleOption(BaseModel):
    id: str
    label: str
    schedule: dict[str, dict[str, str]]  # nurse_id -> { "YYYY-MM-DD": "D"|"E"|"N"|"X" }
    objective_value: Optional[float] = None


class ScheduleResponse(BaseModel):
    options: list[ScheduleOption]


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def date_key(year: int, month_0: int, day: int) -> str:
    """Produce 'YYYY-MM-DD' matching the JS frontend convention (month is 0-indexed)."""
    return f"{year}-{str(month_0 + 1).zfill(2)}-{str(day).zfill(2)}"


DAY_SLOT, EVE_SLOT, NGT_SLOT = 1, 2, 3
SLOT_MAP = {"D": DAY_SLOT, "E": EVE_SLOT, "N": NGT_SLOT}
SLOT_NAME = {DAY_SLOT: "D", EVE_SLOT: "E", NGT_SLOT: "N"}
HOURS_PER_SHIFT = 8


def solve_schedule(req: ScheduleRequest, seed: int) -> tuple[dict, float | None]:
    """Build & solve one CP-SAT model. Returns (schedule_dict, objective_value)."""

    D = req.days_in_month
    nurses = req.nurses
    N = len(nurses)
    T = 3  # always 3 slots
    slots = [DAY_SLOT, EVE_SLOT, NGT_SLOT]
    nurse_ids = [n.id for n in nurses]
    id_to_idx = {n.id: idx for idx, n in enumerate(nurses)}
    levels = [n.level for n in nurses]
    high_indices = [idx for idx, n in enumerate(nurses) if n.level >= 2]

    # Build demand & min_high matrices (D x T)
    default_demand = {s: 2 for s in ["D", "E", "N"]}
    default_min_high = {s: 0 for s in ["D", "E", "N"]}
    for wc in req.ward_configs:
        default_demand[wc.shift_type] = wc.required_nurses
        default_min_high[wc.shift_type] = wc.min_high

    demand = [[default_demand["D"], default_demand["E"], default_demand["N"]] for _ in range(D)]
    min_high = [[default_min_high["D"], default_min_high["E"], default_min_high["N"]] for _ in range(D)]

    # Unavailability set: (nurse_idx, day_1indexed)
    unavail_set: set[tuple[int, int]] = set()
    for u in req.unavailability:
        if u.nurse_id in id_to_idx:
            unavail_set.add((id_to_idx[u.nurse_id], u.day))

    # Preference maps
    pref_weekend = [0] * N
    pref_night = [0] * N
    for p in req.preferences:
        if p.nurse_id in id_to_idx:
            idx = id_to_idx[p.nurse_id]
            pref_weekend[idx] = 1 if p.prefers_weekend else 0
            pref_night[idx] = 1 if p.prefers_night else 0

    # Exclusion pairs as index pairs
    excl_pairs: list[tuple[int, int]] = []
    for e in req.exclusions:
        if e.nurse_id_1 in id_to_idx and e.nurse_id_2 in id_to_idx:
            excl_pairs.append((id_to_idx[e.nurse_id_1], id_to_idx[e.nurse_id_2]))

    days = list(range(1, D + 1))
    nurse_range = list(range(N))

    # Weekend days (using actual calendar)
    weekend_days: set[int] = set()
    for d in days:
        import datetime
        dow = datetime.date(req.year, req.month + 1, d).weekday()  # 0=Mon, 5=Sat, 6=Sun
        if dow >= 5:
            weekend_days.add(d)

    # ── CP-SAT Model ──
    m = cp_model.CpModel()

    # Decision variables: x[(i, d, t)] = 1 if nurse i works slot t on day d
    x = {(i, d, t): m.new_bool_var(f"x_{i}_{d}_{t}")
         for i in nurse_range for d in days for t in slots}

    # Derived: work[(i,d)] and active[i]
    work = {(i, d): m.new_bool_var(f"w_{i}_{d}") for i in nurse_range for d in days}
    active = {i: m.new_bool_var(f"a_{i}") for i in nurse_range}

    # ── Constraints ──

    # 1. One shift per nurse per day + link work variable
    for i in nurse_range:
        for d in days:
            m.add(sum(x[(i, d, t)] for t in slots) <= 1)
            m.add(work[(i, d)] == sum(x[(i, d, t)] for t in slots))
            if (i, d) in unavail_set:
                m.add(work[(i, d)] == 0)
            m.add(work[(i, d)] <= active[i])

    # 2. Demand coverage & skill mix
    for d in days:
        for t_idx, t in enumerate(slots):
            m.add(sum(x[(i, d, t)] for i in nurse_range) >= demand[d - 1][t_idx])
            if high_indices:
                m.add(sum(x[(i, d, t)] for i in high_indices) >= min_high[d - 1][t_idx])

    # 3. Max consecutive workdays = 4
    MAX_CONSEC = 4
    if MAX_CONSEC + 1 <= D:
        for i in nurse_range:
            for start in range(1, D - MAX_CONSEC + 1):
                m.add(sum(work[(i, start + k)] for k in range(MAX_CONSEC + 1)) <= MAX_CONSEC)

    # 4. Night sliding window: max 1 night in any 3-day block
    NIGHT_WINDOW_K = 3
    for i in nurse_range:
        for start in range(1, D - NIGHT_WINDOW_K + 2):
            m.add(sum(x[(i, start + k, NGT_SLOT)] for k in range(NIGHT_WINDOW_K)) <= 1)

    # 5. Night block → 2 days off after
    DAYS_OFF_AFTER_NIGHT = 2
    for i in nurse_range:
        for d in range(1, D):
            both = m.new_bool_var(f"bN_{i}_{d}")
            m.add(both <= x[(i, d, NGT_SLOT)])
            m.add(both <= x[(i, d + 1, NGT_SLOT)])
            m.add(both >= x[(i, d, NGT_SLOT)] + x[(i, d + 1, NGT_SLOT)] - 1)
            for off_d in range(d + 2, min(D, d + 1 + DAYS_OFF_AFTER_NIGHT) + 1):
                m.add(work[(i, off_d)] <= 1 - both)

    # 6. If 3 consecutive workdays → 1 day off after
    CONSEC_TRIGGER = 3
    DAYS_OFF_AFTER_CONSEC = 1
    run = {(i, d): m.new_bool_var(f"run_{i}_{d}") for i in nurse_range for d in days}
    for i in nurse_range:
        for d in days:
            if d < CONSEC_TRIGGER:
                m.add(run[(i, d)] == 0)
            else:
                for k in range(CONSEC_TRIGGER):
                    m.add(run[(i, d)] <= work[(i, d - k)])
                m.add(run[(i, d)] >= sum(work[(i, d - k)] for k in range(CONSEC_TRIGGER)) - (CONSEC_TRIGGER - 1))
            for off_d in range(d + 1, min(D, d + DAYS_OFF_AFTER_CONSEC) + 1):
                m.add(work[(i, off_d)] <= 1 - run[(i, d)])

    # 7. Exclusion pairs: cannot work same shift on same day
    for (a, b) in excl_pairs:
        for d in days:
            for t in slots:
                m.add(x[(a, d, t)] + x[(b, d, t)] <= 1)

    # ── Objective ──
    base_rate_l1, base_rate_l2, night_premium, fixed_nurse_cost = 40, 55, 12, 200
    w_unpreferred, w_match_bonus, w_high_on_night = 30, 12, 15

    obj2 = []

    # Fixed cost per active nurse
    for i in nurse_range:
        obj2.append(2 * fixed_nurse_cost * active[i])

    # Wage costs
    for i in nurse_range:
        base = base_rate_l2 if levels[i] >= 2 else base_rate_l1
        for d in days:
            obj2.append(2 * HOURS_PER_SHIFT * base * x[(i, d, DAY_SLOT)])
            obj2.append(2 * HOURS_PER_SHIFT * base * x[(i, d, EVE_SLOT)])
            obj2.append(2 * HOURS_PER_SHIFT * (base + night_premium) * x[(i, d, NGT_SLOT)])

    # Overtime
    sum_work_var = {i: m.new_int_var(0, D, f"sw_{i}") for i in nurse_range}
    ot = {i: m.new_int_var(0, HOURS_PER_SHIFT * D, f"ot_{i}") for i in nurse_range}
    for i in nurse_range:
        m.add(sum_work_var[i] == sum(work[(i, d)] for d in days))
        hours_var = m.new_int_var(0, HOURS_PER_SHIFT * D, f"hrs_{i}")
        m.add(hours_var == HOURS_PER_SHIFT * sum_work_var[i])
        m.add(ot[i] >= hours_var - 40)
        m.add(ot[i] >= 0)
        base = base_rate_l2 if levels[i] >= 2 else base_rate_l1
        obj2.append(base * ot[i])

    # Preferences
    for i in nurse_range:
        for d in days:
            if d in weekend_days:
                obj2.append((-2 * w_match_bonus if pref_weekend[i] == 1 else 2 * w_unpreferred) * work[(i, d)])
            else:
                obj2.append((-2 * w_match_bonus if pref_weekend[i] == 0 else 2 * w_unpreferred) * work[(i, d)])
            obj2.append((-2 * (w_match_bonus // 2) if pref_night[i] == 1 else 2 * w_unpreferred) * x[(i, d, NGT_SLOT)])

    # High-skill nurses avoid nights
    for i in high_indices:
        for d in days:
            obj2.append(2 * w_high_on_night * x[(i, d, NGT_SLOT)])

    m.minimize(sum(obj2))

    # ── Solve ──
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = req.time_limit_seconds
    solver.parameters.num_workers = 4
    solver.parameters.random_seed = seed

    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise HTTPException(status_code=422, detail="No feasible schedule found. Check constraints/demand.")

    # ── Extract result ──
    schedule: dict[str, dict[str, str]] = {}
    for i in nurse_range:
        nid = nurse_ids[i]
        schedule[nid] = {}
        for d in days:
            key = date_key(req.year, req.month, d)
            assigned_slot = None
            for t in slots:
                if solver.value(x[(i, d, t)]) == 1:
                    assigned_slot = SLOT_NAME[t]
                    break
            schedule[nid][key] = assigned_slot or "X"

    return schedule, float(solver.objective_value) / 2.0


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────
@app.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(req: ScheduleRequest):
    options: list[ScheduleOption] = []
    for i in range(req.num_options):
        seed = 42 + i * 7919
        sched, obj_val = solve_schedule(req, seed)
        options.append(ScheduleOption(
            id=f"option-{i + 1}",
            label=f"Option {i + 1}",
            schedule=sched,
            objective_value=obj_val,
        ))
    return ScheduleResponse(options=options)


@app.get("/health")
async def health():
    return {"status": "ok"}
