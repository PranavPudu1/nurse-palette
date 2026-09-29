import { dateKey, getDaysInMonth } from "./scheduler-data";

export type TimeOffStatus = "pending" | "approved";

export interface TimeOffMarker {
  status: TimeOffStatus;
  /** First day of this run, so only this cell draws the left cap. */
  isStart: boolean;
  /** Last day of this run, so only this cell draws the right cap. */
  isEnd: boolean;
}

/** Keyed `${nurseId}:${date}`, matching the shape buildViolationMap produces. */
export type TimeOffMap = Record<string, TimeOffMarker>;

interface RequestLike {
  nurse_id: string;
  start_date: string;
  end_date: string;
  status: string;
}

interface UnavailLike {
  nurse_id: string;
  date: string;
}

/**
 * Which days each nurse is off, and whether that is settled.
 *
 * A pending request draws a dotted line and an approved day off a solid one, so
 * the schedule itself shows who has asked for what without the manager needing
 * to hold a second screen in their head. Approved wins where both apply: once a
 * decision is recorded there is nothing pending about it.
 *
 * Runs are marked per cell rather than measured in pixels because the grid's
 * day columns are min-width, not fixed width.
 */
export function buildTimeOffMap(
  requests: RequestLike[],
  approvedDays: UnavailLike[],
  year: number,
  month: number
): TimeOffMap {
  const status = new Map<string, TimeOffStatus>();

  for (const r of requests) {
    if (r.status !== "pending") continue;
    for (const date of isoRange(r.start_date, r.end_date)) {
      status.set(`${r.nurse_id}:${date}`, "pending");
    }
  }

  // Applied after the pending pass so a decided day overrides a stale request.
  for (const u of approvedDays) {
    status.set(`${u.nurse_id}:${u.date}`, "approved");
  }

  const days = getDaysInMonth(year, month);
  const nurseIds = new Set<string>([
    ...requests.map((r) => r.nurse_id),
    ...approvedDays.map((u) => u.nurse_id),
  ]);

  const map: TimeOffMap = {};
  for (const nurseId of nurseIds) {
    for (let d = 1; d <= days; d++) {
      const date = dateKey(year, month, d);
      const key = `${nurseId}:${date}`;
      const here = status.get(key);
      if (!here) continue;
      // Neighbours are the real adjacent calendar days, not just days inside the
      // displayed month. A range spanning a month boundary should read as
      // continuing off the edge rather than starting on the 1st.
      const before = status.get(`${nurseId}:${shiftDate(date, -1)}`);
      const after = status.get(`${nurseId}:${shiftDate(date, 1)}`);
      map[key] = {
        status: here,
        isStart: before !== here,
        isEnd: after !== here,
      };
    }
  }
  return map;
}

/** The ISO date `delta` days from `iso`, in UTC. */
function shiftDate(iso: string, delta: number): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  d.setUTCDate(d.getUTCDate() + delta);
  return d.toISOString().slice(0, 10);
}

/** Inclusive ISO date range, in UTC, capped so a bad row cannot hang the grid. */
function isoRange(start: string, end: string): string[] {
  const out: string[] = [];
  const a = /^(\d{4})-(\d{2})-(\d{2})/.exec(start);
  const b = /^(\d{4})-(\d{2})-(\d{2})/.exec(end);
  if (!a || !b) return out;
  const d = new Date(Date.UTC(+a[1], +a[2] - 1, +a[3]));
  const stop = new Date(Date.UTC(+b[1], +b[2] - 1, +b[3]));
  while (d.getTime() <= stop.getTime() && out.length < 400) {
    out.push(d.toISOString().slice(0, 10));
    d.setUTCDate(d.getUTCDate() + 1);
  }
  return out;
}
