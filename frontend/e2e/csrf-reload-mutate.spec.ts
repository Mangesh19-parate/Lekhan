import { test, expect } from "@playwright/test";

test.describe("CSRF In-Memory Token & Reload-Then-Mutate E2E", () => {
  test("refetches CSRF from /me on load into memory without localStorage and succeeds on mutation", async ({
    page,
    context,
  }) => {
    // 1. Mock or execute authentication
    let csrfTokenValue = "derived-hmac-csrf-token-12345";

    await context.addCookies([
      {
        name: "lekhan_session",
        value: "active_test_session_token",
        domain: "localhost",
        path: "/",
        httpOnly: true,
        sameSite: "Lax",
      },
    ]);

    // Mock GET /api/v1/auth/me returning profile + derived CSRF token
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: "0193132e-504f-7a1b-8000-000000000002",
            tenant_id: "0193132e-504f-7a1b-8000-000000000001",
            email: "drafter@lekhan.local",
            display_name: "Advocate Drafter",
            role: "drafter",
            ui_language: "mr",
          },
          csrf_token: csrfTokenValue,
        }),
      });
    });

    let mutationReceivedHeader: string | null = null;
    // Intercept mutation request
    await page.route("**/api/v1/parties/detect-duplicates", async (route) => {
      mutationReceivedHeader = route.request().headers()["x-csrf-token"] || null;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ duplicates: [] }),
      });
    });

    // 2. Initial page load
    await page.goto("/");

    // 3. Page Reload (Simulating browser refresh)
    await page.reload();

    // 4. Verify localStorage has NO CSRF token
    const storedCsrf = await page.evaluate(() => localStorage.getItem("lekhan_csrf_token"));
    expect(storedCsrf).toBeNull();

    // 5. Trigger a mutation via the frontend API client
    const mutationResponse = await page.evaluate(async () => {
      // Dynamic import of the in-memory API client
      const { apiClient, getMemoryCsrfToken } = await import("../src/shared/api");
      const inMemoryToken = getMemoryCsrfToken();
      const res = await apiClient("/api/v1/parties/detect-duplicates", {
        method: "POST",
        body: JSON.stringify({ name: "Ramesh Patil" }),
      });
      return { res, inMemoryToken };
    });

    // 6. Assertions
    expect(mutationResponse.inMemoryToken).toBe(csrfTokenValue);
    expect(mutationReceivedHeader).toBe(csrfTokenValue);
  });
});
