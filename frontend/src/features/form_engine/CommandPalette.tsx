import React, { useState, useEffect, useRef } from "react";
import { Search, FileText, Zap, Moon, Sun, Globe, Download, HelpCircle, Check, Trash2, Layers } from "lucide-react";
import { useI18n } from "../../shared/i18n";

export interface CommandItem {
  id: string;
  category: string;
  label: string;
  shortcut?: string;
  icon: React.ReactNode;
  perform: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateSection: (sectionId: string) => void;
  onSaveDraft: () => void;
  onExportDocx: () => void;
  onLoadSample: () => void;
  onClearForm: () => void;
  onOpenShortcuts: () => void;
  onOpenTemplateSelector?: () => void;
  onOpenPartySearch?: () => void;
  onOpenPropertySearch?: () => void;
  onOpenPilotFeedback?: () => void;
  onOpenHistory?: () => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigateSection,
  onSaveDraft,
  onExportDocx,
  onLoadSample,
  onClearForm,
  onOpenShortcuts,
  onOpenTemplateSelector,
  onOpenPartySearch,
  onOpenPropertySearch,
  onOpenPilotFeedback,
  onOpenHistory,
  theme,
  onToggleTheme,
}) => {
  const { lang, setLang, t } = useI18n();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const items: CommandItem[] = [
    {
      id: "export-docx",
      category: "Draft Actions",
      label: lang === "mr" ? "दस्त निर्मिती व डाऊनलोड (DOCX)" : "Generate & Download DOCX Deed",
      shortcut: "Ctrl+E",
      icon: <Download size={16} color="var(--brand-500)" />,
      perform: () => {
        onExportDocx();
        onClose();
      },
    },
    {
      id: "select-template",
      category: "Draft Actions",
      label: lang === "mr" ? "दस्त साचा निवडा / बदला (Select Template)" : "Change Deed Template",
      icon: <Layers size={16} color="var(--brand-600)" />,
      perform: () => {
        if (onOpenTemplateSelector) onOpenTemplateSelector();
        onClose();
      },
    },
    {
      id: "save-draft",
      category: "Draft Actions",
      label: lang === "mr" ? "मसुदा ब्राउझरमध्ये जतन करा" : "Save Draft to Browser Storage",
      shortcut: "Ctrl+S",
      icon: <Zap size={16} color="var(--brand-500)" />,
      perform: () => {
        onSaveDraft();
        onClose();
      },
    },
    {
      id: "load-sample",
      category: "Draft Actions",
      label: lang === "mr" ? "नागपूर भूखंड नमुना डेटा भरा" : "Load Nagpur Plot Sample Preset",
      shortcut: "Ctrl+L",
      icon: <FileText size={16} color="var(--brand-600)" />,
      perform: () => {
        onLoadSample();
        onClose();
      },
    },
    {
      id: "clear-form",
      category: "Draft Actions",
      label: lang === "mr" ? "फॉर्म साफ करा (सर्व नोंदी काढा)" : "Clear Form Fields",
      icon: <Trash2 size={16} color="var(--danger-600)" />,
      perform: () => {
        onClearForm();
        onClose();
      },
    },
    ...(onOpenPartySearch
      ? [
          {
            id: "reuse-party",
            category: "Actions",
            label: lang === "mr" ? "जतन केलेले पक्षकार निवडा (Party Reuse)" : "Reuse Saved Party",
            icon: <Zap size={16} />,
            perform: () => {
              onOpenPartySearch();
              onClose();
            },
          },
        ]
      : []),
    ...(onOpenPropertySearch
      ? [
          {
            id: "reuse-property",
            category: "Actions",
            label: lang === "mr" ? "जतन केलेली मिळकत निवडा (Property Reuse)" : "Reuse Saved Property",
            icon: <Zap size={16} />,
            perform: () => {
              onOpenPropertySearch();
              onClose();
            },
          },
        ]
      : []),
    ...(onOpenPilotFeedback
      ? [
          {
            id: "pilot-feedback",
            category: "Actions",
            label: lang === "mr" ? "पायलट अभिप्राय नोंदवा (Feedback)" : "Log Pilot Feedback & Corrections",
            icon: <HelpCircle size={16} />,
            perform: () => {
              onOpenPilotFeedback();
              onClose();
            },
          },
        ]
      : []),
    ...(onOpenHistory
      ? [
          {
            id: "view-history",
            category: "Navigation",
            label: lang === "mr" ? "दस्त नोंदवही उघडा (Document History)" : "View Document History",
            icon: <FileText size={16} />,
            perform: () => {
              onOpenHistory();
              onClose();
            },
          },
        ]
      : []),
    {
      id: "sec-parties",
      category: "Jump to Section",
      label: lang === "mr" ? "पक्षकार तपशील (Parties)" : "Jump to Parties Details",
      icon: <FileText size={16} />,
      perform: () => {
        onNavigateSection("parties");
        onClose();
      },
    },
    {
      id: "sec-property",
      category: "Jump to Section",
      label: lang === "mr" ? "मिळकतीचे वर्णन (Property Schedule)" : "Jump to Property Schedule",
      icon: <FileText size={16} />,
      perform: () => {
        onNavigateSection("property_details");
        onClose();
      },
    },
    {
      id: "sec-boundaries",
      category: "Jump to Section",
      label: lang === "mr" ? "चतुःसीमा (Boundaries)" : "Jump to Boundaries",
      icon: <FileText size={16} />,
      perform: () => {
        onNavigateSection("boundaries");
        onClose();
      },
    },
    {
      id: "sec-financial",
      category: "Jump to Section",
      label: lang === "mr" ? "मोबदला व देय रक्कम (Financial Terms)" : "Jump to Consideration & Terms",
      icon: <FileText size={16} />,
      perform: () => {
        onNavigateSection("financial_details");
        onClose();
      },
    },
    {
      id: "sec-witnesses",
      category: "Jump to Section",
      label: lang === "mr" ? "साक्षीदार (Witnesses)" : "Jump to Witnesses",
      icon: <FileText size={16} />,
      perform: () => {
        onNavigateSection("witnesses");
        onClose();
      },
    },
    {
      id: "toggle-theme",
      category: "Preferences",
      label: theme === "dark" ? "Switch to Light Theme" : "Switch to Dark Theme",
      shortcut: "Ctrl+T",
      icon: theme === "dark" ? <Sun size={16} /> : <Moon size={16} />,
      perform: () => {
        onToggleTheme();
        onClose();
      },
    },
    {
      id: "toggle-lang",
      category: "Preferences",
      label: lang === "mr" ? "Switch to English UI" : "मराठी इंटरफेस निवडा",
      shortcut: "Ctrl+G",
      icon: <Globe size={16} />,
      perform: () => {
        setLang(lang === "mr" ? "en" : "mr");
        onClose();
      },
    },
    {
      id: "shortcuts-sheet",
      category: "Preferences",
      label: lang === "mr" ? "कीबोर्ड शॉर्टकट्स मार्गदर्शक" : "View Keyboard Shortcuts Cheat Sheet",
      shortcut: "?",
      icon: <HelpCircle size={16} />,
      perform: () => {
        onOpenShortcuts();
        onClose();
      },
    },
  ];

  const filtered = items.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % (filtered.length || 1));
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      e.preventDefault();
      filtered[selectedIndex].perform();
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1200,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "14vh",
        backgroundColor: "var(--surface-overlay)",
        backdropFilter: "blur(4px)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "580px",
          backgroundColor: "var(--surface-card)",
          borderRadius: "var(--radius-card)",
          boxShadow: "var(--shadow-dialog)",
          border: "1px solid var(--line-medium)",
          overflow: "hidden",
          animation: "scaleUp 150ms cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* Search Input bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "16px 20px",
            borderBottom: "1px solid var(--line-subtle)",
            backgroundColor: "var(--surface-subtle)",
          }}
        >
          <Search size={18} color="var(--brand-600)" className="shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder={t("actions.search")}
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              fontSize: "0.9375rem",
              fontFamily: "var(--font-ui)",
              color: "var(--text-primary)",
              outline: "none",
            }}
          />
          <kbd
            style={{
              fontSize: "0.6875rem",
              padding: "2px 6px",
              borderRadius: "4px",
              backgroundColor: "var(--surface-sunken)",
              color: "var(--text-secondary)",
              border: "1px solid var(--line-medium)",
              fontFamily: "var(--font-mono)",
            }}
          >
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: "360px", overflowY: "auto", padding: "8px 0" }}>
          {filtered.length === 0 ? (
            <div style={{ padding: "24px", textAlign: "center", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
              {lang === "mr" ? "कोणतीही कृती सापडली नाही." : "No matching actions found."}
            </div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => item.perform()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 20px",
                    cursor: "pointer",
                    backgroundColor: isSelected ? "var(--brand-100)" : "transparent",
                    color: isSelected ? "var(--brand-900)" : "var(--text-primary)",
                    transition: "background-color 80ms ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <span style={{ color: isSelected ? "var(--brand-600)" : "var(--text-secondary)" }}>
                      {item.icon}
                    </span>
                    <div>
                      <div style={{ fontSize: "0.875rem", fontWeight: isSelected ? 600 : 500 }}>
                        {item.label}
                      </div>
                      <div style={{ fontSize: "0.6875rem", color: "var(--text-tertiary)" }}>
                        {item.category}
                      </div>
                    </div>
                  </div>

                  {item.shortcut && (
                    <kbd
                      style={{
                        fontSize: "0.6875rem",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        backgroundColor: "var(--surface-sunken)",
                        color: "var(--text-secondary)",
                        border: "1px solid var(--line-medium)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {item.shortcut}
                    </kbd>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

