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
    # 1-indexed day-of-month employment window, inclusive. None = unrestricted.
    # Set for temp nurses, and for anyone joining or leaving mid-month.
    available_from_day: Optional[int] = None
    available_until_day: Optional[int] = None
    # A temp costs more per hour and more to engage at all.
    is_temp: bool = False
    # A temp the solver invented for a what-if variant, with no database row.
    # Only phantoms count against max_active_phantoms.
    is_phantom: bool = False


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
    # Cap on how many invented temps may actually be used. The phantom pool is
    # deliberately larger than this, one per seniority level, so the solver picks
    # both how many temps and which levels rather than being told.
    max_active_phantoms: Optional[int] = None
    temp_fixed_cost: int = 1500
    temp_rate_multiplier: float = 1.5


class ScheduleOption(BaseModel):
    id: str
    label: str
    schedule: dict[str, dict[str, str]]
    objective_value: Optional[float] = None
    # Which temps this particular option hires. Two options for the same temp
    # budget can hire different people, so this has to be per option, not per
    # variant - the grid rows and the apply step both read it.
    temps: list["TempSummary"] = []


class ScheduleResponse(BaseModel):
    options: list[ScheduleOption]


class TempSummary(BaseModel):
    """A temp the solver actually used - in effect, the hiring spec."""
    id: str
    name: str
    level: int
    shift_count: int
    dates: list[str]


class TempVariant(BaseModel):
    temp_count: int
    status: str  # "feasible" | "infeasible" | "no_solution_found"
    options: list[ScheduleOption] = []
    temps: list[TempSummary] = []


ScheduleOption.model_rebuild()


class TempVariantRequest(ScheduleRequest):
    # Ascending. Each count is solved separately and presented in order.
    temp_counts: list[int] = [1, 2, 3]
    options_per_count: int = 1


class TempVariantResponse(BaseModel):
    """Smallest workable number of temps, plus a variant per count tried."""
    min_feasible_count: Optional[int] = None
    variants: list[TempVariant] = []


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

    # Employment windows, precomputed so the inner loop stays two comparisons.
    # A nurse with no window is treated as available all month.
    win_lo = [n.available_from_day if n.available_from_day is not None else 1 for n in nurses]
    win_hi = [n.available_until_day if n.available_until_day is not None else D for n in nurses]

    # ── Hard Constraints ──

    # 1. One shift per day + link work + unavail + window + active
    #
    # Pinning work to 0 is enough to cover all three slots, because work is
    # defined as the sum of the slot vars on the line above. Every other
    # constraint and objective term for that nurse-day is then multiplied by a
    # variable that is already zero, so nothing else needs a window check.
    for i in nurse_range:
        for d in days:
            model.add(sum(x[(i, d, t)] for t in slots) <= hc.max_shifts_per_day)
            model.add(work[(i, d)] == sum(x[(i, d, t)] for t in slots))
            if (i, d) in unavail_set or not (win_lo[i] <= d <= win_hi[i]):
                model.add(work[(i, d)] == 0)
            model.add(work[(i, d)] <= active[i])

    # 1b. Phantom temps: cap how many may be used, and make `active` exact for
    # them. Elsewhere active is only an upper bound, which is harmless when it
    # merely carries a cost - but here it is being counted, so an idle phantom
    # must be forced inactive or it would consume one of the k slots.
    phantom_indices = [i for i in nurse_range if nurses[i].is_phantom]
    if phantom_indices:
        for i in phantom_indices:
            model.add(active[i] <= sum(work[(i, d)] for d in days))
        if req.max_active_phantoms is not None:
            model.add(sum(active[i] for i in phantom_indices) <= req.max_active_phantoms)
        # Identical phantoms at the same level are interchangeable, which makes
        # the search waste time on permutations of the same schedule. Ordering
        # them within a level removes that symmetry.
        by_level: dict[int, list[int]] = {}
        for i in phantom_indices:
            by_level.setdefault(levels[i], []).append(i)
        for group in by_level.values():
            for a, b in zip(group, group[1:]):
                model.add(active[a] >= active[b])

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

    # Fixed cost per active nurse. A temp is more expensive to engage at all,
    # which is what makes the solver reach for one only when it has to - and
    # prefer the cheapest seniority that still works.
    for i in nurse_range:
        engage = req.temp_fixed_cost if nurses[i].is_temp else fixed_nurse_cost
        obj2.append(2 * engage * active[i])

    # Wage costs
    for i in nurse_range:
        base = base_rate.get(levels[i], 40)
        if nurses[i].is_temp:
            base = int(base * req.temp_rate_multiplier)
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
        if nurses[i].is_temp:
            base = int(base * req.temp_rate_multiplier)
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
    solver.parameters.num_search_workers = 4
    # Stop early once provably within 2% of optimal (rarely provable here,
    # but free when it is).
    solver.parameters.relative_gap_limit = 0.02
    # Fast pass: 3 seconds finds essentially the same schedules the full
    # budget does (measured 1-2.5% on the internal objective; the app
    # rescores client-side so this number is never shown). The rest of the
    # old 10-second budget went to an optimality proof that never finishes,
    # which made a 3-option generation take 30 seconds. If the fast pass
    # finds nothing and infeasibility is NOT proven (status UNKNOWN), retry
    # once with the caller's full budget so hard instances cannot falsely
    # report "no feasible schedule".
    fast_limit = min(req.time_limit_seconds, 3.0)
    solver.parameters.max_time_in_seconds = fast_limit
    status = solver.solve(model)
    if (status not in (cp_model.OPTIMAL, cp_model.FEASIBLE)
            and status != cp_model.INFEASIBLE
            and fast_limit < req.time_limit_seconds):
        solver.parameters.max_time_in_seconds = req.time_limit_seconds
        status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # Return the status so the caller can tell "provably impossible" from
        # "ran out of time". The two need different advice: only genuine
        # infeasibility justifies offering to hire temp nurses.
        return None, None, None, status

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

    return schedule, float(solver.objective_value) / 2.0, x_vals, status


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
def infeasible_detail(status) -> dict:
    """Structured failure detail so the client can branch on the cause.

    "infeasible" means the solver proved no schedule exists under these hard
    constraints, which is the only case where hiring temp nurses is the right
    suggestion. "no_solution_found" means the search ran out of time, where the
    right suggestion is a longer budget.
    """
    proven = status == cp_model.INFEASIBLE
    return {
        "code": "infeasible" if proven else "no_solution_found",
        "message": ("No feasible schedule found. Check constraints/demand."
                    if proven else
                    "The solver ran out of time before finding a schedule."),
    }


