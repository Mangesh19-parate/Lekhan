import { test, expect } from "@playwright/test";

test.describe("DraftingWorkspace Generation, Validation & Polling E2E", () => {
  const tenantId = "0193132e-504f-7a1b-8000-000000000001";
  const userId = "0193132e-504f-7a1b-8000-000000000002";
  const csrfToken = "derived-hmac-csrf-token-drafting-e2e";
  const documentId = "0193132e-504f-7a1b-8000-000000000099";
  const jobId = "0193132e-504f-7a1b-8000-000000000088";

  test.beforeEach(async ({ context, page }) => {
    // 1. Setup authenticated session
    await context.addCookies([
      {
        name: "lekhan_session",
        value: "active_drafting_session_token",
        domain: "localhost",
        path: "/",
        httpOnly: true,
        sameSite: "Lax",
      },
    ]);

    // 2. Set initial view to new_draft and clear existing draft form data in localStorage
    await page.addInitScript(() => {
      localStorage.setItem("lekhan_current_view", "new_draft");
      localStorage.removeItem("lekhan_current_form");
      localStorage.removeItem("lekhan_current_repeaters");
    });

    // 3. Mock Auth /me
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: userId,
            tenant_id: tenantId,
            email: "drafter@lekhan.local",
            display_name: "Advocate Drafter",
            role: "drafter",
            ui_language: "mr",
          },
          csrf_token: csrfToken,
        }),
      });
    });
  });

  test("blocks submission and shows field-level errors when required fields are empty", async ({ page }) => {
    let validateCalled = false;
    let documentsCalled = false;

    await page.route("**/api/v1/documents/validate/*", async (route) => {
      validateCalled = true;
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: true, violations: [] }) });
    });

    await page.route("**/api/v1/documents", async (route) => {
      if (route.request().method() === "POST") {
        documentsCalled = true;
        await route.fulfill({ status: 202, body: JSON.stringify({ job_id: jobId }) });
      }
    });

    await page.goto("/");

    // Click submit button directly on empty form
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // Verify submission is blocked
    expect(validateCalled).toBe(false);
    expect(documentsCalled).toBe(false);

    // Assert field-level error messages are shown
    const errorAlerts = page.locator('.has-error, [role="alert"]');
    await expect(errorAlerts.first()).toBeVisible();
  });

  test("fills form, validates, generates, polls progress (REQUESTED -> RENDERED -> VERIFIED -> DONE), and downloads DOCX", async ({ page }) => {
    let validateReceivedData: any = null;
    let documentsReceivedPayload: any = null;
    let pollCount = 0;

    // 1. Mock Validation endpoint
    await page.route("**/api/v1/documents/validate/*", async (route) => {
      validateReceivedData = JSON.parse(route.request().postData() || "{}");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          valid: true,
          derived_fields: {
            "financial.balance_amount": 2000000,
            "property.area_sqft": 1614.59,
          },
          violations: [],
          visibility: {},
        }),
      });
    });

    // 2. Mock Document Creation (Async 202)
    await page.route("**/api/v1/documents", async (route) => {
      if (route.request().method() === "POST") {
        documentsReceivedPayload = JSON.parse(route.request().postData() || "{}");
        await route.fulfill({
          status: 202,
          contentType: "application/json",
          body: JSON.stringify({
            job_id: jobId,
            status: "queued",
            state: "REQUESTED",
            document_id: documentId,
            download_url: `/api/v1/documents/${documentId}/download`,
          }),
        });
      } else {
        await route.fulfill({ status: 200, body: JSON.stringify({ items: [] }) });
      }
    });

    // 3. Mock Polling GET /api/v1/jobs/{jobId}
    // Simulates the exact state progression: REQUESTED -> RENDERED -> VERIFIED -> DONE
    await page.route(`**/api/v1/jobs/${jobId}`, async (route) => {
      pollCount++;
      if (pollCount === 1) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: jobId,
            status: "running",
            state: "RENDERED",
            attempts: 1,
            outputs: { docx: false, pdf: false },
          }),
        });
      } else if (pollCount === 2) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: jobId,
            status: "running",
            state: "VERIFIED",
            attempts: 1,
            outputs: { docx: false, pdf: false },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: jobId,
            status: "succeeded",
            state: "COMPLETED",
            document_id: documentId,
            attempts: 1,
            outputs: { docx: true, pdf: false },
            download_url: `/api/v1/documents/${documentId}/download`,
          }),
        });
      }
    });

    // 4. Mock DOCX Download
    await page.route(`**/api/v1/documents/${documentId}/download`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers: {
          "Content-Disposition": `attachment; filename="sale_deed_plot_mr_${documentId}.docx"`,
        },
        body: Buffer.from("PK\x03\x04synthetic docx content test"),
      });
    });

    await page.goto("/");

    // Click "Load Sample" to fill all required fields and repeaters
    const loadSampleBtn = page.getByRole("button", { name: /नमुना भरला|Load Sample/i });
    await expect(loadSampleBtn).toBeVisible();
    await loadSampleBtn.click();

    // Start download waiting and click Generate
    const downloadPromise = page.waitForEvent("download");
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();

    // Verify progress UI modal appears and shows timeline
    const progressTimeline = page.locator('[data-testid="generation-progress-timeline"]');
    await expect(progressTimeline).toBeVisible();

    // Assert the DOCX download triggers and succeeds
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain(".docx");
    expect(download.suggestedFilename()).toContain("sale_deed_plot_mr");

    // Verify validate was called before /documents
    expect(validateReceivedData).not.toBeNull();
    expect(validateReceivedData.data).toBeDefined();

    // Verify /documents payload has actual form values and NO hardcoded fallbacks
    expect(documentsReceivedPayload).not.toBeNull();
    expect(documentsReceivedPayload.template_id).toBe("sale_deed_plot_mr");
    expect(documentsReceivedPayload.property_details.mouza).toContain("सोनेगाव");
    expect(documentsReceivedPayload.financial.total_consideration).toBe(2500000);
    expect(documentsReceivedPayload.financial.earnest_advance).toBe(500000);

    // Verify Progress UI shows Done
    const doneStep = page.locator('[data-testid="progress-step-done"]');
    await expect(doneStep).toHaveAttribute("data-step-status", "completed");
  });

  test("shows error code and Retry button on job failure, and retrying recovers", async ({ page }) => {
    let failFirstAttempt = true;

    await page.route("**/api/v1/documents/validate/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ valid: true, violations: [] }),
      });
    });

    await page.route("**/api/v1/documents", async (route) => {
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({ job_id: jobId, status: "queued", state: "REQUESTED", document_id: documentId }),
      });
    });

    await page.route(`**/api/v1/jobs/${jobId}`, async (route) => {
      if (failFirstAttempt) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: jobId,
            status: "failed",
            state: "RENDERED",
            error: {
              code: "TEMPLATE_TAG_ERROR",
              message: "Unrendered Jinja tag detected in template",
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: jobId,
            status: "succeeded",
            state: "COMPLETED",
            document_id: documentId,
            download_url: `/api/v1/documents/${documentId}/download`,
          }),
        });
      }
    });

    await page.route(`**/api/v1/documents/${documentId}/download`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers: {
          "Content-Disposition": `attachment; filename="sale_deed_plot_mr_${documentId}.docx"`,
        },
        body: Buffer.from("PK\x03\x04recovered docx content"),
      });
    });

    await page.goto("/");

    // Load sample
    await page.getByRole("button", { name: /नमुना भरला|Load Sample/i }).click();

    // Click submit
    await page.locator('button[type="submit"]').click();

    // Verify error code is shown in failure banner
    const errorCodeEl = page.locator('[data-testid="job-error-code"]');
    await expect(errorCodeEl).toBeVisible();
    await expect(errorCodeEl).toHaveText("TEMPLATE_TAG_ERROR");

    // Verify Retry button is visible
    const retryBtn = page.locator('[data-testid="job-retry-button"]');
    await expect(retryBtn).toBeVisible();

    // Now allow second attempt to succeed and click Retry
    failFirstAttempt = false;
    const downloadPromise = page.waitForEvent("download");
    await retryBtn.click();

    // Assert download occurs on retry success
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain(".docx");
  });
});
