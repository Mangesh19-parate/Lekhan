import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, type TemplateSummaryItem, type LintReport } from "../../shared/api";
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
  Send,
  Archive,
} from "lucide-react";

const DEFAULT_STUDIO_TEMPLATES = [
  { template_id: "sale_deed_plot_mr", name_mr: "प्लॉट खरेदीखत (नागपूर सुधार प्रन्यास / मनपा)", name_en: "Sale Deed: Plot", version: "1.0.0", status: "approved" },
  { template_id: "sale_deed_flat_mr", name_mr: "सदनिका खरेदीखत (रेरा नोंदणीकृत इमारत)", name_en: "Sale Deed: Flat", version: "1.0.0", status: "approved" },
  { template_id: "general_poa_mr", name_mr: "कुलमुखत्यारपत्र (General Power of Attorney)", name_en: "General POA", version: "1.0.0", status: "approved" },
  { template_id: "agreement_to_sell_plot_mr", name_mr: "इसारपावती / साठेखत", name_en: "Agreement to Sell", version: "1.0.0", status: "approved" },
];

interface TemplateStudioViewProps {
  onNavigate: (viewId: string) => void;
}

export const TemplateStudioView: React.FC<TemplateStudioViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<TemplateSummaryItem[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("sale_deed_plot_mr");
  const [lintReport, setLintReport] = useState<LintReport | null>(null);
  const [linting, setLinting] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadDocxFile, setUploadDocxFile] = useState<File | null>(null);
  const [uploadManifestFile, setUploadManifestFile] = useState<File | null>(null);
  const [uploadTemplateId, setUploadTemplateId] = useState<string>("sale_deed_plot_mr");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResultReport, setUploadResultReport] = useState<LintReport | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [lifecycleLoading, setLifecycleLoading] = useState(false);
  const [lifecycleMessage, setLifecycleMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmitForReview = async (tId: string) => {
    setLifecycleLoading(true);
    setLifecycleMessage(null);
    try {
      await api.submitTemplate(tId);
      setLifecycleMessage({
        type: "success",
        text: lang === "mr" ? "साचा पुनरावलोकनासाठी यशस्वीरित्या पाठवला." : "Template submitted for review successfully."
      });
      await fetchTemplates();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Submission failed";
      setLifecycleMessage({ type: "error", text: msg });
    } finally {
      setLifecycleLoading(false);
    }
  };

  const handleApproveTemplate = async (tId: string) => {
    setLifecycleLoading(true);
    setLifecycleMessage(null);
    try {
      await api.approveTemplate(tId);
      setLifecycleMessage({
        type: "success",
        text: lang === "mr" ? "साचा उत्पादन वापरासाठी मंजूर केला गेला." : "Template approved for production use."
      });
      await fetchTemplates();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Approval failed";
      setLifecycleMessage({ type: "error", text: msg });
    } finally {
      setLifecycleLoading(false);
    }
  };

  const handleRetireTemplate = async (tId: string) => {
    if (!window.confirm(lang === "mr" ? "तुम्हाला हा साचा निवृत्त करायचा आहे का?" : "Are you sure you want to retire this template?")) {
      return;
    }
    setLifecycleLoading(true);
    setLifecycleMessage(null);
    try {
      await api.retireTemplate(tId);
      setLifecycleMessage({
        type: "success",
        text: lang === "mr" ? "साचा निवृत्त करण्यात आला." : "Template retired successfully."
      });
      await fetchTemplates();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Retirement failed";
      setLifecycleMessage({ type: "error", text: msg });
    } finally {
      setLifecycleLoading(false);
    }
  };

  const safeTemplates = Array.isArray(templates) && templates.length > 0 ? templates : DEFAULT_STUDIO_TEMPLATES;

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await api.listTemplates();
      setTemplates(Array.isArray(data) && data.length > 0 ? data : DEFAULT_STUDIO_TEMPLATES);
      if (Array.isArray(data) && data.length > 0 && !selectedTemplateId) {
        setSelectedTemplateId(data[0].template_id);
      }
    } catch {
      setTemplates(DEFAULT_STUDIO_TEMPLATES);
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Check template files";
      alert("Linter failed: " + msg);
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
            options={safeTemplates.map((t) => ({
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
            const currentTmpl = safeTemplates.find((t) => t.template_id === selectedTemplateId);
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
                    variant="secondary"
                    onClick={() => handleRunLinter(selectedTemplateId)}
                    disabled={linting || lifecycleLoading}
                    leftIcon={<Play size={15} />}
                  >
                    {linting ? "Linting Template..." : "Re-Run DocxLinter"}
                  </Button>

                  {/* Template Submission (draft -> under_review) */}
                  {(!currentTmpl?.status || currentTmpl.status === "draft") && (
                    <Button
                      size="md"
                      variant="primary"
                      onClick={() => handleSubmitForReview(selectedTemplateId)}
                      disabled={lifecycleLoading || linting}
                      leftIcon={<Send size={15} />}
                    >
                      {lifecycleLoading ? "Submitting..." : lang === "mr" ? "पुनरावलोकनासाठी पाठवा (Submit)" : "Submit for Review"}
                    </Button>
                  )}

                  {/* Template Approval (under_review -> approved) */}
                  {currentTmpl?.status === "under_review" && (
                    <Button
                      size="md"
                      variant="primary"
                      onClick={() => handleApproveTemplate(selectedTemplateId)}
                      disabled={lifecycleLoading || linting || (lintReport && !lintReport.can_approve)}
                      leftIcon={<CheckCircle2 size={15} />}
                    >
                      {lifecycleLoading ? "Approving..." : lang === "mr" ? "साचा मंजूर करा (Approve)" : "Approve Template"}
                    </Button>
                  )}

                  {/* Template Retirement (approved -> retired) */}
                  {currentTmpl?.status === "approved" && (
                    <Button
                      size="md"
                      variant="secondary"
                      onClick={() => handleRetireTemplate(selectedTemplateId)}
                      disabled={lifecycleLoading || linting}
                      leftIcon={<Archive size={15} />}
                      style={{ color: "var(--danger-600)", borderColor: "var(--danger-border, #FCA5A5)" }}
                    >
                      {lifecycleLoading ? "Retiring..." : lang === "mr" ? "साचा निवृत्त करा (Retire)" : "Retire Template"}
                    </Button>
                  )}

                  {/* Separation of Duties & Lifecycle Status Alerts */}
                  {lifecycleMessage && (
                    <div
                      style={{
                        padding: "10px 12px",
                        borderRadius: "var(--radius-input)",
                        fontSize: "0.8125rem",
                        marginTop: "8px",
                        backgroundColor: lifecycleMessage.type === "error" ? "var(--danger-50, #FEF2F2)" : "var(--brand-50, #F0FDF4)",
                        border: `1px solid ${lifecycleMessage.type === "error" ? "var(--danger-border, #FCA5A5)" : "var(--brand-500, #22C55E)"}`,
                        color: lifecycleMessage.type === "error" ? "var(--danger-600, #991B1B)" : "var(--brand-900, #14532D)",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: "8px",
                      }}
                    >
                      {lifecycleMessage.type === "error" ? (
                        <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: "2px" }} />
                      ) : (
                        <CheckCircle2 size={16} style={{ flexShrink: 0, marginTop: "2px" }} />
                      )}
                      <div>
                        <strong>{lifecycleMessage.type === "error" ? (lifecycleMessage.text.includes("Separation of duties") ? "Separation of Duties Notice: " : "Action Failed: ") : "Success: "}</strong>
                        <span>{lifecycleMessage.text}</span>
                      </div>
                    </div>
                  )}
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
                  {lintReport.errors.map((err, idx: number) => (
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
        onClose={() => {
          setUploadModalOpen(false);
          setUploadResultReport(null);
          setUploadError(null);
        }}
        title={lang === "mr" ? "नवीन साचा आवृत्ती अपलोड करा" : "Upload Template Version"}
        maxWidth="600px"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "14px", fontSize: "0.875rem" }}>
          <p style={{ margin: 0, color: "var(--text-secondary)" }}>
            Upload a prepared legal deed DOCX and its companion <code>manifest.json</code> schema definition.
          </p>

          {uploadError && (
            <div style={{ padding: "10px 14px", borderRadius: "var(--radius-input)", backgroundColor: "#FEF2F2", border: "1px solid #F87171", color: "#991B1B" }}>
              <strong>Error:</strong> {uploadError}
            </div>
          )}

          {uploadResultReport ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div
                style={{
                  padding: "12px 16px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: uploadResultReport.can_approve ? "var(--brand-100)" : "#FEF2F2",
                  border: `1px solid ${uploadResultReport.can_approve ? "var(--brand-500)" : "#EF4444"}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  {uploadResultReport.can_approve ? (
                    <CheckCircle2 size={20} color="var(--brand-600)" />
                  ) : (
                    <XCircle size={20} color="#DC2626" />
                  )}
                  <span style={{ fontWeight: 600 }}>
                    {uploadResultReport.can_approve ? "Lint Passed - Draft Created" : "Lint Failed - Flaws Detected"}
                  </span>
                </div>
                <Badge
                  variant={uploadResultReport.can_approve ? "approved" : "danger"}
                  size="sm"
                  label={uploadResultReport.can_approve ? "Can Approve" : "Approval Blocked"}
                />
              </div>

              {/* Errors List */}
              {Array.isArray(uploadResultReport.errors) && uploadResultReport.errors.length > 0 && (
                <div style={{ padding: "12px", borderRadius: "var(--radius-input)", backgroundColor: "#FFF1F2", border: "1px solid #FECDD3" }}>
                  <div style={{ fontWeight: 700, color: "#9F1239", marginBottom: "6px" }}>Errors:</div>
                  <ul style={{ margin: 0, paddingLeft: "18px" }}>
                    {uploadResultReport.errors.map((err, i) => (
                      <li key={i} style={{ fontSize: "0.8125rem" }}><strong>{err.code}:</strong> {err.message}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Leftover Data */}
              {Array.isArray(uploadResultReport.leftover_data) && uploadResultReport.leftover_data.length > 0 && (
                <div style={{ padding: "12px", borderRadius: "var(--radius-input)", backgroundColor: "#FFF7ED", border: "1px solid #FED7AA" }}>
                  <div style={{ fontWeight: 700, color: "#9A3412", marginBottom: "6px" }}>Leftover Client PII:</div>
                  <ul style={{ margin: 0, paddingLeft: "18px" }}>
                    {uploadResultReport.leftover_data.map((l, i) => (
                      <li key={i} style={{ fontSize: "0.8125rem" }}>{l.category || "PII"} (x{l.count || 1}): {l.masked_sample || ""}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "8px" }}>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    setUploadModalOpen(false);
                    setUploadResultReport(null);
                  }}
                >
                  Done
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div>
                <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Target Template ID:</label>
                <input
                  type="text"
                  value={uploadTemplateId}
                  onChange={(e) => setUploadTemplateId(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "var(--radius-input)",
                    border: "1px solid var(--line-subtle)",
                    marginTop: "4px",
                    fontSize: "0.875rem",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>DOCX Template File (.docx):</label>
                <input
                  type="file"
                  accept=".docx"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadDocxFile(e.target.files[0]);
                    }
                  }}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "var(--radius-input)",
                    border: "1px solid var(--line-subtle)",
                    marginTop: "4px",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Optional manifest.json (or uses active schema):</label>
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setUploadManifestFile(e.target.files[0]);
                    }
                  }}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "var(--radius-input)",
                    border: "1px solid var(--line-subtle)",
                    marginTop: "4px",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "8px" }}>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setUploadModalOpen(false)}
                  disabled={uploading}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  disabled={uploading || !uploadDocxFile}
                  onClick={async () => {
                    if (!uploadDocxFile) {
                      setUploadError("Please choose a .docx template file.");
                      return;
                    }
                    setUploading(true);
                    setUploadError(null);
                    try {
                      let manifestContent = "{}";
                      if (uploadManifestFile) {
                        manifestContent = await uploadManifestFile.text();
                      } else {
                        try {
                          const existing = await api.getTemplateManifest(uploadTemplateId);
                          manifestContent = JSON.stringify(existing);
                        } catch {
                          manifestContent = JSON.stringify({
                            manifest_schema: 1,
                            template_id: uploadTemplateId,
                            name_en: uploadTemplateId,
                            name_mr: uploadTemplateId,
                            version: 1,
                            status: "draft",
                            document_type: "sale_deed",
                            property_type: "general",
                            language: "mr",
                            page_size: "legal",
                            digits_setting: "western",
                            retention_class: "matter_lifecycle",
                            parties: {},
                            repeaters: {},
                            sections: [],
                            fields: {},
                            derived_fields: {},
                            validations: [],
                          });
                        }
                      }

                      const formData = new FormData();
                      formData.append("template_id", uploadTemplateId);
                      formData.append("docx_file", uploadDocxFile);
                      formData.append("manifest_json", manifestContent);

                      const res = await api.uploadTemplate(formData);
                      setUploadResultReport(res.lint_report);
                      fetchTemplates();
                    } catch (err: unknown) {
                      const msg = err instanceof Error ? err.message : "Failed to upload template";
                      setUploadError(msg);
                    } finally {
                      setUploading(false);
                    }
                  }}
                >
                  {uploading ? "Uploading & Linting..." : "Upload & Run Linter"}
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};
