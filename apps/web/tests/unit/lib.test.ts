import { describe, expect, it } from "vitest";

import { formatDate, formatNumber, intlLocale } from "@/lib/format";
import { flattenUnits } from "@/lib/units";
import type { Roadmap } from "@/types/roadmap";

describe("format", () => {
  it("uses a fixed timezone so server and browser print the same date", () => {
    expect(formatDate("2026-10-31T23:30:00Z")).toBe("Oct 31, 2026");
  });

  it("writes Roman Urdu with English forms, not Urdu-script ones", () => {
    expect(intlLocale("ur-Latn")).toBe("en-GB");
    expect(intlLocale("ur")).toBe("ur");
  });

  it("groups digits by the language", () => {
    expect(formatNumber(12345)).toBe("12,345");
  });
});

describe("flattenUnits", () => {
  const unit = (id: string, day: number, order: number) => ({ id, day, order }) as never;
  const roadmap = {
    id: "r1",
    title: "Road",
    status: "active",
    phases: [
      {
        title: "Second phase",
        order: 2,
        tasks: [{ id: "t3", title: "Late", order: 1, learning_units: [unit("u5", 1, 1)] }],
      },
      {
        title: "First phase",
        order: 1,
        tasks: [
          { id: "t2", title: "B", order: 2, learning_units: [unit("u3", 1, 1)] },
          { id: "t1", title: "A", order: 1, learning_units: [unit("u2", 2, 1), unit("u1", 1, 2), unit("u0", 1, 1)] },
        ],
      },
    ],
  } as unknown as Roadmap;

  it("lists lessons in the order a learner meets them: phase, task, day, position", () => {
    expect(flattenUnits([roadmap]).map((c) => c.unit.id)).toEqual(["u0", "u1", "u2", "u3", "u5"]);
  });

  it("carries where each lesson lives", () => {
    const first = flattenUnits([roadmap])[0];
    expect(first).toMatchObject({ roadmapId: "r1", taskId: "t1", phaseTitle: "First phase" });
  });

  it("copes with a roadmap that has no phases", () => {
    expect(flattenUnits([{ id: "r", title: "x", status: "active" } as unknown as Roadmap])).toEqual([]);
  });
});
