import React, { useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Input, Select } from "../../shared/components";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Play,
  Cpu,
  Layers,
  ArrowRight,
} from "lucide-react";

interface ValidationCenterViewProps {
  onNavigate: (viewId: string) => void;
}

export const ValidationCenterView: React.FC<ValidationCenterViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [templateId, setTemplateId] = useState("sale_deed_plot_mr");
  const [totalConsideration, setTotalConsideration] = useState("2500000");
  const [earnestAdvance, setEarnestAdvance] = useState("500000");
  const [areaSqm, setAreaSqm] = useState("150");
  const [evaluating, setEvaluating] = useState(false);
  const [validationResult, setValidationResult] = useState<any | null>(null);

  const handleTestValidation = async () => {
    setEvaluating(true);
    setValidationResult(null);

    const testPayload = {
      property: {
        mouza: "सोनेगाव",
        khasra_no: "45/2",
        plot_no: "12",
        area_sqm: parseFloat(areaSqm) || 0,
      },
      financial: {
        total_consideration: parseFloat(totalConsideration) || 0,
        earnest_advance: parseFloat(earnestAdvance) || 0,
      },
    };

    try {
      const res = await api.validateDraftData(templateId, testPayload);
      setValidationResult(res);
    } catch (err: any) {
      setValidationResult({
        valid: false,
        violations: [{ message_en: err?.message || "Validation failed", message_mr: "तपासणी अयशस्वी" }],
        derived_fields: {},
      });
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "नियम व प्रमाणीकरण केंद्र (Validation Center)" : "Validation Center & AST Engine"}
            </h1>
            <Badge variant="approved" size="md" label="Pratt Parser AST" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "साच्यांचे गणिती नियम, इसार रक्कम मर्यादा व क्षेत्रफळ सुसंगततेची थेट पडताळणी."
              : "Server-side manifest condition AST evaluator, cross-field rules, and derived computation."}
          </p>
        </div>

        <Button size="sm" variant="primary" onClick={handleTestValidation} disabled={evaluating} leftIcon={<Play size={14} />}>
          {evaluating ? "Evaluating AST..." : lang === "mr" ? "नियम तपासा (Test AST)" : "Evaluate Rules"}
        </Button>
      </div>

      {/* 2. Interactive Rule Sandbox */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "20px" }}>
        {/* Left: Input Console */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
              {lang === "mr" ? "तपासणी इनपुट (Test Fact Values)" : "Test Fact Input Parameters"}
            </h3>
            <Badge variant="neutral" size="sm" label="Live Schema v1" />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Active Template:</label>
              <Select
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                options={[
                  { label: "Sale Deed Plot (sale_deed_plot_mr)", value: "sale_deed_plot_mr" },
                  { label: "Agreement to Sell Plot (agreement_to_sell_plot_mr)", value: "agreement_to_sell_plot_mr" },
                ]}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>एकूण मोबदला (Total Consideration Rs.):</label>
                <Input
                  type="number"
                  value={totalConsideration}
                  onChange={(e) => setTotalConsideration(e.target.value)}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>इसार / आगाऊ रक्कम (Earnest / Advance Rs.):</label>
                <Input
                  type="number"
                  value={earnestAdvance}
                  onChange={(e) => setEarnestAdvance(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>मिळकत क्षेत्रफळ (Property Area Sq. Metres):</label>
              <Input
                type="number"
                value={areaSqm}
                onChange={(e) => setAreaSqm(e.target.value)}
              />
            </div>

            <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setTotalConsideration("2000000");
                  setEarnestAdvance("2500000"); // Intentional violation!
                }}
              >
                {lang === "mr" ? "त्रुटी चाचणी (Advance > Total)" : "Simulate Violation (Advance > Total)"}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setTotalConsideration("2500000");
                  setEarnestAdvance("500000"); // Valid!
                }}
              >
                {lang === "mr" ? "योग्य मूल्ये (Valid Case)" : "Reset to Valid"}
              </Button>
            </div>
          </div>
        </Card>

        {/* Right: AST Evaluation Output */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
            {lang === "mr" ? "AST मूल्यांकन निकाल" : "Server AST Evaluation Output"}
          </h3>

          {!validationResult ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "var(--text-secondary)" }}>
              <Cpu size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
              <div>Click 'Evaluate Rules' to run server-side AST verification.</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {/* Overall status */}
              <div
                style={{
                  padding: "12px 16px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: validationResult.valid ? "var(--brand-100)" : "#FEE2E2",
                  border: `1px solid ${validationResult.valid ? "var(--brand-500)" : "#FCA5A5"}`,
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                }}
              >
                {validationResult.valid ? (
                  <CheckCircle2 size={20} color="var(--brand-600)" />
                ) : (
                  <XCircle size={20} color="var(--danger-600)" />
                )}
                <span style={{ fontWeight: 600, fontSize: "0.875rem", color: validationResult.valid ? "var(--brand-900)" : "#991B1B" }}>
                  {validationResult.valid
                    ? lang === "mr" ? "सर्व नियम वैध ठरले आहेत (Valid)" : "Payload satisfies all business rules"
                    : lang === "mr" ? "नियमांचे उल्लंघन आढळले (Rule Violations Detected)" : "Blocking Validation Violations Found"}
                </span>
              </div>

              {/* Violations */}
              {validationResult.violations && validationResult.violations.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--danger-600)" }}>
                    Violations:
                  </span>
                  {validationResult.violations.map((v: any, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        padding: "8px 12px",
                        borderRadius: "var(--radius-input)",
                        backgroundColor: "#FEF2F2",
                        border: "1px solid #FECACA",
                        fontSize: "0.8125rem",
                        color: "#B91C1C",
                      }}
                    >
                      {lang === "mr" ? v.message_mr || v.message_en : v.message_en}
                    </div>
                  ))}
                </div>
              )}

              {/* Derived Fields Output */}
              {validationResult.derived_fields && Object.keys(validationResult.derived_fields).length > 0 && (
                <div>
                  <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                    Authoritative Backend Derived Values:
                  </span>
                  <div style={{ backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)", marginTop: "6px", fontSize: "0.8125rem" }}>
                    {Object.entries(validationResult.derived_fields).map(([k, val]: [string, any]) => (
                      <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0" }}>
                        <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{k}:</span>
                        <strong style={{ color: "var(--brand-900)" }}>{String(val)}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

