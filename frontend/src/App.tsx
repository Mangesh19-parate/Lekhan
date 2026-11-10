import React, { useState } from "react";
import { I18nProvider, useI18n } from "./shared/i18n";
import { DynamicForm } from "./features/form_engine/DynamicForm";
import { defaultManifest } from "./features/form_engine/sampleManifest";
import { FileCheck } from "lucide-react";

const AppContent: React.FC = () => {
  const { lang, setLang } = useI18n();
  const [submitting, setSubmitting] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const handleSubmit = async (formData: Record<string, any>) => {
    setSubmitting(true);
    setDownloadSuccess(null);
    try {
      // Build sample payload for spike engine
      const payload = {
        sellers: [
          {
            full_name: "आनंद बळवंत जोशी",
            gender: "male",
            age: 52,
            occupation: "व्यवसाय",
            address: "फ्लॅट क्र. 201, समर्थ संकुल, धरमपेठ, नागपूर",
            pan: "ABCDE1234F",
          },
        ],
        purchasers: [
          {
            full_name: "सुरेश रामराव पाटील",
            gender: "male",
            age: 41,
            occupation: "नोकरी",
            address: "प्लॉट क्र. 45, त्रिमूर्ती नगर, नागपूर",
            pan: "FGHIJ5678K",
          },
        ],
        property_details: {
          mouza: formData["property.mouza"] || "सोनेगाव",
          khasra_no: formData["property.khasra_no"] || "45/2",
          plot_no: formData["property.plot_no"] || "12",
          layout_name: formData["property.layout_name"] || "शिवकृपा लेआउट",
          sheet_no: formData["property.sheet_no"] || "14",
          area_sqm: formData["property.area_sqm"] || 150.0,
        },
        boundaries: {
          east: formData["boundaries.east"] || "रस्ता",
          west: formData["boundaries.west"] || "प्लॉट क्र. 13",
          north: formData["boundaries.north"] || "प्लॉट क्र. 11",
          south: formData["boundaries.south"] || "लेआउट सीमा",
        },
        financial_details: {
          total_consideration: formData["financial.total_consideration"] || 2500000.0,
          earnest_advance: formData["financial.earnest_advance"] || 500000.0,
        },
        execution_date: "2026-11-10",
      };

      const res = await fetch("/api/v1/documents/generate-spike", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Generation failed: ${res.statusText}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Sale_Deed_${payload.property_details.plot_no}_${payload.property_details.mouza}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setDownloadSuccess("दस्त यशस्वीरित्या डाऊनलोड झाला! (DOCX downloaded)");
    } catch (err: any) {
      alert(`त्रुटी: ${err?.message || "दस्त निर्मितीमध्ये त्रुटी"}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--surface-canvas)" }}>
      {/* Top Navbar */}
      <header
        style={{
          backgroundColor: "var(--brand-900)",
          color: "var(--text-on-dark)",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          boxShadow: "var(--shadow-nav)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h1 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700, letterSpacing: 0 }}>
            Lekhan | लेखन
          </h1>
          <span
            style={{
              fontSize: "0.75rem",
              backgroundColor: "rgba(255,255,255,0.15)",
              padding: "2px 8px",
              borderRadius: "var(--radius-pill)",
            }}
          >
            Phase 1 Dev
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <nav style={{ display: "flex", gap: "12px", fontSize: "0.875rem" }}>
            <a
              href="http://127.0.0.1:8000/form"
              target="_blank"
              rel="noreferrer"
              style={{ color: "rgba(255,255,255,0.85)", textDecoration: "none" }}
            >
              Backend UI
            </a>
            <a
              href="http://127.0.0.1:8000/templates/admin"
              target="_blank"
              rel="noreferrer"
              style={{ color: "rgba(255,255,255,0.85)", textDecoration: "none" }}
            >
              Templates Admin
            </a>
            <a
              href="http://127.0.0.1:8000/api/docs"
              target="_blank"
              rel="noreferrer"
              style={{ color: "rgba(255,255,255,0.85)", textDecoration: "none" }}
            >
              API Docs
            </a>
          </nav>

          {/* Language Switcher */}
          <div
            style={{
              display: "flex",
              gap: "4px",
              backgroundColor: "rgba(255,255,255,0.12)",
              padding: "3px",
              borderRadius: "var(--radius-pill)",
            }}
          >
            <button
              type="button"
              onClick={() => setLang("mr")}
              style={{
                backgroundColor: lang === "mr" ? "var(--brand-500)" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "var(--radius-pill)",
                padding: "4px 12px",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: 600,
              }}
            >
              मराठी
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              style={{
                backgroundColor: lang === "en" ? "var(--brand-500)" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "var(--radius-pill)",
                padding: "4px 12px",
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: 600,
              }}
            >
              English
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ maxWidth: "1000px", margin: "24px auto", padding: "0 16px" }}>
        {downloadSuccess && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: "var(--brand-100)",
              color: "var(--brand-900)",
              padding: "12px 16px",
              borderRadius: "var(--radius-card)",
              marginBottom: "16px",
              fontWeight: 500,
            }}
          >
            <FileCheck size={20} color="var(--brand-600)" />
            {downloadSuccess}
          </div>
        )}

        <DynamicForm
          manifest={defaultManifest}
          onSubmit={handleSubmit}
          isSubmitting={submitting}
        />
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <I18nProvider>
      <AppContent />
    </I18nProvider>
  );
};

export default App;
