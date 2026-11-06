import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LessonFeedback from "@/components/lessons/LessonFeedback";
import { FEEDBACK_REASONS, type LessonFeedback as Vote } from "@/lib/api/feedback";
import en from "@/messages/en.json";
import { renderWithIntl } from "./helpers";

const getFeedback = vi.fn<(id: string) => Promise<Vote | null>>();
const saveFeedback = vi.fn();
const toastError = vi.fn();

vi.mock("@/lib/api/feedback", async (original) => ({
  ...(await original<typeof import("@/lib/api/feedback")>()),
  getLessonFeedback: (id: string) => getFeedback(id),
  saveLessonFeedback: (id: string, body: unknown) => saveFeedback(id, body),
}));
vi.mock("sonner", () => ({ toast: { error: (m: string) => toastError(m), success: vi.fn() } }));

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  renderWithIntl(
    <QueryClientProvider client={client}>
      <LessonFeedback unitId="unit-1" />
    </QueryClientProvider>
  );

  return userEvent.setup();
}

beforeEach(() => {
  getFeedback.mockReset().mockResolvedValue(null);
  saveFeedback.mockReset();
  toastError.mockReset();
});

describe("LessonFeedback", () => {
  it("asks the question and offers yes and no", async () => {
    setup();

    expect(await screen.findByText("Was this lesson helpful?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Yes" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "No" })).toBeInTheDocument();
  });

  it("saves a yes at once and says thanks", async () => {
    saveFeedback.mockResolvedValue({ helpful: true, reason: null, comment: null });
    const user = setup();
    await user.click(await screen.findByRole("button", { name: "Yes" }));

    expect(saveFeedback).toHaveBeenCalledWith("unit-1", { helpful: true });
    expect(await screen.findByText(/Thanks, that helps/)).toBeInTheDocument();
  });

  it("saves a no at once, then lets the learner say what was wrong", async () => {
    saveFeedback
      .mockResolvedValueOnce({ helpful: false, reason: null, comment: null })
      .mockResolvedValueOnce({ helpful: false, reason: "wrong", comment: "The table is wrong" });
    const user = setup();
    await user.click(await screen.findByRole("button", { name: "No" }));

    expect(saveFeedback).toHaveBeenNthCalledWith(1, "unit-1", { helpful: false }); // never lost, even if they stop here
    expect(await screen.findByText("What went wrong?")).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "Something is wrong" }));
    await user.type(screen.getByPlaceholderText("Tell us more (optional)"), "  The table is wrong ");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(saveFeedback).toHaveBeenNthCalledWith(2, "unit-1", { helpful: false, reason: "wrong", comment: "The table is wrong" });
    expect(await screen.findByText(/Thanks for the details/)).toBeInTheDocument();
  });

  it("will not send an empty detail form, but lets the learner skip it", async () => {
    saveFeedback.mockResolvedValue({ helpful: false, reason: null, comment: null });
    const user = setup();
    await user.click(await screen.findByRole("button", { name: "No" }));

    expect(await screen.findByRole("button", { name: "Send" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Skip" }));

    expect(await screen.findByText(/Thanks for the details/)).toBeInTheDocument();
  });

  it("shows an earlier vote instead of asking again, and lets it be changed", async () => {
    getFeedback.mockResolvedValue({ helpful: true, reason: null, comment: null });
    saveFeedback.mockResolvedValue({ helpful: false, reason: null, comment: null });
    const user = setup();

    expect(await screen.findByText(/Thanks, that helps/)).toBeInTheDocument();
    expect(screen.queryByText("Was this lesson helpful?")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Change my answer" }));

    expect(saveFeedback).toHaveBeenCalledWith("unit-1", { helpful: false });
    expect(await screen.findByText("What went wrong?")).toBeInTheDocument();
  });

  it("tells the learner when the answer could not be saved", async () => {
    saveFeedback.mockRejectedValue(new Error("offline"));
    const user = setup();
    await user.click(await screen.findByRole("button", { name: "Yes" }));

    await waitFor(() => expect(toastError).toHaveBeenCalledWith(en.feedback.failed));
    expect(screen.getByRole("button", { name: "Yes" })).toBeEnabled(); // and they can try again
  });

  it("offers every reason the server accepts, with a label for each", () => {
    expect(Object.keys(en.feedback.reasons).sort()).toEqual([...FEEDBACK_REASONS].sort());
    expect(Object.keys(en.admin.insights.reasons).sort()).toEqual([...FEEDBACK_REASONS].sort());
  });
});
