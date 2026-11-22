import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Select, Input } from "../../shared/components";
import {
  Settings,
  ShieldCheck,
  Globe,
  Clock,
  Save,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

interface SystemSettingsViewProps {
  onNavigate: (viewId: string) => void;
}

export const SystemSettingsView: React.FC<SystemSettingsViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [retentionClass, setRetentionClass] = useState("matter_lifecycle");
  const [digitsSetting, setDigitsSetting] = useState("western");
  const [idleMinutes, setIdleMinutes] = useState("30");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSystemSettings()
      .then((res) => {
        if (res.retention_class) setRetentionClass(res.retention_class);
        if (res.digits_setting) setDigitsSetting(res.digits_setting);
        if (res.idle_minutes) setIdleMinutes(String(res.idle_minutes));
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to load system settings";
        setErrorMessage(msg);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setErrorMessage(null);
    try {
      const parsedMinutes = parseInt(idleMinutes, 10);
      if (isNaN(parsedMinutes) || parsedMinutes < 5 || parsedMinutes > 720) {
        throw new Error("Idle timeout must be between 5 and 720 minutes.");
      }
      await api.updateSystemSettings({
        retention_class: retentionClass,
        digits_setting: digitsSetting,
        idle_minutes: parsedMinutes,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save settings";
      setErrorMessage(msg);
    } finally {
      setSaving(false);
    }
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
            <Badge variant="approved" size="md" label="Tenant Policy (Audited)" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "डॉक्युमेंट धारणा कालावधी, संख्या स्वरूप, सत्र समाप्ती व भाषा प्राधान्ये."
              : "Tenant retention policies, statutory numbering preferences, and cryptographic session limits."}
          </p>
        </div>

        <Button
          size="sm"
          variant="primary"
          onClick={handleSave}
          disabled={saving || loading}
          leftIcon={<Save size={14} />}
        >
          {saving
            ? (lang === "mr" ? "जतन होत आहे..." : "Saving...")
            : saved
            ? (lang === "mr" ? "जतन झाले!" : "Settings Saved!")
            : (lang === "mr" ? "बदल जतन करा" : "Save Changes")}
        </Button>
      </div>

      {/* Alert Banners */}
      {saved && (
        <div style={{ padding: "12px 16px", borderRadius: "var(--radius-input)", backgroundColor: "var(--brand-100)", border: "1px solid var(--brand-500)", color: "var(--brand-900)", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <CheckCircle2 size={16} color="var(--brand-600)" />
          <span>{lang === "mr" ? "सिस्टम सेटिंग्ज यशस्वीरित्या जतन केल्या गेल्या आहेत आणि ऑडिट लॉगमध्ये नोंद झाली आहे." : "System settings persisted to backend and recorded in immutable audit log."}</span>
        </div>
      )}

      {errorMessage && (
        <div style={{ padding: "12px 16px", borderRadius: "var(--radius-input)", backgroundColor: "var(--danger-100, #FEE2E2)", border: "1px solid var(--danger-500, #EF4444)", color: "var(--danger-900, #7F1D1D)", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <AlertTriangle size={16} color="#DC2626" />
          <span>{errorMessage}</span>
        </div>
      )}

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
