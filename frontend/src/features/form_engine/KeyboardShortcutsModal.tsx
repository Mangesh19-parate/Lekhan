import React from "react";
import { Modal } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { Keyboard } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { t } = useI18n();

  const shortcuts = [
    { key: "Ctrl + K / ⌘K", desc: t("shortcuts.command_palette") },
    { key: "Ctrl + S", desc: t("shortcuts.save_draft") },
    { key: "Ctrl + Enter", desc: t("shortcuts.add_party") },
    { key: "Ctrl + E", desc: "Generate & Download DOCX" },
    { key: "Ctrl + L", desc: "Load Nagpur Plot Sample" },
    { key: "Ctrl + T", desc: t("shortcuts.toggle_theme") },
    { key: "Ctrl + G", desc: t("shortcuts.toggle_lang") },
    { key: "?", desc: t("shortcuts.title") },
    { key: "Esc", desc: t("shortcuts.close_dialog") },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("shortcuts.title")}
      description={t("shortcuts.subtitle")}
      maxWidth="500px"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {shortcuts.map((s, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "8px 12px",
              borderRadius: "var(--radius-input)",
              backgroundColor: "var(--surface-sunken)",
            }}
          >
            <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontWeight: 500 }}>
              {s.desc}
            </span>
            <kbd
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.75rem",
                padding: "3px 8px",
                borderRadius: "4px",
                backgroundColor: "var(--surface-card)",
                border: "1px solid var(--line-medium)",
                color: "var(--brand-900)",
                fontWeight: 600,
              }}
            >
              {s.key}
            </kbd>
          </div>
        ))}
      </div>
    </Modal>
  );
};

