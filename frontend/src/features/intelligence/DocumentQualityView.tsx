import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, DocumentQualityResponse } from "../../shared/api";
import { Button, Badge, Card, Select } from "../../shared/components";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileCheck2,
  Play,
  RotateCcw,
} from "lucide-react";

interface DocumentQualityViewProps {
  onNavigate: (viewId: string) => void;
}

export const DocumentQualityView: React.FC<DocumentQualityViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [selectedTarget, setSelectedTarget] = useState("sale_deed_plot_mr");
  const [targetOptions, setTargetOptions] = useState<Array<{ label: string; value: string }>>([
    { label: "Sale Deed Plot (sale_deed_plot_mr)", value: "sale_deed_plot_mr" },
    { label: "Agreement to Sell Plot (agreement_to_sell_plot_mr)", value: "agreement_to_sell_plot_mr" },
    { label: "Sale Deed Flat EN (sale_deed_flat_en)", value: "sale_deed_flat_en" },
  ]);
  const [isInspecting, setIsInspecting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [report, setReport] = useState<DocumentQualityResponse | null>(null);

  useEffect(() => {
    // Load recent generated documents and templates to populate target options
    Promise.all([
      api.listDocuments({ limit: 10 }).catch(() => null),
      api.listTemplates().catch(() => null),
    ]).then(([docsRes, tmplsRes]) => {
      const opts: Array<{ label: string; value: string }> = [];
      if (docsRes?.items && docsRes.items.length > 0) {
        docsRes.items.forEach((d) => {
          opts.push({
            label: `Document: ${d.doc_no} (${d.language.toUpperCase()})`,
            value: d.id,
          });
        });
      }
      if (tmplsRes && tmplsRes.length > 0) {
        tmplsRes.forEach((t) => {
          opts.push({
            label: `Template: ${t.name} (${t.id})`,
            value: t.id,
          });
        });
      }
      if (opts.length > 0) {
        setTargetOptions(opts);
        setSelectedTarget(opts[0].value);
      }
    });
  }, []);

  const runQualityInspection = async () => {
    if (!selectedTarget) return;
    setIsInspecting(true);
    setErrorMessage(null);
    try {
      const res = await api.checkDocumentQuality(selectedTarget);
      setReport(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run document quality inspection";
      setErrorMessage(msg);
    } finally {
      setIsInspecting(false);
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "दस्त गुणवत्ता व तपासणी केंद्र (Document Quality Center)" : "Document Quality Center"}
            </h1>
            <Badge variant="approved" size="md" label="DocxLinter & Leftover Scanner" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "तयार केलेल्या दस्तऐवजांची १०-मुद्द्यांची कायदेशीर व तांत्रिक गुणवत्ता पडताळणी."
              : "Live backend inspection running DocxLinter, PII leftover scanner, font audit, and structural safety checks."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button size="sm" variant="primary" onClick={runQualityInspection} disabled={isInspecting} leftIcon={<Play size={14} />}>
            {isInspecting ? (lang === "mr" ? "तपासणी सुरू आहे..." : "Inspecting...") : (lang === "mr" ? "गुणवत्ता तपासणी सुरू करा" : "Run Quality Inspection")}
          </Button>
        </div>
      </div>

      {/* Error alert */}
      {errorMessage && (
        <div style={{ padding: "12px 16px", borderRadius: "var(--radius-input)", backgroundColor: "var(--danger-100, #FEE2E2)", border: "1px solid var(--danger-500, #EF4444)", color: "var(--danger-900, #7F1D1D)", fontSize: "0.875rem" }}>
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* 2. Target Selector */}
      <Card style={{ padding: "16px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>
            {lang === "mr" ? "तपासावयाचा दस्त / साचा:" : "Select Document / Template:"}
          </span>
          <Select
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
            options={targetOptions}
          />
        </div>

        <Button size="sm" variant="secondary" onClick={runQualityInspection} disabled={isInspecting} leftIcon={<RotateCcw size={14} />}>
          {lang === "mr" ? "पुन्हा तपासा" : "Re-Inspect"}
        </Button>
      </Card>

      {/* 3. Inspection Report Results */}
      {report ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Status Banner */}
          <div
            style={{
              padding: "18px 24px",
              borderRadius: "var(--radius-card)",
              backgroundColor: report.overall_status === "Passed" ? "var(--brand-100)" : "var(--danger-100, #FEE2E2)",
              border: `1px solid ${report.overall_status === "Passed" ? "var(--brand-500)" : "var(--danger-500, #EF4444)"}`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              {report.overall_status === "Passed" ? (
                <CheckCircle2 size={26} color="var(--brand-600)" />
              ) : (
                <XCircle size={26} color="#DC2626" />
              )}
              <div>
                <div style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--brand-900)" }}>
                  {report.overall_status === "Passed"
                    ? (lang === "mr" ? "दस्त गुणवत्ता तपासणी उत्तीर्ण (Passed All Integrity Checks)" : "Quality Inspection Passed")
                    : (lang === "mr" ? "दस्त गुणवत्ता तपासणीत त्रुटी आढळल्या (Integrity Checks Failed)" : "Quality Inspection Findings Requiring Action")}
                </div>
                <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                  Inspected at: {new Date(report.timestamp).toLocaleString()} | Target: {report.document_id} | Score: {report.score}
                </div>
              </div>
            </div>
            <Badge
              variant={report.overall_status === "Passed" ? "approved" : "danger"}
              size="md"
              label={report.overall_status}
            />
          </div>

          {/* Blocking Errors */}
          {report.blocking_errors && report.blocking_errors.length > 0 && (
            <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px", borderColor: "#EF4444" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#B91C1C", fontWeight: 700 }}>
                <XCircle size={18} />
                <span>{lang === "mr" ? "गंभीर त्रुटी (Blocking Errors)" : "Blocking Errors"}</span>
              </div>
              {report.blocking_errors.map((e, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "10px 14px",
                    borderRadius: "var(--radius-input)",
                    backgroundColor: "#FEF2F2",
                    border: "1px solid #FCA5A5",
                    fontSize: "0.8125rem",
                  }}
                >
                  <strong>[{e.code}]:</strong> {e.message}
                </div>
              ))}
            </Card>
          )}

          {/* Leftover PII Data */}
          {report.leftover_data && report.leftover_data.length > 0 && (
            <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px", borderColor: "#DC2626" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#DC2626", fontWeight: 700 }}>
                <AlertTriangle size={18} />
                <span>{lang === "mr" ? "अवशिष्ट वैयक्तिक माहिती (Leftover PII Detected)" : "Leftover PII / Sensitive Client Data Detected"}</span>
              </div>
              {report.leftover_data.map((l, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "10px 14px",
                    borderRadius: "var(--radius-input)",
                    backgroundColor: "#FFF1F2",
                    border: "1px solid #FECDD3",
                    fontSize: "0.8125rem",
                  }}
                >
                  <strong>{l.category} (x{l.count}) in {l.part}:</strong> Masked preview: <code>{l.masked_sample}</code>
                </div>
              ))}
            </Card>
          )}

          {/* Detailed Passed Checks */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "16px" }}>
            {report.passed_checks.map((c, idx) => (
              <Card key={idx} style={{ padding: "16px", display: "flex", alignItems: "flex-start", gap: "12px" }}>
                <CheckCircle2 size={18} color="var(--brand-600)" style={{ flexShrink: 0, marginTop: "2px" }} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--brand-900)" }}>{c.name}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>{c.description}</div>
                </div>
              </Card>
            ))}
          </div>

          {/* Warnings List */}
          {report.warnings && report.warnings.length > 0 && (
            <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "#B45309" }}>
                {lang === "mr" ? "कायदेशीर सूचना (Non-Blocking Advisory Notes)" : "Non-Blocking Advisory Observations"}
              </h3>
              {report.warnings.map((w, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "10px 14px",
                    borderRadius: "var(--radius-input)",
                    backgroundColor: "var(--approved-100)",
                    border: "1px solid var(--approved-500)",
                    fontSize: "0.8125rem",
                  }}
                >
                  <strong>[{w.code}]:</strong> {w.message}
                </div>
              ))}
            </Card>
          )}
        </div>
      ) : (
        <Card style={{ padding: "48px 24px", textAlign: "center" }}>
          <FileCheck2 size={40} color="var(--text-tertiary)" style={{ margin: "0 auto 12px auto" }} />
          <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--brand-900)", margin: 0 }}>
            {lang === "mr" ? "गुणवत्ता तपासणी सुरू करण्यासाठी बटणावर क्लिक करा." : "Click 'Run Quality Inspection' to evaluate deed"}
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: "6px 0 16px 0" }}>
            Runs real DocxLinter and leftover scanner on the selected document or template.
          </p>
          <Button size="sm" variant="primary" onClick={runQualityInspection} disabled={isInspecting}>
            {lang === "mr" ? "तपासणी करा" : "Run Inspection"}
          </Button>
        </Card>
      )}
    </div>
  );
};
