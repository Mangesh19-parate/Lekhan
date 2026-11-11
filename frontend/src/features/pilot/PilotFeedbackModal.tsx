import React, { useState } from "react";
import { Modal, Input, Button, Select } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { useToast } from "../../shared/components";
import { useAuth } from "../../shared/auth/AuthContext";
import { MessageSquarePlus, CheckCircle2, AlertCircle } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  templateId?: string;
  documentId?: string;
}

export const PilotFeedbackModal: React.FC<Props> = ({
  isOpen,
  onClose,
  templateId = "sale_deed_plot_mr",
  documentId,
}) => {
  const { lang, t } = useI18n();
  const { toast } = useToast();
  const { csrfToken } = useAuth();

  const [category, setCategory] = useState("legal_clause");
  const [severity, setSeverity] = useState("minor");
  const [description, setDescription] = useState("");
  const [originalText, setOriginalText] = useState("");
  const [correctedText, setCorrectedText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim() || description.trim().length < 3) {
      setError(lang === "mr" ? "कृपया त्रुटीचे सविस्तर वर्णन लिहा." : "Please provide feedback description.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/pilot/corrections", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "X-CSRF-Token": csrfToken || "",
        },
        credentials: "include",
        body: JSON.stringify({
          template_id: templateId,
          document_id: documentId || null,
          category,
          severity,
          description: description.trim(),
          original_text: originalText.trim() || null,
          corrected_text: correctedText.trim() || null,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Submission failed with HTTP ${res.status}`);
      }

      toast({
        title: lang === "mr" ? "अभिप्राय नोंदवला गेला" : "Feedback Logged",
        description: lang === "mr" ? "पायलट त्रुटी दुरुस्तीसाठी यशस्वीपणे नोंदवली गेली आहे." : "Your feedback has been logged into the pilot triage engine.",
        type: "success",
      });

      setDescription("");
      setOriginalText("");
      setCorrectedText("");
      onClose();
    } catch (err: any) {
      console.error("Pilot correction error:", err);
      setError(err.message || "Failed to submit correction");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={lang === "mr" ? "पायलट मसुदा अभिप्राय व त्रुटी नोंदवा" : "Log Pilot Feedback & Corrections"}
      size="md"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {error && (
          <div style={{ padding: "10px 14px", backgroundColor: "var(--color-danger-bg)", color: "var(--color-danger-fg)", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <Select
            id="feedback-category"
            label={lang === "mr" ? "त्रुटीचा प्रकार (Category)" : "Category"}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={[
              { value: "legal_clause", label: lang === "mr" ? "कायदेशीर कलम / मजकूर (Legal Clause)" : "Legal Clause / Recital" },
              { value: "grammar", label: lang === "mr" ? "मराठी व्याकरण / शब्दरचना (Grammar)" : "Marathi Grammar / Syntax" },
              { value: "layout_spacing", label: lang === "mr" ? "मांडणी व समास (Layout & Spacing)" : "Layout & Spacing" },
              { value: "numbering", label: lang === "mr" ? "क्रमांक पद्धती (Numbering)" : "Numbering & Hierarchy" },
              { value: "missing_field", label: lang === "mr" ? "गहाळ तपशील (Missing Field)" : "Missing Field" },
              { value: "other", label: lang === "mr" ? "इतर (Other)" : "Other" },
            ]}
          />

          <Select
            id="feedback-severity"
            label={lang === "mr" ? "गांभीर्य (Severity)" : "Severity"}
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            options={[
              { value: "cosmetic", label: lang === "mr" ? "साधारण (Cosmetic)" : "Cosmetic" },
              { value: "minor", label: lang === "mr" ? "मध्यम (Minor)" : "Minor" },
              { value: "blocking", label: lang === "mr" ? "गंभीर / अडथळा (Blocking)" : "Blocking" },
            ]}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
            {lang === "mr" ? "त्रुटीचे वर्णन / सुधारणा सूचना *" : "Feedback & Correction Description *"}
          </label>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={lang === "mr" ? "दस्तऐवजात काय बदल किंवा सुधारणा हवी आहे..." : "Describe the correction needed in this template or deed draft..."}
            required
            style={{
              width: "100%",
              padding: "10px 12px",
              borderRadius: "var(--radius-input)",
              border: "1px solid var(--line-subtle)",
              backgroundColor: "var(--surface-sunken)",
              color: "var(--text-primary)",
              fontSize: "0.875rem",
              fontFamily: "var(--font-ui)",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
            {lang === "mr" ? "मूळ मसुदा मजकूर (ऐच्छिक)" : "Original Draft Text (Optional)"}
          </label>
          <textarea
            rows={2}
            value={originalText}
            onChange={(e) => setOriginalText(e.target.value)}
            placeholder={lang === "mr" ? "सध्याचा मजकूर..." : "Current generated draft wording..."}
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: "var(--radius-input)",
              border: "1px solid var(--line-subtle)",
              backgroundColor: "var(--surface-sunken)",
              color: "var(--text-primary)",
              fontSize: "0.8125rem",
              fontFamily: "var(--font-mono)",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
            {lang === "mr" ? "सुचवलेला योग्य मजकूर (ऐच्छिक)" : "Proposed Corrected Text (Optional)"}
          </label>
          <textarea
            rows={2}
            value={correctedText}
            onChange={(e) => setCorrectedText(e.target.value)}
            placeholder={lang === "mr" ? "अपेक्षित दुरुस्त मजकूर..." : "Proposed replacement legal wording..."}
            style={{
              width: "100%",
              padding: "8px 12px",
              borderRadius: "var(--radius-input)",
              border: "1px solid var(--line-subtle)",
              backgroundColor: "var(--surface-sunken)",
              color: "var(--text-primary)",
              fontSize: "0.8125rem",
              fontFamily: "var(--font-mono)",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
          <Button variant="secondary" size="md" onClick={onClose} type="button">
            {lang === "mr" ? "रद्द करा" : "Cancel"}
          </Button>
          <Button
            variant="primary"
            size="md"
            type="submit"
            isLoading={isSubmitting}
            leftIcon={<CheckCircle2 size={16} />}
          >
            {lang === "mr" ? "नोंदवा" : "Submit Feedback"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
