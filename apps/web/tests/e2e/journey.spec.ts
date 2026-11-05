import { expect, test, type APIRequestContext } from "@playwright/test";

const API = `${(process.env.E2E_API_URL ?? "http://localhost:8000").replace(/\/+$/, "")}/api/v1`;
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";
const EMAIL = process.env.E2E_EMAIL ?? "";
const PASSWORD = process.env.E2E_PASSWORD ?? "";

test.skip(!EMAIL || !PASSWORD, "Set E2E_EMAIL and E2E_PASSWORD (a confirmed account) to run the journey.");

// A new account cannot be confirmed without opening its email, so the journey starts
// from a confirmed test account. The first half is done through the screens; creating
// the roadmap goes through the API (it is the slow, AI-heavy step) and the screens then
// check what the learner would see.
async function tokenFor(request: APIRequestContext) {
  const res = await request.post(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    headers: { apikey: SUPABASE_KEY },
    data: { email: EMAIL, password: PASSWORD },
  });
  expect(res.ok()).toBeTruthy();
  return (await res.json()).access_token as string;
}

test("sign in, onboarding done, roadmap, lesson, sign out", async ({ page, request }) => {
  const token = await tokenFor(request);
  const auth = { Authorization: `Bearer ${token}` };

  // The account must have finished onboarding before it can use the app.
  const profile = await request.put(`${API}/profile/me`, {
    headers: auth,
    data: {
      full_name: "E2E Learner",
      language: "en",
      career_slug: "backend-engineer",
      skill_level: "beginner",
      daily_hours: 1,
      target_duration: 3,
      learning_style: "reading",
      onboarding_completed: true,
    },
  });
  expect(profile.ok()).toBeTruthy();

  // Sign in through the form.
  await page.goto("/login");
  await page.getByLabel("Email address").fill(EMAIL);
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "Sign In" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  // Build a roadmap and wait for it (a real AI call).
  const started = await request.post(`${API}/roadmaps/generate`, {
    headers: auth,
    data: {
      career_slug: "backend-engineer",
      career_stage: "beginner",
      skill_level: "beginner",
      learning_goal: "get my first job",
      learning_style: "reading",
      daily_hours: 1,
      target_duration: 3,
    },
  });
  expect(started.status()).toBe(202);
  const { id } = await started.json();

  await expect
    .poll(async () => (await (await request.get(`${API}/roadmaps/${id}/status`, { headers: auth })).json()).status, {
      timeout: 180_000,
      intervals: [3000],
    })
    .toBe("active");

  // The roadmap shows up with its phases.
  await page.goto(`/roadmaps/${id}`);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const detail = await (await request.get(`${API}/roadmaps/${id}`, { headers: auth })).json();
  const task = detail.phases[0].tasks[0];

  // Open the first task: the plan appears quickly and lessons fill in behind it.
  await request.post(`${API}/tasks/${task.id}/learning-plan`, { headers: auth });
  await page.goto(`/roadmaps/${id}/task/${task.id}`);
  const lessonLinks = page.locator(`a[href*="/task/${task.id}/learn/"]`);
  await expect(lessonLinks.first()).toBeVisible({ timeout: 60_000 });

  // Open a lesson and read it.
  await lessonLinks.first().click();
  await expect(page).toHaveURL(/\/learn\//);
  await expect
    .poll(async () => (await page.getByRole("main").innerText()).length, { timeout: 120_000 })
    .toBeGreaterThan(500);

  // Sign out from the account menu.
  await page.getByRole("button", { name: /E2E Learner|Student/ }).click();
  await page.getByRole("menuitem", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/(login)?$/);

  // Signed out, the app is closed again.
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
});

test("public pages are reachable without signing in", async ({ page }) => {
  for (const path of ["/", "/about", "/pricing", "/login", "/register"]) {
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(200);
    await expect(page.locator("main")).toHaveCount(1);
  }

  const missing = await page.goto("/this-page-does-not-exist");
  expect(missing?.status()).toBe(404);
  await expect(page.getByText("off the roadmap")).toBeVisible();
});
