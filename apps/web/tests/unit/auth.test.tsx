import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResendConfirmation from "@/components/auth/ResendConfirmation";
import { registerSchema } from "@/lib/validations/auth";
import { formatTime } from "@/lib/planner";
import { renderWithIntl } from "./helpers";

const resend = vi.fn();
const toastError = vi.fn();
const toastSuccess = vi.fn();

vi.mock("@/services/auth/auth", () => ({ authService: { resendConfirmation: (e: string) => resend(e) } }));
vi.mock("sonner", () => ({ toast: { error: (m: string) => toastError(m), success: (m: string) => toastSuccess(m) } }));

beforeEach(() => {
  resend.mockReset();
  toastError.mockReset();
  toastSuccess.mockReset();
});

describe("ResendConfirmation", () => {
  it("sends the email again for the address, then makes the person wait", async () => {
    resend.mockResolvedValue({ error: null });
    renderWithIntl(<ResendConfirmation email="sana@example.com" />);
    await userEvent.click(screen.getByRole("button", { name: "Resend confirmation email" }));

    expect(resend).toHaveBeenCalledWith("sana@example.com");
    await waitFor(() => expect(toastSuccess).toHaveBeenCalled());
    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.getByRole("button")).toHaveTextContent(/Resend in \d+s/);
  });

  it("tells the person when they are going too fast, and waits too", async () => {
    resend.mockResolvedValue({ error: { message: "email rate limit exceeded" } });
    renderWithIntl(<ResendConfirmation email="sana@example.com" />);
    await userEvent.click(screen.getByRole("button"));

    await waitFor(() => expect(toastError).toHaveBeenCalledWith(expect.stringContaining("Too many attempts")));
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("shows a plain error and stays usable when sending fails", async () => {
    resend.mockRejectedValue(new Error("offline"));
    renderWithIntl(<ResendConfirmation email="sana@example.com" />);
    await userEvent.click(screen.getByRole("button"));

    await waitFor(() => expect(toastError).toHaveBeenCalled());
    expect(screen.getByRole("button")).toBeEnabled();
  });
});

describe("sign-up form rules", () => {
  const valid = {
    email: "sana@example.com",
    password: "longenough1",
    confirmPassword: "longenough1",
    fullName: "Sana Khan",
  };

  it("requires agreeing to the Terms and Privacy Policy", () => {
    const refused = registerSchema.safeParse({ ...valid, agree: false });

    expect(refused.success).toBe(false);
    expect(refused.error?.issues[0].message).toBe("mustAgree");
    expect(registerSchema.safeParse({ ...valid, agree: true }).success).toBe(true);
  });

  it("still checks that the two passwords match", () => {
    const result = registerSchema.safeParse({ ...valid, confirmPassword: "different1", agree: true });

    expect(result.success).toBe(false);
  });
});

describe("clock times", () => {
  it("uses an ordinary space before AM/PM, so the server and the browser print the same text", () => {
    const text = formatTime("19:05:00", "en");

    expect(text).toBe("7:05 PM");
    expect(text).not.toMatch(/[  ]/);
  });
});
