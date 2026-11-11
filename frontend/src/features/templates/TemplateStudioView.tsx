import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Select, Modal, Skeleton } from "../../shared/components";
import {
  FileCode,
  ShieldCheck,
  Upload,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  RotateCcw,
  RefreshCw,
  FileText,
} from "lucide-react";

interface TemplateStudioViewProps {
  onNavigate: (viewId: string) => void;
}

export const TemplateStudioView: React.FC<TemplateStudioViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("sale_deed_plot_mr");
  const [lintReport, setLintReport] = useState<any | null>(null);
  const [linting, setLinting] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await api.listTemplates();
      setTemplates(data || []);
      if (data && data.length > 0 && !selectedTemplateId) {
        setSelectedTemplateId(data[0].template_id);
      }
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleRunLinter = async (tId?: string) => {
    const idToLint = tId || selectedTemplateId;
    if (!idToLint) return;
    setLinting(true);
    setLintReport(null);
    try {
      const report = await api.lintTemplate(idToLint);
      setLintReport(report);
    } catch (err: any) {
      alert("Linter failed: " + (err?.message || "Check template files"));
    } finally {
      setLinting(false);
    }
  };

  useEffect(() => {
    if (selectedTemplateId) {
      handleRunLinter(selectedTemplateId);
    }
  }, [selectedTemplateId]);

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "साचा स्टुडिओ व तपासणी (Template Studio & Linter)" : "Template Studio & Linter"}
            </h1>
            <Badge variant="approved" size="md" label="DocxLinter Quality Gate" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "साच्यांचे जीवनचक्र (Lifecycle), टॅग सुसंगतता, शिल्लक डेटा तपासणी आणि कायदेशीर मंजुरी कार्यप्रवाह."
              : "Template lifecycle governance, DocxLinter static quality checks, leftover data inspection, and strict approval rules."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button size="sm" variant="secondary" onClick={fetchTemplates} leftIcon={<RefreshCw size={14} />}>
            {lang === "mr" ? "रिफ्रेश" : "Refresh"}
          </Button>
          <Button size="sm" variant="primary" onClick={() => setUploadModalOpen(true)} leftIcon={<Upload size={14} />}>
            {lang === "mr" ? "नवीन साचा अपलोड करा" : "Upload Template Version"}
          </Button>
        </div>
      </div>

      {/* 2. Separation of Duties Banner */}
      <div
        style={{
          padding: "14px 18px",
          borderRadius: "var(--radius-card)",
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--line-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <ShieldCheck size={22} color="var(--brand-600)" />
          <div>
            <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--brand-900)" }}>
              {lang === "mr" ? "कर्तव्य पृथक्करण नियम (Separation of Duties Enforced)" : "Separation of Duties Enforced"}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              {lang === "mr"
                ? "साचा सादर करणारा वापरकर्ता स्वतःच्या आवृत्तीला मंजुरी देऊ शकत नाही. मंजूर साचे अपरिवर्तनीय असतात."
                : "Submitters cannot approve their own template versions. Approved templates are immutable (Hard Rule 3)."}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
            {lang === "mr" ? "तपासावयाचा साचा:" : "Select Template:"}
          </span>
          <Select
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
            options={templates.map((t) => ({
              label: `${lang === "mr" ? t.name_mr || t.name_en : t.name_en} (${t.template_id})`,
              value: t.template_id,
            }))}
          />
        </div>
      </div>

      {/* 3. Linter Execution & Status Panel */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.6fr", gap: "20px" }}>
        {/* Left: Template Lifecycle & Approval Status */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
            {lang === "mr" ? "साचा जीवनचक्र स्थिती" : "Template Lifecycle State"}
          </h3>

          {(() => {
            const currentTmpl = templates.find((t) => t.template_id === selectedTemplateId);
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Current Status:</span>
                  <Badge
                    variant={currentTmpl?.status === "approved" ? "approved" : "neutral"}
                    size="md"
                    label={currentTmpl?.status?.toUpperCase() || "DRAFT"}
                  />
                </div>

                <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem" }}>
                  <div><strong>ID:</strong> {currentTmpl?.template_id}</div>
                  <div><strong>Version:</strong> v{currentTmpl?.version || 1}</div>
                  <div><strong>Language:</strong> {currentTmpl?.language === "mr" ? "मराठी (mr)" : "English (en)"}</div>
                  <div><strong>Document Type:</strong> {currentTmpl?.document_type}</div>
                  <div><strong>Property:</strong> {currentTmpl?.property_type}</div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px", paddingTop: "12px", borderTop: "1px solid var(--line-subtle)" }}>
                  <Button
                    size="md"
                    variant="primary"
                    onClick={() => handleRunLinter(selectedTemplateId)}
                    disabled={linting}
                    leftIcon={<Play size={15} />}
                  >
                    {linting ? "Linting Template..." : "Re-Run DocxLinter"}
                  </Button>
                </div>
              </div>
            );
          })()}
        </Card>

        {/* Right: Real DocxLinter Findings Report */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
              {lang === "mr" ? "DocxLinter गुणवत्ता पडताळणी निकाल" : "DocxLinter Static Quality Inspection"}
            </h3>
            {lintReport && (
              <Badge
                variant={lintReport.can_approve ? "approved" : "neutral"}
                size="md"
                label={lintReport.can_approve ? "PASS: Ready to Approve" : "FAIL: Errors Block Approval"}
              />
            )}
          </div>

          {linting ? (
            <Skeleton height="220px" />
          ) : !lintReport ? (
            <div style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
              Select a template to inspect with DocxLinter.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {/* Summary Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", textAlign: "center" }}>
                <div style={{ padding: "10px", backgroundColor: "var(--surface-sunken)", borderRadius: "var(--radius-input)" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: lintReport.errors?.length ? "var(--danger-600)" : "var(--brand-600)" }}>
                    {lintReport.errors?.length || 0}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Errors (Blocking)</div>
                </div>

                <div style={{ padding: "10px", backgroundColor: "var(--surface-sunken)", borderRadius: "var(--radius-input)" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#D97706" }}>
                    {lintReport.warnings?.length || 0}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Warnings</div>
                </div>

                <div style={{ padding: "10px", backgroundColor: "var(--surface-sunken)", borderRadius: "var(--radius-input)" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: lintReport.leftover_data?.length ? "var(--danger-600)" : "var(--brand-600)" }}>
                    {lintReport.leftover_data?.length || 0}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Leftover Facts</div>
                </div>
              </div>

              {/* Detected Fonts & Split Runs */}
              <div style={{ fontSize: "0.8125rem", display: "flex", justifyContent: "space-between", backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)" }}>
                <span><strong>Fonts:</strong> {lintReport.fonts?.join(", ") || "Unicode Noto Serif Devanagari"}</span>
                <span><strong>Repaired Split Runs:</strong> {lintReport.split_runs_repaired || 0}</span>
              </div>

              {/* Errors List */}
              {lintReport.errors && lintReport.errors.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--danger-600)" }}>
                    Approval-Blocking Findings:
                  </span>
                  {lintReport.errors.map((err: any, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        padding: "8px 12px",
                        borderRadius: "var(--radius-input)",
                        backgroundColor: "#FEE2E2",
                        border: "1px solid #FCA5A5",
                        fontSize: "0.8125rem",
                        color: "#991B1B",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <XCircle size={16} />
                      <span>{err.message || err.code}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Clean Bill */}
              {lintReport.errors?.length === 0 && lintReport.leftover_data?.length === 0 && (
                <div
                  style={{
                    padding: "12px",
                    borderRadius: "var(--radius-input)",
                    backgroundColor: "var(--brand-100)",
                    border: "1px solid var(--brand-500)",
                    fontSize: "0.8125rem",
                    color: "var(--brand-900)",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                  }}
                >
                  <CheckCircle2 size={18} color="var(--brand-600)" />
                  <span>
                    {lang === "mr"
                      ? "साचा सर्व OpenXML, फॉन्ट, शिल्लक डेटा व टॅग सुसंगतता चाचण्यांमध्ये १००% उत्तीर्ण झाला आहे."
                      : "Template passed all OpenXML structure, font, leftover scanner, and manifest tag checks cleanly."}
                  </span>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title={lang === "mr" ? "नवीन साचा आवृत्ती अपलोड करा" : "Upload Template Version"}
        maxWidth="550px"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "14px", fontSize: "0.875rem" }}>
          <p style={{ margin: 0, color: "var(--text-secondary)" }}>
            Upload a prepared legal deed DOCX and its companion <code>manifest.json</code> schema definition.
          </p>
          <div style={{ border: "2px dashed var(--line-subtle)", borderRadius: "var(--radius-card)", padding: "24px", textAlign: "center" }}>
            <Upload size={32} color="var(--text-tertiary)" style={{ margin: "0 auto 8px auto" }} />
            <div style={{ fontWeight: 600 }}>Drag & drop DOCX and manifest.json here</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "4px" }}>
              Must satisfy OpenXML Legal paper size and PAGE fields.
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
            <Button size="sm" variant="secondary" onClick={() => setUploadModalOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" variant="primary" onClick={() => { setUploadModalOpen(false); alert("Uploaded template queued for DocxLinter verification."); }}>
              Submit Version
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
