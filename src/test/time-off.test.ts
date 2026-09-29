import { describe, it, expect } from "vitest";
import { datesInRange } from "@/hooks/useDayOffRequests";
import { buildTimeOffMap } from "@/lib/time-off";

describe("datesInRange", () => {
  it("returns the range inclusive of both ends", () => {
    expect(datesInRange("2026-10-01", "2026-10-03")).toEqual([
      "2026-10-01", "2026-10-02", "2026-10-03",
    ]);
  });

  it("returns a single date when start equals end", () => {
    expect(datesInRange("2026-10-05", "2026-10-05")).toEqual(["2026-10-05"]);
  });

  it("does not shift dates east of UTC", () => {
    // The old implementation parsed local midnight and serialized in UTC, so in
    // Asia/Seoul every approved day off landed a day early. The app ships a
    // Korean locale, so this is the case that mattered.
    const prev = process.env.TZ;
    process.env.TZ = "Asia/Seoul";
    try {
      expect(datesInRange("2026-10-01", "2026-10-02")).toEqual(["2026-10-01", "2026-10-02"]);
    } finally {
      process.env.TZ = prev;
    }
  });

  it("crosses a month boundary", () => {
    expect(datesInRange("2026-10-30", "2026-11-01")).toEqual([
      "2026-10-30", "2026-10-31", "2026-11-01",
    ]);
  });

  it("returns nothing when the end precedes the start", () => {
    expect(datesInRange("2026-10-05", "2026-10-01")).toEqual([]);
  });

  it("caps a runaway range", () => {
    expect(datesInRange("2026-01-01", "2030-01-01").length).toBe(62);
  });
});

describe("buildTimeOffMap", () => {
  const year = 2026;
  const month = 9; // October

  it("marks a pending request as pending, with caps at each end", () => {
    const map = buildTimeOffMap(
      [{ nurse_id: "n1", start_date: "2026-10-05", end_date: "2026-10-07", status: "pending" }],
      [],
      year,
      month
    );
    expect(map["n1:2026-10-05"]).toEqual({ status: "pending", isStart: true, isEnd: false });
    expect(map["n1:2026-10-06"]).toEqual({ status: "pending", isStart: false, isEnd: false });
    expect(map["n1:2026-10-07"]).toEqual({ status: "pending", isStart: false, isEnd: true });
    expect(map["n1:2026-10-08"]).toBeUndefined();
  });

  it("marks approved days as approved", () => {
    const map = buildTimeOffMap([], [{ nurse_id: "n1", date: "2026-10-10" }], year, month);
    expect(map["n1:2026-10-10"]).toEqual({ status: "approved", isStart: true, isEnd: true });
  });

  it("lets a recorded decision override a stale pending request", () => {
    const map = buildTimeOffMap(
      [{ nurse_id: "n1", start_date: "2026-10-05", end_date: "2026-10-06", status: "pending" }],
      [{ nurse_id: "n1", date: "2026-10-05" }],
      year,
      month
    );
    expect(map["n1:2026-10-05"].status).toBe("approved");
    expect(map["n1:2026-10-06"].status).toBe("pending");
    // Different statuses, so each day caps its own run rather than merging.
    expect(map["n1:2026-10-05"].isEnd).toBe(true);
    expect(map["n1:2026-10-06"].isStart).toBe(true);
  });

  it("ignores requests that are already decided", () => {
    const map = buildTimeOffMap(
      [
        { nurse_id: "n1", start_date: "2026-10-05", end_date: "2026-10-05", status: "denied" },
        { nurse_id: "n1", start_date: "2026-10-06", end_date: "2026-10-06", status: "approved" },
      ],
      [],
      year,
      month
    );
    expect(map["n1:2026-10-05"]).toBeUndefined();
    expect(map["n1:2026-10-06"]).toBeUndefined();
  });

  it("clips a request that starts before the month", () => {
    const map = buildTimeOffMap(
      [{ nurse_id: "n1", start_date: "2026-09-28", end_date: "2026-10-02", status: "pending" }],
      [],
      year,
      month
    );
    expect(map["n1:2026-10-01"]).toBeDefined();
    // Day 1 continues a run that began in September, so it is not a start cap.
    expect(map["n1:2026-10-01"].isStart).toBe(false);
    expect(map["n1:2026-10-02"].isEnd).toBe(true);
  });

  it("keeps nurses separate", () => {
    const map = buildTimeOffMap(
      [{ nurse_id: "n1", start_date: "2026-10-05", end_date: "2026-10-05", status: "pending" }],
      [{ nurse_id: "n2", date: "2026-10-05" }],
      year,
      month
    );
    expect(map["n1:2026-10-05"].status).toBe("pending");
    expect(map["n2:2026-10-05"].status).toBe("approved");
  });
});
