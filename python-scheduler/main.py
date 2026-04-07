"""
FastAPI wrapper for the OR-Tools nurse schedule optimizer.
Supports configurable hard constraints and rich soft constraints.

Install deps:  pip install fastapi uvicorn ortools pydantic
Run locally:   uvicorn main:app --reload --port 8080
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ortools.sat.python import cp_model
from typing import Optional
import datetime

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
    level: int  # 1..5


class WardConfigInput(BaseModel):
    shift_type: str  # "D", "E", "N"
    required_nurses: int
    min_high: int  # minimum level>=2 nurses for this shift


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


class SoftConstraintInput(BaseModel):
    constraint_type: str
    nurse_id: Optional[str] = None
    params: dict  # flexible JSON


class HardConstraintParams(BaseModel):
    max_shifts_per_day: int = 1
    night_window_max: int = 1
    night_window_k: int = 3
    days_off_after_night_block: int = 2
    max_consecutive_workdays: int = 4
    consec_trigger: int = 3
    days_off_after_consec: int = 1


class ScheduleRequest(BaseModel):
    year: int
    month: int  # 0-indexed (JS convention)
    days_in_month: int
    nurses: list[NurseInput]
    ward_configs: list[WardConfigInput]
    preferences: list[PreferenceInput]
    unavailability: list[UnavailInput]
    exclusions: list[ExclusionInput]
    soft_constraints: list[SoftConstraintInput] = []
    hard_constraints: Optional[HardConstraintParams] = None
    num_options: int = 3
    time_limit_seconds: float = 15.0


class ScheduleOption(BaseModel):
    id: str
    label: str
    schedule: dict[str, dict[str, str]]
    objective_value: Optional[float] = None


class ScheduleResponse(BaseModel):
    options: list[ScheduleOption]


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def date_key(year: int, month_0: int, day: int) -> str:
    return f"{year}-{str(month_0 + 1).zfill(2)}-{str(day).zfill(2)}"


DAY_SLOT, EVE_SLOT, NGT_SLOT = 1, 2, 3
SLOT_MAP = {"D": DAY_SLOT, "E": EVE_SLOT, "N": NGT_SLOT}
SLOT_NAME = {DAY_SLOT: "D", EVE_SLOT: "E", NGT_SLOT: "N"}
HOURS_PER_SHIFT = 8


def build_and_solve(req: ScheduleRequest, prev_solutions: list[dict] = None):
    """Build CP-SAT model, solve, return (schedule_dict, objective_value)."""

    hc = req.hard_constraints or HardConstraintParams()
    D = req.days_in_month
    nurses = req.nurses
    N = len(nurses)
    T = 3
    slots = [DAY_SLOT, EVE_SLOT, NGT_SLOT]
    nurse_ids = [n.id for n in nurses]
    id_to_idx = {n.id: idx for idx, n in enumerate(nurses)}
    levels = [n.level for n in nurses]
    high_indices = [idx for idx, n in enumerate(nurses) if n.level >= 2]

    # Build demand & min_high matrices
    default_demand = {"D": 2, "E": 2, "N": 2}
    default_min_high = {"D": 0, "E": 0, "N": 0}
    for wc in req.ward_configs:
        default_demand[wc.shift_type] = wc.required_nurses
        default_min_high[wc.shift_type] = wc.min_high

    demand = [[default_demand["D"], default_demand["E"], default_demand["N"]] for _ in range(D)]
    min_high = [[default_min_high["D"], default_min_high["E"], default_min_high["N"]] for _ in range(D)]

    # Unavailability
    unavail_set: set[tuple[int, int]] = set()
    for u in req.unavailability:
        if u.nurse_id in id_to_idx:
            unavail_set.add((id_to_idx[u.nurse_id], u.day))

    # Preference maps (backward compat)
    pref_weekend = [0] * N
    pref_night = [0] * N
    for p in req.preferences:
        if p.nurse_id in id_to_idx:
            idx = id_to_idx[p.nurse_id]
            pref_weekend[idx] = 1 if p.prefers_weekend else 0
            pref_night[idx] = 1 if p.prefers_night else 0

    # Exclusion pairs
    excl_pairs: list[tuple[int, int]] = []
    for e in req.exclusions:
        if e.nurse_id_1 in id_to_idx and e.nurse_id_2 in id_to_idx:
            excl_pairs.append((id_to_idx[e.nurse_id_1], id_to_idx[e.nurse_id_2]))

    days = list(range(1, D + 1))
    nurse_range = list(range(N))

    # Weekend days
    weekend_days: set[int] = set()
    for d in days:
        dow = datetime.date(req.year, req.month + 1, d).weekday()
        if dow >= 5:
            weekend_days.add(d)

    # ── CP-SAT Model ──
    model = cp_model.CpModel()

    x = {(i, d, t): model.new_bool_var(f"x_{i}_{d}_{t}")
         for i in nurse_range for d in days for t in slots}
    work = {(i, d): model.new_bool_var(f"w_{i}_{d}") for i in nurse_range for d in days}
    active = {i: model.new_bool_var(f"a_{i}") for i in nurse_range}

    # ── Hard Constraints ──

    # 1. One shift per day + link work + unavail + active
    for i in nurse_range:
        for d in days:
            model.add(sum(x[(i, d, t)] for t in slots) <= hc.max_shifts_per_day)
            model.add(work[(i, d)] == sum(x[(i, d, t)] for t in slots))
            if (i, d) in unavail_set:
                model.add(work[(i, d)] == 0)
            model.add(work[(i, d)] <= active[i])

    # 2. Demand & skill mix
    for d in days:
        for t_idx, t in enumerate(slots):
            model.add(sum(x[(i, d, t)] for i in nurse_range) >= demand[d - 1][t_idx])
            if high_indices:
                model.add(sum(x[(i, d, t)] for i in high_indices) >= min_high[d - 1][t_idx])

    # 3. Night shifts must come in consecutive pairs
    # If a nurse works a night on day d, either day d-1 or day d+1 must also be night
    for i in nurse_range:
        for d in days:
            if d == 1:
                # First day: if night, then next day must also be night
                model.add(x[(i, d, NGT_SLOT)] <= x[(i, d + 1, NGT_SLOT)])
            elif d == D:
                # Last day: if night, then previous day must also be night
                model.add(x[(i, d, NGT_SLOT)] <= x[(i, d - 1, NGT_SLOT)])
            else:
                # Middle days: if night, at least one neighbor must be night
                model.add(x[(i, d, NGT_SLOT)] <= x[(i, d - 1, NGT_SLOT)] + x[(i, d + 1, NGT_SLOT)])

    # 3b. Limit night blocks to exactly 2 consecutive (no 3+ in a row)
    for i in nurse_range:
        for d in range(1, D - 1):
            model.add(x[(i, d, NGT_SLOT)] + x[(i, d + 1, NGT_SLOT)] + x[(i, d + 2, NGT_SLOT)] <= 2)

    # 4. Night block → days off after (2 mandatory rest days after a night pair)
    for i in nurse_range:
        for d in range(1, D):
            both = model.new_bool_var(f"bN_{i}_{d}")
            model.add(both <= x[(i, d, NGT_SLOT)])
            model.add(both <= x[(i, d + 1, NGT_SLOT)])
            model.add(both >= x[(i, d, NGT_SLOT)] + x[(i, d + 1, NGT_SLOT)] - 1)
            for od in range(d + 2, min(D, d + 1 + hc.days_off_after_night_block) + 1):
                model.add(work[(i, od)] <= 1 - both)

    # 5. Max consecutive workdays
    if hc.max_consecutive_workdays + 1 <= D:
        for i in nurse_range:
            for start in range(1, D - hc.max_consecutive_workdays + 1):
                model.add(sum(work[(i, start + k)] for k in range(hc.max_consecutive_workdays + 1)) <= hc.max_consecutive_workdays)

    # 6. Consecutive trigger → days off
    run = {(i, d): model.new_bool_var(f"run_{i}_{d}") for i in nurse_range for d in days}
    for i in nurse_range:
        for d in days:
            if d < hc.consec_trigger:
                model.add(run[(i, d)] == 0)
            else:
                for k in range(hc.consec_trigger):
                    model.add(run[(i, d)] <= work[(i, d - k)])
                model.add(run[(i, d)] >= sum(work[(i, d - k)] for k in range(hc.consec_trigger)) - (hc.consec_trigger - 1))
            for od in range(d + 1, min(D, d + hc.days_off_after_consec) + 1):
                model.add(work[(i, od)] <= 1 - run[(i, d)])

    # 7. Exclusion pairs
    for (a, b) in excl_pairs:
        for d in days:
            for t in slots:
                model.add(x[(a, d, t)] + x[(b, d, t)] <= 1)

    # ── Objective (×2 scaled) ──
    base_rate = {1: 40, 2: 55, 3: 70, 4: 85, 5: 100}
    night_premium = 12
    fixed_nurse_cost = 200
    w_unpreferred = 30
    w_match_bonus = 12

    obj2 = []

    # Fixed cost per active nurse
    for i in nurse_range:
        obj2.append(2 * fixed_nurse_cost * active[i])

    # Wage costs
    for i in nurse_range:
        base = base_rate.get(levels[i], 40)
        for d in days:
            obj2.append(2 * HOURS_PER_SHIFT * base * x[(i, d, DAY_SLOT)])
            obj2.append(2 * HOURS_PER_SHIFT * base * x[(i, d, EVE_SLOT)])
            obj2.append(2 * HOURS_PER_SHIFT * (base + night_premium) * x[(i, d, NGT_SLOT)])

    # Overtime
    sum_work_var = {i: model.new_int_var(0, D, f"sw_{i}") for i in nurse_range}
    ot = {i: model.new_int_var(0, HOURS_PER_SHIFT * D, f"ot_{i}") for i in nurse_range}
    for i in nurse_range:
        model.add(sum_work_var[i] == sum(work[(i, d)] for d in days))
        hours_var = model.new_int_var(0, HOURS_PER_SHIFT * D, f"hrs_{i}")
        model.add(hours_var == HOURS_PER_SHIFT * sum_work_var[i])
        model.add(ot[i] >= hours_var - 40)
        model.add(ot[i] >= 0)
        base = base_rate.get(levels[i], 40)
        obj2.append(base * ot[i])

    # Legacy preference penalties (backward compat)
    for i in nurse_range:
        lw = pref_weekend[i]
        ln = pref_night[i]
        for d in days:
            if lw != 0:
                coef = -2 * w_match_bonus if (lw == 1) == (d in weekend_days) else 2 * w_unpreferred
                obj2.append(coef * work[(i, d)])
            if ln != 0:
                obj2.append((-2 * (w_match_bonus // 2) if ln == 1 else 2 * w_unpreferred) * x[(i, d, NGT_SLOT)])

    # ── Soft Constraints ──
    for sc in req.soft_constraints:
        tp = sc.constraint_type
        p = sc.params
        w = p.get("weight", 0)

        # Resolve nurse index
        ni = id_to_idx.get(sc.nurse_id) if sc.nurse_id else None

        if tp == "soft_unavail" and ni is not None:
            day_num = p.get("day")
            slot_num = p.get("slot")  # None means all slots
            if day_num and 1 <= day_num <= D:
                if slot_num is None:
                    obj2.append(2 * w * work[(ni, day_num)])
                elif 1 <= slot_num <= T:
                    obj2.append(2 * w * x[(ni, day_num, slot_num)])

        elif tp == "soft_prefer_work" and ni is not None:
            day_num = p.get("day")
            slot_num = p.get("slot")
            if day_num and 1 <= day_num <= D:
                if slot_num is None:
                    nw = model.new_bool_var(f"sc_nw_{ni}_{day_num}")
                    model.add(nw + work[(ni, day_num)] == 1)
                    obj2.append(2 * w * nw)
                elif 1 <= slot_num <= T:
                    ns = model.new_bool_var(f"sc_ns_{ni}_{day_num}_{slot_num}")
                    model.add(ns + x[(ni, day_num, slot_num)] == 1)
                    obj2.append(2 * w * ns)

        elif tp == "soft_prefer_shift" and ni is not None:
            day_num = p.get("day")
            slot_num = p.get("slot")
            if day_num and slot_num and 1 <= day_num <= D and 1 <= slot_num <= T:
                ns = model.new_bool_var(f"sc_nsh_{ni}_{day_num}_{slot_num}")
                model.add(ns + x[(ni, day_num, slot_num)] == 1)
                obj2.append(2 * w * ns)

        elif tp == "prefer_weekend":
            workers = _resolve_workers(p, ni, nurse_range, id_to_idx)
            for wi in workers:
                for d in weekend_days:
                    obj2.append(-2 * w * work[(wi, d)])

        elif tp == "prefer_weekday":
            workers = _resolve_workers(p, ni, nurse_range, id_to_idx)
            for wi in workers:
                for d in days:
                    if d not in weekend_days:
                        obj2.append(-2 * w * work[(wi, d)])

        elif tp == "prefer_night":
            workers = _resolve_workers(p, ni, nurse_range, id_to_idx)
            for wi in workers:
                for d in days:
                    obj2.append(-2 * w * x[(wi, d, NGT_SLOT)])

        elif tp == "avoid_night":
            workers = _resolve_workers(p, ni, nurse_range, id_to_idx)
            for wi in workers:
                for d in days:
                    obj2.append(2 * w * x[(wi, d, NGT_SLOT)])

        elif tp == "soft_max_nights" and ni is not None:
            cap = p.get("max_nights", 2)
            exc = model.new_int_var(0, D, f"sc_exc_{ni}")
            model.add(exc >= sum(x[(ni, d, NGT_SLOT)] for d in days) - cap)
            obj2.append(2 * w * exc)

        elif tp == "maximize_shifts":
            workers = _resolve_workers(p, ni, nurse_range, id_to_idx)
            for wi in workers:
                for d in days:
                    obj2.append(-2 * w * work[(wi, d)])

        elif tp == "level_night_penalty":
            penalties = p.get("penalties", {})
            for wi in nurse_range:
                lvl = levels[wi]
                pen = penalties.get(str(lvl), 0)
                if pen > 0:
                    for d in days:
                        obj2.append(2 * pen * x[(wi, d, NGT_SLOT)])

    model.minimize(sum(obj2))

    # ── No-good cuts for previous solutions ──
    if prev_solutions:
        for prev in prev_solutions:
            ones = []
            for i in nurse_range:
                for d in days:
                    for t in slots:
                        k = (i, d, t)
                        if prev.get(k, 0) == 1:
                            ones.append(x[k])
            if ones:
                model.add(sum(ones) <= len(ones) - 1)

    # ── Solve ──
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = req.time_limit_seconds
    solver.parameters.num_search_workers = 4

    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None, None

    # Extract result
    x_vals = {}
    schedule: dict[str, dict[str, str]] = {}
    for i in nurse_range:
        nid = nurse_ids[i]
        schedule[nid] = {}
        for d in days:
            key = date_key(req.year, req.month, d)
            assigned_slot = None
            for t in slots:
                val = solver.value(x[(i, d, t)])
                x_vals[(i, d, t)] = val
                if val == 1:
                    assigned_slot = SLOT_NAME[t]
            schedule[nid][key] = assigned_slot or "X"

    return schedule, float(solver.objective_value) / 2.0, x_vals


def _resolve_workers(params: dict, single_ni: int | None, nurse_range: list[int], id_to_idx: dict) -> list[int]:
    """Resolve worker list from params or fall back to single nurse index."""
    worker_ids = params.get("workers", [])
    if worker_ids:
        return [id_to_idx[wid] for wid in worker_ids if wid in id_to_idx]
    if single_ni is not None:
        return [single_ni]
    return []


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────
@app.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(req: ScheduleRequest):
    options: list[ScheduleOption] = []
    prev_solutions: list[dict] = []

    for i in range(req.num_options):
        sched, obj_val, x_vals = build_and_solve(req, prev_solutions)
        if sched is None:
            if i == 0:
                raise HTTPException(status_code=422, detail="No feasible schedule found. Check constraints/demand.")
            break
        options.append(ScheduleOption(
            id=f"option-{i + 1}",
            label=f"Option {i + 1}",
            schedule=sched,
            objective_value=obj_val,
        ))
        prev_solutions.append(x_vals)

    return ScheduleResponse(options=options)


@app.get("/health")
async def health():
    return {"status": "ok"}
