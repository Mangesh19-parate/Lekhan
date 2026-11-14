import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card } from "../../shared/components";
import {
  Clock,
  Play,
  Trash2,
  FileText,
  AlertTriangle,
  RefreshCw,
  Plus,
} from "lucide-react";

interface DraftsPendingViewProps {
  onNavigate: (viewId: string) => void;
  onResumeDraft?: (draftData: any) => void;
}

export const DraftsPendingView: React.FC<DraftsPendingViewProps> = ({
  onNavigate,
  onResumeDraft,
}) => {
  const { lang } = useI18n();
  const [drafts, setDrafts] = useState<any[]>(() => {
    const saved = localStorage.getItem("lekhan_saved_drafts");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        /* ignore parse error */
      }
    }
    return [];
  });

  const handleDeleteDraft = (id: string) => {
    const updated = drafts.filter((d) => d.id !== id);
    setDrafts(updated);
    localStorage.setItem("lekhan_saved_drafts", JSON.stringify(updated));
  };

  const handleResume = (draft: any) => {
    if (onResumeDraft) {
      onResumeDraft(draft);
    }
    onNavigate("new_draft");
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "मसुदे व प्रलंबित प्रकरणे (Drafts & Pending Matters)" : "Drafts & In-Progress Matters"}
            </h1>
            <Badge variant="neutral" size="md" label={`${drafts.length} Active Drafts`} />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "अपूर्ण राहिलेले मसुदे, ऑटोसॅव्ह झालेले कामकाज व पुनरुत्थानासाठी सज्ज प्रकरणे."
              : "Recover and resume drafting in-progress legal matters with zero data loss."}
          </p>
        </div>

        <Button size="sm" variant="primary" onClick={() => onNavigate("new_draft")} leftIcon={<Plus size={15} />}>
          {lang === "mr" ? "नवीन मसुदा" : "Create New Draft"}
        </Button>
      </div>

      {/* 2. Drafts Grid */}
      {drafts.length === 0 ? (
        <Card style={{ padding: "48px 24px", textAlign: "center" }}>
          <Clock size={40} color="var(--text-tertiary)" style={{ margin: "0 auto 12px auto" }} />
          <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--brand-900)", margin: 0 }}>
            {lang === "mr" ? "कोणताही प्रलंबित मसुदा नाही." : "No in-progress drafts found."}
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: "6px 0 16px 0" }}>
            {lang === "mr" ? "सर्व दस्त पूर्ण झाले आहेत अथवा नोंदवहीत जमा झाले आहेत." : "All drafting matters are up to date."}
          </p>
          <Button size="sm" variant="primary" onClick={() => onNavigate("new_draft")}>
            {lang === "mr" ? "नवीन मसुदा तयार करा" : "Start New Draft"}
          </Button>
        </Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: "16px" }}>
          {drafts.map((d) => (
            <Card
              key={d.id}
              style={{
                padding: "18px",
                display: "flex",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
                    {d.title || "Untitled Draft"}
                  </h3>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "2px" }}>
                    Last saved: {new Date(d.savedAt).toLocaleString()}
                  </div>
                </div>
                <Badge variant="neutral" size="sm" label="In Progress" />
              </div>

              <div style={{ backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem" }}>
                <div><strong>Mouza:</strong> {d.mouza || d.data?.formData?.["property.mouza"] || "Sonegaon"}</div>
                <div><strong>Plot No:</strong> {d.plotNo || d.data?.formData?.["property.plot_no"] || "Draft Plot"}</div>
              </div>

              <div style={{ display: "flex", gap: "8px", marginTop: "auto", paddingTop: "8px" }}>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleResume(d)}
                  leftIcon={<Play size={14} />}
                  style={{ flex: 1 }}
                >
                  {lang === "mr" ? "मसुदा सुरू ठेवा" : "Resume Drafting"}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleDeleteDraft(d.id)}
                  leftIcon={<Trash2 size={14} />}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

