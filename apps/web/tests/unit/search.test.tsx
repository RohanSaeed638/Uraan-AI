import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import GlobalSearch from "@/components/dashboard/GlobalSearch";
import type { SearchHit } from "@/lib/api/search";
import { renderWithIntl } from "./helpers";

const push = vi.fn();
const searchAll = vi.fn<(q: string) => Promise<SearchHit[]>>();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }), usePathname: () => "/dashboard" }));
vi.mock("next/link", () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));
vi.mock("@/lib/api/search", () => ({ searchAll: (q: string) => searchAll(q) }));

const hit = (kind: SearchHit["kind"], title: string, url: string, subtitle: string | null = null): SearchHit => ({
  kind,
  id: `${kind}-${title}`,
  title,
  subtitle,
  url,
});

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const user = userEvent.setup();

  renderWithIntl(
    <QueryClientProvider client={client}>
      <GlobalSearch />
    </QueryClientProvider>
  );

  return { user, box: screen.getByRole("combobox") };
}

beforeEach(() => {
  push.mockReset();
  searchAll.mockReset();
});

describe("GlobalSearch", () => {
  it("does not search for a single letter", async () => {
    const { user, box } = setup();
    await user.type(box, "b");
    await new Promise((r) => setTimeout(r, 400));

    expect(searchAll).not.toHaveBeenCalled();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("shows results under their group headings once the person pauses", async () => {
    searchAll.mockResolvedValue([
      hit("roadmap", "Backend Engineer Roadmap", "/roadmaps/1", "active"),
      hit("career", "Backend Developer", "/careers/backend-developer", "Software"),
    ]);
    const { user, box } = setup();
    await user.type(box, "backend");

    expect(await screen.findByText("Roadmaps")).toBeInTheDocument();
    expect(screen.getByText("Careers")).toBeInTheDocument();
    expect(screen.getAllByRole("option")).toHaveLength(2);
    expect(searchAll).toHaveBeenCalledTimes(1);
    expect(searchAll).toHaveBeenCalledWith("backend");
  });

  it("opens a result when it is clicked, then closes and clears", async () => {
    searchAll.mockResolvedValue([hit("lesson", "HTTP basics", "/roadmaps/1/task/2/learn/3", "Learn the web")]);
    const { user, box } = setup();
    await user.type(box, "http");
    await user.click(await screen.findByRole("option", { name: /HTTP basics/ }));

    expect(push).toHaveBeenCalledWith("/roadmaps/1/task/2/learn/3");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(box).toHaveValue("");
  });

  it("works from the keyboard: arrow down, then Enter", async () => {
    searchAll.mockResolvedValue([
      hit("task", "Learn HTTP", "/roadmaps/1/task/2"),
      hit("lesson", "HTTP verbs", "/roadmaps/1/task/2/learn/3"),
    ]);
    const { user, box } = setup();
    await user.type(box, "http");
    await screen.findAllByRole("option");
    await user.keyboard("{ArrowDown}{ArrowDown}");

    expect(box.getAttribute("aria-activedescendant")).toMatch(/-1$/);

    await user.keyboard("{Enter}");

    expect(push).toHaveBeenCalledWith("/roadmaps/1/task/2/learn/3");
  });

  it("wraps around at both ends of the list", async () => {
    searchAll.mockResolvedValue([hit("task", "One http", "/a"), hit("task", "Two http", "/b")]);
    const { user, box } = setup();
    await user.type(box, "http");
    await screen.findAllByRole("option");
    await user.keyboard("{ArrowUp}");

    expect(box.getAttribute("aria-activedescendant")).toMatch(/-1$/); // from nothing, up goes to the last

    await user.keyboard("{ArrowDown}");

    expect(box.getAttribute("aria-activedescendant")).toMatch(/-0$/); // down from the last goes to the first
  });

  it("offers the app's own pages by name, without asking the server", async () => {
    searchAll.mockResolvedValue([]);
    const { user, box } = setup();
    await user.type(box, "calend");
    // The matched letters are wrapped in <mark>, so match on the text, not the accessible name.
    const option = await screen.findByRole("option");

    expect(option).toHaveTextContent("Calendar");
    expect(screen.getByText("Pages")).toBeInTheDocument();

    await user.click(option);

    expect(push).toHaveBeenCalledWith("/calendar");
  });

  it("says so when nothing matches", async () => {
    searchAll.mockResolvedValue([]);
    const { user, box } = setup();
    await user.type(box, "zzzqq");

    expect(await screen.findByText(/No results for/)).toBeInTheDocument();
  });

  it("says so when the search itself fails", async () => {
    searchAll.mockRejectedValue(new Error("network"));
    const { user, box } = setup();
    await user.type(box, "python");

    expect(await screen.findByText(/Search is not available/)).toBeInTheDocument();
  });

  it("Escape closes the list and the clear button empties the box", async () => {
    searchAll.mockResolvedValue([hit("task", "Learn Python", "/p")]);
    const { user, box } = setup();
    await user.type(box, "python");
    await screen.findByRole("listbox");
    await user.keyboard("{Escape}");

    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Clear search" }));

    expect(box).toHaveValue("");
  });

  it("highlights the part of the title that matched", async () => {
    searchAll.mockResolvedValue([hit("task", "Learn Python Basics", "/p")]);
    const { user, box } = setup();
    await user.type(box, "python");
    await screen.findByRole("option");

    await waitFor(() => expect(document.querySelector("mark")?.textContent).toBe("Python"));
  });

  it("is announced as a search combobox", () => {
    const { box } = setup();

    expect(screen.getByRole("search")).toBeInTheDocument();
    expect(box).toHaveAttribute("aria-expanded", "false");
    expect(box).toHaveAttribute("aria-autocomplete", "list");
  });
});
