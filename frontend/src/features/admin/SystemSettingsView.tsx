import React, { useState } from "react";
import { useI18n } from "../../shared/i18n";
import { Button, Badge, Card, Select, Input } from "../../shared/components";
import {
  Settings,
  ShieldCheck,
  Globe,
  Clock,
  Save,
  CheckCircle2,
} from "lucide-react";

interface SystemSettingsViewProps {
  onNavigate: (viewId: string) => void;
}

export const SystemSettingsView: React.FC<SystemSettingsViewProps> = ({ onNavigate }) => {
  const { lang, setLang } = useI18n();
  const [retentionClass, setRetentionClass] = useState("matter_lifecycle");
  const [digitsSetting, setDigitsSetting] = useState("western");
  const [idleMinutes, setIdleMinutes] = useState("30");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "सिस्टम प्राधान्ये व सेटिंग्ज (System Settings)" : "System Settings & Statutory Config"}
            </h1>
            <Badge variant="approved" size="md" label="Tenant Policy" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "डॉक्युमेंट धारणा कालावधी, संख्या स्वरूप, सत्र समाप्ती व भाषा प्राधान्ये."
              : "Tenant retention policies, statutory numbering preferences, and cryptographic session limits."}
          </p>
        </div>

        <Button size="sm" variant="primary" onClick={handleSave} leftIcon={<Save size={14} />}>
          {saved ? (lang === "mr" ? "जतन झाले!" : "Settings Saved!") : (lang === "mr" ? "बदल जतन करा" : "Save Changes")}
        </Button>
      </div>

      {/* 2. Settings Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
        {/* Retention Policy */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
            <ShieldCheck size={18} color="var(--brand-600)" />
            <span>{lang === "mr" ? "दस्त धारणा धोरण (Retention Policy)" : "Statutory Document Retention"}</span>
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0 }}>
            Governs how long generated deed snapshots and files are kept in the tenant store.
          </p>
          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Retention Class:</label>
            <Select
              value={retentionClass}
              onChange={(e) => setRetentionClass(e.target.value)}
              options={[
                { label: "Matter Lifecycle (Permanent Statutory)", value: "matter_lifecycle" },
                { label: "12-Year Statutory Limitation", value: "limitation_12yr" },
                { label: "30-Year Property Search Archive", value: "search_30yr" },
              ]}
            />
          </div>
        </Card>

        {/* Numbering & Formatting */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
            <Globe size={18} color="var(--brand-600)" />
            <span>{lang === "mr" ? "अंक व चलन स्वरूप (Number Formatting)" : "Number & Currency Formatting"}</span>
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0 }}>
            Indian grouping system (13,10,000) with Devanagari or Western script digits.
          </p>
          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Digits Script Default:</label>
            <Select
              value={digitsSetting}
              onChange={(e) => setDigitsSetting(e.target.value)}
              options={[
                { label: "Western Digits (1, 2, 3...) - Standard Legal", value: "western" },
                { label: "Devanagari Digits (१, २, ३...) - Traditional", value: "devanagari" },
              ]}
            />
          </div>
        </Card>

        {/* Security & Sessions */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
            <Clock size={18} color="var(--brand-600)" />
            <span>{lang === "mr" ? "सत्र समाप्ती वेळ (Session Policy)" : "Session & Security Policy"}</span>
          </div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0 }}>
            Automated session expiration after inactivity to safeguard draft legal deeds.
          </p>
          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Idle Inactivity Timeout (Minutes):</label>
            <Input
              type="number"
              value={idleMinutes}
              onChange={(e) => setIdleMinutes(e.target.value)}
            />
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            Absolute session lifetime: 12 Hours (enforced by server token rotation)
          </div>
        </Card>
      </div>
    </div>
  );
};

