import React from "react";
import { Modal, Button, EmptyState } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { Clock, RotateCcw, Trash2, FileCheck } from "lucide-react";

export interface SavedDraft {
  id: string;
  savedAt: string;
  title: string;
  plotNo?: string;
  mouza?: string;
  data: {
    formData: Record<string, any>;
    repeatersData: Record<string, any[]>;
  };
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  drafts: SavedDraft[];
  onRestore: (draft: SavedDraft) => void;
  onDelete: (id: string) => void;
}

export const RecentDraftsDrawer: React.FC<Props> = ({
  isOpen,
  onClose,
  drafts,
  onRestore,
  onDelete,
}) => {
  const { lang, t } = useI18n();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("nav.recent_drafts")}
      description={
        lang === "mr"
          ? "या ब्राउझरमध्ये स्वयंचलित किंवा हाताने जतन केलेले मसुदे"
          : "Drafts saved automatically or manually in this browser"
      }
      maxWidth="560px"
    >
      {drafts.length === 0 ? (
        <EmptyState
          icon={<Clock size={24} />}
          title={lang === "mr" ? "कोणतेही जुने मसुदे उपलब्ध नाहीत" : "No recent drafts found"}
          description={
            lang === "mr"
              ? "तुम्ही फॉर्म भरता तेव्हा मसुदा स्वयंचलितरित्या जतन केला जातो."
              : "As you edit deed terms, drafts will be saved locally here."
          }
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {drafts.map((draft) => (
            <div
              key={draft.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 16px",
                borderRadius: "var(--radius-card)",
                backgroundColor: "var(--surface-sunken)",
                border: "1px solid var(--line-subtle)",
              }}
            >
              <div>
                <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  {draft.title || (lang === "mr" ? "खरेदीखत मसुदा" : "Sale Deed Draft")}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                  <span>{draft.plotNo ? `Plot ${draft.plotNo}` : ""} {draft.mouza ? `(${draft.mouza})` : ""}</span>
                  <span style={{ marginLeft: "8px", opacity: 0.8 }}>
                    • {new Date(draft.savedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Button
                  size="sm"
                  variant="secondary"
                  pill
                  onClick={() => {
                    onRestore(draft);
                    onClose();
                  }}
                  leftIcon={<RotateCcw size={13} />}
                >
                  {t("actions.restore")}
                </Button>
                <button
                  type="button"
                  onClick={() => onDelete(draft.id)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--danger-600)",
                    padding: "6px",
                    cursor: "pointer",
                    borderRadius: "var(--radius-input)",
                  }}
                  title={t("actions.remove")}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
};

