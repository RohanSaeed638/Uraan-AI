import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ActivityHeatmap from "@/components/shared/ActivityHeatmap";
import Pill from "@/components/shared/Pill";
import { renderWithIntl } from "./helpers";

let pathname = "/dashboard";

vi.mock("next/navigation", () => ({ usePathname: () => pathname }));
vi.mock("next/link", () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

describe("BottomNav", () => {
  it("lists the five everyday places and marks the current one", async () => {
    const { default: BottomNav } = await import("@/components/dashboard/BottomNav");
    pathname = "/roadmaps/abc";
    renderWithIntl(<BottomNav />);

    const links = screen.getAllByRole("link");
    expect(links.map((l) => l.getAttribute("href"))).toEqual([
      "/dashboard",
      "/roadmaps",
      "/calendar",
      "/mentor",
      "/progress",
    ]);
    expect(screen.getByRole("link", { name: /my roadmaps/i })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: /dashboard/i })).not.toHaveAttribute("aria-current");
  });
});

describe("ActivityHeatmap", () => {
  const today = new Date(Date.UTC(2026, 9, 31)); // Saturday 31 October 2026

  it("draws one square per past day, 18 weeks wide, and none for days still to come", () => {
    render(<ActivityHeatmap days={[]} label="summary" dayLabel={(d, c) => `${d}:${c}`} today={today} />);

    const squares = document.querySelectorAll("[title]");
    // 18 weeks x 7 days = 126 cells; today is the last cell of the last week (a Saturday).
    expect(squares).toHaveLength(126);
    expect(screen.getByRole("img", { name: "summary" })).toBeInTheDocument();
  });

  it("shades a busy day and describes it in its tooltip", () => {
    render(
      <ActivityHeatmap
        days={[{ date: "2026-10-31", count: 5, xp: 40 }]}
        label="summary"
        dayLabel={(d, c) => `${d}:${c}`}
        today={today}
      />
    );

    const busy = document.querySelector('[title="2026-10-31:5"]');
    expect(busy).not.toBeNull();
    expect(busy?.className).toContain("bg-brand-violet/75");
  });

  it("leaves out days that have not happened yet", () => {
    const wednesday = new Date(Date.UTC(2026, 9, 28));
    render(<ActivityHeatmap days={[]} label="s" dayLabel={(d) => d} today={wednesday} />);

    // Sunday to Wednesday of the last week exist; Thursday to Saturday do not.
    expect(document.querySelector('[title="2026-10-29"]')).toBeNull();
    expect(document.querySelector('[title="2026-10-28"]')).not.toBeNull();
  });
});

describe("Pill", () => {
  it("shows its text", () => {
    render(<Pill>Beginner</Pill>);
    expect(screen.getByText("Beginner")).toBeInTheDocument();
  });
});
