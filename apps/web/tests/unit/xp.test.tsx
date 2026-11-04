import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import XpBurst, { fireXp, XP_LESSON, XP_TASK } from "@/components/shared/XpBurst";

// jsdom cannot run the library's exit animation, so its parts are plain elements here: what is under test
// is when a chip is added and when it is taken away, not how it moves.
vi.mock("framer-motion", async () => {
  const React = await import("react");

  return {
    AnimatePresence: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
    motion: {
      div: ({ children, className }: { children: React.ReactNode; className?: string }) =>
        React.createElement("div", { className }, children),
    },
    useReducedMotion: () => false,
  };
});

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("XpBurst", () => {
  it("awards what the server awards", () => {
    // These must match XP_LESSON_COMPLETED and XP_TASK_COMPLETED in apps/api/app/services/gamification_service.py.
    expect(XP_LESSON).toBe(10);
    expect(XP_TASK).toBe(25);
  });

  it("shows the amount when XP is earned, and takes it away again", () => {
    render(<XpBurst />);

    act(() => fireXp(25));

    expect(screen.getByText("+25 XP")).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(2500));

    expect(screen.queryByText("+25 XP")).not.toBeInTheDocument();
  });

  it("shows two awards at once, one under the other", () => {
    render(<XpBurst />);

    act(() => {
      fireXp(10);
      fireXp(25);
    });

    expect(screen.getByText("+10 XP")).toBeInTheDocument();
    expect(screen.getByText("+25 XP")).toBeInTheDocument();
  });

  it("is a polite live region, so screen readers hear it", () => {
    render(<XpBurst />);

    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "polite");
  });

  it("does nothing until something is earned", () => {
    render(<XpBurst />);

    expect(screen.queryByText(/XP/)).not.toBeInTheDocument();
  });
});
