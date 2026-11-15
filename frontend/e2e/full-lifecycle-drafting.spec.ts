import { test, expect } from "@playwright/test";

test.describe("Full Legal Drafting Lifecycle E2E", () => {
  test("complete path: login+MFA -> create party/property -> generate -> review -> finalise -> download", async ({
    page,
    context,
  }) => {
    const tenantId = "0193132e-504f-7a1b-8000-000000000001";
    const documentId = "0193132e-504f-7a1b-8000-000000000099";
    const jobId = "0193132e-504f-7a1b-8000-000000000088";
    const csrfToken = "derived-hmac-csrf-token-lifecycle-e2e";

    // 1. Mock Authentication: Step 1 (Password) -> MFA Pending -> Step 2 (MFA Verify)
    await page.route("**/api/v1/auth/login", async (route) => {
      const body = JSON.parse(route.request().postData() || "{}");
      if (body.email === "drafter@lekhan.local" && body.password === "ValidPassword123!") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            mfa_required: true,
            message: "Two-step MFA required. Please enter 6-digit TOTP code.",
          }),
        });
      } else {
        await route.fulfill({ status: 401, body: JSON.stringify({ detail: "Invalid credentials" }) });
      }
    });

    await page.route("**/api/v1/auth/mfa/verify", async (route) => {
      const body = JSON.parse(route.request().postData() || "{}");
      if (body.code === "123456") {
        await context.addCookies([
          {
            name: "lekhan_session",
            value: "full_authenticated_session_cookie",
            domain: "localhost",
            path: "/",
            httpOnly: true,
            sameSite: "Lax",
          },
        ]);
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            status: "ok",
            user: {
              id: "0193132e-504f-7a1b-8000-000000000002",
              tenant_id: tenantId,
              email: "drafter@lekhan.local",
              role: "drafter",
            },
            csrf_token: csrfToken,
          }),
        });
      } else {
        await route.fulfill({ status: 401, body: JSON.stringify({ detail: "Invalid MFA code" }) });
      }
    });

    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: {
            id: "0193132e-504f-7a1b-8000-000000000002",
            tenant_id: tenantId,
            email: "drafter@lekhan.local",
            role: "drafter",
          },
          csrf_token: csrfToken,
        }),
      });
    });

    // 2. Mock Party Creation (bilingual names per AGENTS.md Hard Rule 1)
    await page.route("**/api/v1/parties", async (route) => {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "0193132e-504f-7a1b-8000-000000000010",
          name_en: "Ramchandra Joshi",
          name_mr: "रामचंद्र जोशी",
          category: "individual",
          pan: "ABCDE1234F",
        }),
      });
    });

    // 3. Mock Property Creation
    await page.route("**/api/v1/properties", async (route) => {
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "0193132e-504f-7a1b-8000-000000000020",
          survey_number: "45/2",
          village: "Wadi",
          district: "Nagpur",
          area_sqft: 1500,
        }),
      });
    });

    // 4. Mock Document Generation (Async: returns 202 + job id)
    await page.route("**/api/v1/documents", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 202,
          contentType: "application/json",
          body: JSON.stringify({
            job_id: jobId,
            status: "queued",
            state: "REQUESTED",
            document_id: documentId,
            download_url: `/api/v1/documents/${documentId}/download`,
            pdf_url: `/api/v1/documents/${documentId}/pdf`,
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ items: [], total: 0, limit: 50, offset: 0 }),
        });
      }
    });

    // Mock Job Status Polling
    await page.route(`**/api/v1/jobs/${jobId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: jobId,
          status: "succeeded",
          state: "COMPLETED",
          document_id: documentId,
          attempts: 1,
          outputs: { docx: true, pdf: true },
          download_url: `/api/v1/documents/${documentId}/download`,
          pdf_url: `/api/v1/documents/${documentId}/pdf`,
        }),
      });
    });

    // 5. Mock Review & Finalise
    await page.route(`**/api/v1/documents/${documentId}/review`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "reviewed",
          doc_id: documentId,
          reviewer: "advocate.reviewer@lekhan.local",
          checklist: { parties_verified: true, property_boundaries_checked: true },
        }),
      });
    });

    await page.route(`**/api/v1/documents/${documentId}/finalise`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "finalised",
          doc_id: documentId,
        }),
      });
    });

    // 6. Mock Downloads (DOCX Master and PDF Convenience Copy)
    await page.route(`**/api/v1/documents/${documentId}/download`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers: {
          "Content-Disposition": 'attachment; filename="Draft_DOC_2026_001.docx"',
          "X-Lekhan-Master-Format": "docx",
        },
        body: Buffer.from("PK\x03\x04synthetic_docx_master_stream"),
      });
    });

    await page.route(`**/api/v1/documents/${documentId}/pdf`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/pdf",
        headers: {
          "Content-Disposition": 'attachment; filename="Convenience_Copy_DOC_2026_001.pdf"',
          "X-Lekhan-Document-Type": "convenience-copy",
        },
        body: Buffer.from("%PDF-1.4 synthetic convenience copy"),
      });
    });

    // --- Execute E2E Flow ---
    await page.goto("/");

    // Execute typed API client lifecycle through the frontend application context
    const lifecycleResult = await page.evaluate(async () => {
      const { api, apiClient, setMemoryCsrfToken } = await import("../src/shared/api");

      // A. Login with password -> triggers MFA pending
      const loginRes = await apiClient<{ mfa_required: boolean }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: "drafter@lekhan.local", password: "ValidPassword123!" }),
      });

      // B. Complete MFA step with TOTP code -> establishes session + CSRF token
      const mfaRes = await apiClient<{ status: string; csrf_token: string }>("/api/v1/auth/mfa/verify", {
        method: "POST",
        body: JSON.stringify({ code: "123456" }),
      });
      setMemoryCsrfToken(mfaRes.csrf_token);

      // C. Create Party
      const party = await api.createParty({
        name_en: "Ramchandra Joshi",
        name_mr: "रामचंद्र जोशी",
        category: "individual",
        pan: "ABCDE1234F",
      });

      // D. Create Property
      const property = await api.createProperty({
        survey_number: "45/2",
        village: "Wadi",
        district: "Nagpur",
        area_sqft: 1500,
      });

      // E. Generate Document (Async 202)
      const genJob = await api.generateDocument({
        template_id: "sale_deed_plot_mr",
        party_id: party.id,
        property_id: property.id,
      });

      // F. Poll Job Status
      const jobStatus = await api.getJob(genJob.job_id);

      // G. Review Document
      const reviewRes = await api.markReviewed(jobStatus.document_id!, {
        parties_verified: true,
        property_boundaries_checked: true,
      });

      // H. Finalise Document
      const finaliseRes = await api.finaliseDocument(jobStatus.document_id!);

      return {
        mfaStatus: mfaRes.status,
        partyId: party.id,
        propertyId: property.id,
        jobId: genJob.job_id,
        jobStatus: jobStatus.status,
        documentId: jobStatus.document_id,
        reviewStatus: reviewRes.status,
        finaliseStatus: finaliseRes.status,
      };
    });

    // Verify assertions across the full path
    expect(lifecycleResult.mfaStatus).toBe("ok");
    expect(lifecycleResult.partyId).toBe("0193132e-504f-7a1b-8000-000000000010");
    expect(lifecycleResult.propertyId).toBe("0193132e-504f-7a1b-8000-000000000020");
    expect(lifecycleResult.jobStatus).toBe("succeeded");
    expect(lifecycleResult.reviewStatus).toBe("reviewed");
    expect(lifecycleResult.finaliseStatus).toBe("finalised");

    // I. Verify Master DOCX and PDF Downloads
    const docxResponse = await context.request.get(`/api/v1/documents/${documentId}/download`);
    expect(docxResponse.status()).toBe(200);
    expect(docxResponse.headers()["content-type"]).toContain("wordprocessingml.document");

    const pdfResponse = await context.request.get(`/api/v1/documents/${documentId}/pdf`);
    expect(pdfResponse.status()).toBe(200);
    expect(pdfResponse.headers()["content-type"]).toContain("application/pdf");
  });
});
