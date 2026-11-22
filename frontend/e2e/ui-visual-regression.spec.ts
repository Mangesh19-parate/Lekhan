import { test, expect } from "@playwright/test";

test.describe("UI & Visual Regression Suite (DESIGN.md Tokens, Dark Mode, Responsive, Stepper Wizard)", () => {
  const tenantId = "0193132e-504f-7a1b-8000-000000000001";
  const userId = "0193132e-504f-7a1b-8000-000000000002";
  const csrfToken = "test-csrf-token-visual-e2e";

  test.beforeEach(async ({ context, page }) => {
    // 1. Mock session cookie
    await context.addCookies([
      {
        name: "lekhan_session",
        value: "active_visual_session_token",
        domain: "localhost",
        path: "/",
        httpOnly: true,
        sameSite: "Lax",
      },
    ]);

    // 2. Set default initial view and theme
    await page.addInitScript(() => {
      localStorage.setItem("lekhan_current_view", "overview");
      localStorage.setItem("lekhan_theme", "light");
      localStorage.setItem("lekhan_language", "en");
    });

    // 3. Mock Auth & Core APIs
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: userId,
            tenant_id: tenantId,
            email: "advocate@lekhan.local",
            display_name: "Senior Advocate V. Deshmukh",
            role: "advocate",
            is_active: true,
          },
          tenant: {
            id: tenantId,
            name: "Vidarbha Legal Chambers",
            slug: "vidarbha-legal",
          },
          csrf_token: csrfToken,
        }),
      });
    });

    await page.route("**/api/v1/dashboard/stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          drafts_in_progress: 14,
          pending_reviews: 5,
          finalised_documents: 42,
          approved_templates: 67,
          operational_alerts: [],
          language_distribution: { mr: 28, en: 14 },
        }),
      });
    });

    await page.route("**/api/v1/documents*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: "doc-001",
              doc_no: "NGP/2026/SD-0042",
              template_id: "sale_deed_plot_mr",
              status: "finalised",
              language: "mr",
              created_at: "2026-11-15T10:30:00Z",
              docx_download_url: "/api/v1/documents/doc-001/docx",
              pdf_download_url: "/api/v1/documents/doc-001/pdf",
            },
            {
              id: "doc-002",
              doc_no: "NGP/2026/GPA-0019",
              template_id: "general_poa_mr",
              status: "reviewed",
              language: "mr",
              created_at: "2026-11-16T14:15:00Z",
              docx_download_url: "/api/v1/documents/doc-002/docx",
              pdf_download_url: "/api/v1/documents/doc-002/pdf",
            },
            {
              id: "doc-003",
              doc_no: "NGP/2026/GFT-0008",
              template_id: "gift_deed_mr",
              status: "draft",
              language: "en",
              created_at: "2026-11-17T09:00:00Z",
              docx_download_url: "/api/v1/documents/doc-003/docx",
              pdf_download_url: "/api/v1/documents/doc-003/pdf",
            },
          ],
          total: 3,
          page: 1,
          size: 10,
        }),
      });
    });
  });

  test("1. Responsive Viewport Check: Mobile 360px down-scaling", async ({ page }) => {
    // Set 360px viewport as requested
    await page.setViewportSize({ width: 360, height: 740 });
    await page.goto("/");

    // Verify main navigation header exists and hamburger menu is visible
    const hamburgerBtn = page.locator('button[aria-label="Open navigation menu"]');
    await expect(hamburgerBtn).toBeVisible();

    // Verify sidebar starts collapsed / off-screen on mobile
    const aside = page.locator("aside");
    await expect(aside).toHaveClass(/-translate-x-full/);

    // Open hamburger menu
    await hamburgerBtn.click();
    await expect(aside).toHaveClass(/translate-x-0/);

    // Verify backdrop is visible
    const backdrop = page.locator(".lekhan-sidebar-backdrop");
    await expect(backdrop).toBeVisible();

    // Close menu by clicking backdrop
    await backdrop.click();
    await expect(aside).toHaveClass(/-translate-x-full/);
  });

  test("2. Dark Mode Toggle & CSS Variable Verification", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    // Check light theme initial state
    const html = page.locator("html");
    await expect(html).toHaveAttribute("data-theme", "light");

    // Click theme toggle button
    const themeBtn = page.locator('button[aria-label="Toggle theme"]');
    await themeBtn.click();

    // Verify data-theme switches to dark
    await expect(html).toHaveAttribute("data-theme", "dark");

    // Verify localStorage persists dark mode
    const storedTheme = await page.evaluate(() => localStorage.getItem("lekhan_theme"));
    expect(storedTheme).toBe("dark");

    // Toggle back to light
    await themeBtn.click();
    await expect(html).toHaveAttribute("data-theme", "light");
  });

  test("3. Trilingual Switcher (Marathi <-> English <-> Hindi) and Typography Check", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    // Default English text check
    await expect(page.locator("text=Chamber Overview")).toBeVisible();

    // Click Marathi language switch
    const mrBtn = page.getByRole("button", { name: "मराठी" });
    await mrBtn.click();

    // Verify Marathi text is rendered
    await expect(page.locator("text=दफ्तर आढावा")).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", "mr");

    // Click Hindi language switch
    const hiBtn = page.getByRole("button", { name: "हिन्दी" });
    await hiBtn.click();

    // Verify Hindi text is rendered
    await expect(page.locator("html")).toHaveAttribute("lang", "hi");

    // Verify zero letter spacing on Devanagari in computed styles
    const bodyStyles = await page.evaluate(() => {
      const el = document.body;
      return window.getComputedStyle(el).letterSpacing;
    });
    // In CSS :lang(mr), :lang(hi) letter-spacing is 0
    expect(["normal", "0px"]).toContain(bodyStyles);
  });

  test("4. Command Palette Keyboard Shortcut (Ctrl+K / ⌘K)", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    // Trigger Command Palette with keyboard shortcut
    await page.keyboard.press("Control+K");

    // Command palette dialog should become visible
    const palette = page.getByRole("dialog");
    await expect(palette).toBeVisible();

    // Type search query
    const searchInput = palette.locator("input");
    await searchInput.fill("Gift Deed");

    // Press Escape to dismiss
    await page.keyboard.press("Escape");
    await expect(palette).not.toBeVisible();
  });

  test("5. Dashboard Analytics & Charts Rendering", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    // Verify the documents per day chart container
    await expect(page.locator("text=Documents Generated per Day")).toBeVisible();

    // Verify the bilingual language distribution ring
    await expect(page.locator("text=Language Distribution")).toBeVisible();
    await expect(page.locator("text=Marathi (मराठी)")).toBeVisible();
    await expect(page.locator("text=English")).toBeVisible();

    // Verify document lifecycle status breakdown
    await expect(page.locator("text=Document Lifecycle Status")).toBeVisible();
  });

  test("6. Stepper Wizard Workflow & Live Document Preview Pane", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    // Navigate to Stepper Wizard
    await page.getByRole("button", { name: /मसुदा सहाय्यक|Drafting Wizard/i }).click();

    // Step 1: Select Language
    await expect(page.locator("text=Select Language")).toBeVisible();
    await page.locator("text=मराठी (Devanagari)").click();
    await page.getByRole("button", { name: /Next|पुढे/i }).click();

    // Step 2: Select Property Category
    await expect(page.locator("text=Property Category")).toBeVisible();
    await page.locator("text=Plot / Land").click();
    await page.getByRole("button", { name: /Next|पुढे/i }).click();

    // Step 3: Select Deed Template
    await expect(page.locator("text=Select Deed Template")).toBeVisible();
    await page.locator("text=Sale Deed (Plot)").click();

    // Verify Live Document Preview Pane is updated
    const previewPane = page.locator(".bg-canvas.border");
    await expect(previewPane).toBeVisible();
    await expect(previewPane.locator("text=खरेदीखत (Sale Deed)")).toBeVisible();
    await expect(previewPane.locator("text=वैधानिक सूचना (Statutory Notice)")).toBeVisible();
  });

  test("7. Sortable & Paginated Table Interactions", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    // Navigate to Document Register
    await page.getByRole("button", { name: /Deed Register|दस्तऐवज नोंदवही/i }).click();

    // Verify table columns exist
    await expect(page.locator("text=Document Number")).toBeVisible();
    await expect(page.locator("text=Status")).toBeVisible();
    await expect(page.locator("text=Generated Date")).toBeVisible();

    // Sort by Document Number
    const docNoHeader = page.locator("th", { hasText: "Document Number" });
    await docNoHeader.click();

    // Test filter search
    const filterInput = page.getByPlaceholder(/Filter deeds in register/i);
    if (await filterInput.isVisible()) {
      await filterInput.fill("NGP/2026");
    }

    // Verify rows are rendered
    await expect(page.locator("text=NGP/2026/SD-0042")).toBeVisible();
  });

  test("8. Keyboard Accessibility: Skip-to-content Link", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/");

    // Press Tab to focus the skip-to-content link
    await page.keyboard.press("Tab");

    const skipLink = page.locator("a[href='#main-content']");
    await expect(skipLink).toBeFocused();
    await expect(skipLink).toHaveText("Skip to main content");
  });
});
