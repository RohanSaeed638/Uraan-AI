import { act, render, screen } from "@testing-library/react";
import { Bell } from "lucide-react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Illustration from "@/components/illustrations/Illustration";
import RoadmapBuilding from "@/components/roadmap/RoadmapBuilding";
import EmptyState from "@/components/shared/EmptyState";
import en from "@/messages/en.json";
import { renderWithIntl } from "./helpers";

/** next/image rewrites `src` to `/_next/image?url=<encoded path>&...`, so compare the decoded url. */
function sources(container: HTMLElement) {
  return Array.from(container.querySelectorAll("img")).map((img) => {
    const src = img.getAttribute("src") ?? "";
    const url = new URL(src, "http://localhost").searchParams.get("url");

    return url ?? src;
  });
}

describe("Illustration", () => {
  it("renders a light and a dark version of the picture", () => {
    const { container } = render(<Illustration name="bell" />);

    expect(sources(container)).toEqual(["/illustrations/bell.light.webp", "/illustrations/bell.dark.webp"]);
  });

  it("is hidden from screen readers and has no alt text", () => {
    const { container } = render(<Illustration name="trophy" />);

    expect(container.firstElementChild).toHaveAttribute("aria-hidden", "true");
    for (const img of Array.from(container.querySelectorAll("img"))) {
      expect(img).toHaveAttribute("alt", "");
    }
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("is sized by the size prop and takes extra classes", () => {
    const { container } = render(<Illustration name="path" size={96} className="hidden sm:block" />);
    const box = container.firstElementChild as HTMLElement;

    expect(box.style.width).toBe("96px");
    expect(box.style.height).toBe("96px");
    expect(box).toHaveClass("hidden", "sm:block");
  });

  it("shows only the matching version for each theme", () => {
    const { container } = render(<Illustration name="flame" />);
    const [light, dark] = Array.from(container.querySelectorAll("img"));

    expect(light).toHaveClass("dark:hidden");
    expect(dark).toHaveClass("hidden", "dark:block");
  });
});

describe("EmptyState", () => {
  it("shows the picture instead of the icon when art is given", () => {
    const { container } = render(<EmptyState icon={Bell} art="bell" title="All caught up" text="Nothing new." />);

    expect(sources(container)[0]).toBe("/illustrations/bell.light.webp");
    expect(container.querySelector("svg")).toBeNull();
    expect(screen.getByText("All caught up")).toBeInTheDocument();
    expect(screen.getByText("Nothing new.")).toBeInTheDocument();
  });

  it("falls back to the icon without art", () => {
    const { container } = render(<EmptyState icon={Bell} title="All caught up" />);

    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("svg")).not.toBeNull();
  });

  it("renders an action when given", () => {
    render(<EmptyState title="Nothing here" action={<button>Add one</button>} />);

    expect(screen.getByRole("button", { name: "Add one" })).toBeInTheDocument();
  });
});

describe("RoadmapBuilding", () => {
  const steps = en.onboarding.generating;

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("announces progress as a status with the default title", () => {
    renderWithIntl(<RoadmapBuilding />);

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: steps.title })).toBeInTheDocument();
  });

  it("uses a custom title when given", () => {
    renderWithIntl(<RoadmapBuilding compact title="Generate your roadmap" />);

    expect(screen.getByRole("heading", { name: "Generate your roadmap" })).toBeInTheDocument();
  });

  it("lists every step, with the first one current", () => {
    renderWithIntl(<RoadmapBuilding />);

    for (const key of ["s1", "s2", "s3", "s4", "s5"] as const) {
      expect(screen.getByText(steps[key])).toBeInTheDocument();
    }
    expect(screen.getByText(steps.s1)).toHaveClass("font-medium");
    expect(screen.getByText(steps.s2)).not.toHaveClass("font-medium");
  });

  it("moves on to the next step over time and stays on the last one", () => {
    renderWithIntl(<RoadmapBuilding />);

    act(() => {
      vi.advanceTimersByTime(7000);
    });
    expect(screen.getByText(steps.s2)).toHaveClass("font-medium");
    expect(screen.getByText(steps.s1)).not.toHaveClass("font-medium");

    act(() => {
      vi.advanceTimersByTime(7000 * 10);
    });
    expect(screen.getByText(steps.s5)).toHaveClass("font-medium");
  });
});
