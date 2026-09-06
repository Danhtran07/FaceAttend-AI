import { describe, expect, it } from "vitest";

import { getCalendarCellCount, shiftMonth } from "./attendanceCalendar";

describe("attendance calendar helpers", () => {
  it("creates complete Monday-first calendar rows", () => {
    expect(getCalendarCellCount(2026, 9)).toBe(35);
    expect(getCalendarCellCount(2026, 2)).toBe(35);
  });

  it("moves across year boundaries", () => {
    expect(shiftMonth(2026, 1, -1)).toEqual({ year: 2025, month: 12 });
    expect(shiftMonth(2026, 12, 1)).toEqual({ year: 2027, month: 1 });
  });
});