@app.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(req: ScheduleRequest):
    options: list[ScheduleOption] = []
    prev_solutions: list[dict] = []

    for i in range(req.num_options):
        sched, obj_val, x_vals, status = build_and_solve(req, prev_solutions)
        if sched is None:
            if i == 0:
                raise HTTPException(status_code=422, detail=infeasible_detail(status))
            break
        options.append(ScheduleOption(
            id=f"option-{i + 1}",
            label=f"Option {i + 1}",
            schedule=sched,
            objective_value=obj_val,
        ))
        prev_solutions.append(x_vals)

    return ScheduleResponse(options=options)


# One phantom per seniority level per slot, so the solver answers "how many
# temps" and "which seniority" together. Fixing the level would be worse than
# guessing: a level-1-only pool can report that even three temps cannot work
# when a single senior temp would have covered the seniority floor.
PHANTOM_LEVELS = [1, 2, 3, 4, 5]


def _with_phantoms(req: TempVariantRequest, k: int) -> ScheduleRequest:
    """The same ward and rules, plus a pool of invented temps capped at k."""
    extras = [
        NurseInput(
            id=f"__temp_{level}_{j + 1}__",
            name=f"Temp {level}.{j + 1}",
            level=level,
            is_temp=True,
            is_phantom=True,
        )
        for level in PHANTOM_LEVELS
        for j in range(k)
    ]
    return ScheduleRequest(
        **{**req.model_dump(exclude={"temp_counts", "options_per_count", "nurses"}),
           "nurses": list(req.nurses) + extras,
           "num_options": req.options_per_count,
           "max_active_phantoms": k}
    )


def _summarize_temps(sub: ScheduleRequest, schedule: dict) -> list[TempSummary]:
    """The phantoms that actually got shifts - in effect, who to hire.

    Also drops the idle phantoms from `schedule` in place. The pool is
    deliberately larger than the cap, so most of it goes unused, and an unused
    phantom is not a hire: it should not appear as an empty row in the grid, and
    its placeholder id must never reach the apply step, which resolves ids to
    real nurses.
    """
    out: list[TempSummary] = []
    for n in sub.nurses:
        if not n.is_phantom:
            continue
        worked = sorted(d for d, v in schedule.get(n.id, {}).items() if v != "X")
        if not worked:
            schedule.pop(n.id, None)
            continue
        out.append(TempSummary(id=n.id, name=n.name, level=n.level,
                               shift_count=len(worked), dates=worked))
    return out


@app.post("/generate-temp-variants", response_model=TempVariantResponse)
async def generate_temp_variants(req: TempVariantRequest):
    """Schedules that become possible if temp nurses are hired.

    Offered when the permanent staff cannot cover the month. Feasibility is
    monotone in headcount here - demand is a lower bound, engaging a nurse is
    optional, and every per-nurse rule is an upper bound, so a spare nurse can
    always be given no shifts. The first count that works is therefore the
    minimum.

    Every requested count is still solved, because the manager is choosing
    between them, not just looking for the smallest. The cap is an upper bound,
    so a variant may use fewer temps than it was allowed - "3 allowed, 2 used"
    is a real answer, and a more honest one than padding a third temp with a
    token shift to fill the quota.
    """
    variants: list[TempVariant] = []
    min_feasible: Optional[int] = None

    for k in sorted(set(req.temp_counts)):
        sub = _with_phantoms(req, k)
        options: list[ScheduleOption] = []
        temps: list[TempSummary] = []
        prev_solutions: list[dict] = []
        status_label = "infeasible"

        for i in range(max(1, sub.num_options)):
            sched, obj_val, x_vals, status = build_and_solve(sub, prev_solutions)
            if sched is None:
                if i == 0:
                    status_label = ("infeasible" if status == cp_model.INFEASIBLE
                                    else "no_solution_found")
                break
            status_label = "feasible"
            used = _summarize_temps(sub, sched)  # also prunes idle phantom rows
            if i == 0:
                temps = used
            options.append(ScheduleOption(
                id=f"temp{k}-option-{i + 1}",
                label=f"{k} temp · Option {i + 1}",
                schedule=sched,
                objective_value=obj_val,
                temps=used,
            ))
            prev_solutions.append(x_vals)

        variants.append(TempVariant(temp_count=k, status=status_label,
                                    options=options, temps=temps))

        if status_label == "feasible" and min_feasible is None:
            min_feasible = k

    return TempVariantResponse(min_feasible_count=min_feasible, variants=variants)


@app.get("/health")
async def health():
    return {"status": "ok"}
