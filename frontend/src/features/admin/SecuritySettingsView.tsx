import React, { useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, type MfaSetupResponse } from "../../shared/api";
import { Card, Button, Input, Badge } from "../../shared/components";
import {
  ShieldCheck,
  KeyRound,
  Lock,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Eye,
  EyeOff,
  Smartphone,
} from "lucide-react";

interface SecuritySettingsViewProps {
  onNavigate: (viewId: string) => void;
}

export const SecuritySettingsView: React.FC<SecuritySettingsViewProps> = () => {
  const { lang } = useI18n();

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdMessage, setPwdMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // MFA Setup State
  const [mfaSetupData, setMfaSetupData] = useState<MfaSetupResponse | null>(null);
  const [mfaSetupLoading, setMfaSetupLoading] = useState(false);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaPassword, setMfaPassword] = useState("");
  const [mfaEnabling, setMfaEnabling] = useState(false);
  const [mfaMessage, setMfaMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Disable MFA State
  const [showDisableMfa, setShowDisableMfa] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [disablePassword, setDisablePassword] = useState("");
  const [disabling, setDisabling] = useState(false);

  // Password Visibility
  const [showPwd, setShowPwd] = useState(false);

  // Handle Password Change
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdMessage(null);

    if (newPassword.length < 12) {
      setPwdMessage({
        type: "error",
        text: lang === "mr" ? "पासवर्ड किमान १२ अक्षरांचा असावा." : "New password must be at least 12 characters (docs/AUTH.md).",
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPwdMessage({
        type: "error",
        text: lang === "mr" ? "नवीन पासवर्ड आणि पुष्टीकरण पासवर्ड जुळत नाहीत." : "New password and confirmation do not match.",
      });
      return;
    }

    setPwdLoading(true);
    try {
      const res = await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwdMessage({
        type: "success",
        text: res.message || (lang === "mr" ? "पासवर्ड यशस्वीरित्या बदलला गेला." : "Password updated successfully."),
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Password update failed.";
      setPwdMessage({ type: "error", text: msg });
    } finally {
      setPwdLoading(false);
    }
  };

  // Step 1: Initiate MFA Setup
  const handleInitiateMfaSetup = async () => {
    setMfaSetupLoading(true);
    setMfaMessage(null);
    try {
      const data = await api.setupMfa();
      setMfaSetupData(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to initiate MFA setup.";
      setMfaMessage({ type: "error", text: msg });
    } finally {
      setMfaSetupLoading(false);
    }
  };

  // Step 2: Verify & Enable MFA
  const handleEnableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaCode || !mfaPassword) return;

    setMfaEnabling(true);
    setMfaMessage(null);
    try {
      const res = await api.enableMfa({
        code: mfaCode.trim(),
        password: mfaPassword,
      });
      setMfaMessage({
        type: "success",
        text: res.message || (lang === "mr" ? "MFA यशस्वीरित्या सुरू केले." : "Two-Factor Authentication enabled successfully."),
      });
      setMfaSetupData(null);
      setMfaCode("");
      setMfaPassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to verify and activate MFA.";
      setMfaMessage({ type: "error", text: msg });
    } finally {
      setMfaEnabling(false);
    }
  };

  // Handle Disable MFA
  const handleDisableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    setDisabling(true);
    setMfaMessage(null);
    try {
      const res = await api.disableMfa({
        code: disableCode.trim(),
        password: disablePassword,
      });
      setMfaMessage({
        type: "success",
        text: res.message || (lang === "mr" ? "MFA बंद केले गेले." : "MFA disabled successfully."),
      });
      setShowDisableMfa(false);
      setDisableCode("");
      setDisablePassword("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to disable MFA.";
      setMfaMessage({ type: "error", text: msg });
    } finally {
      setDisabling(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "960px", margin: "0 auto" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
          {lang === "mr" ? "सुरक्षा व खाते संरक्षण" : "Chamber Security & Credentials"}
        </h1>
        <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
          {lang === "mr"
            ? "पासवर्ड बदला आणि TOTP आधारित द्वि-घटक प्रमाणीकरण (MFA) सक्रिय करा."
            : "Manage your credentials, password rotation (Argon2id), and TOTP Multi-Factor Authentication (docs/AUTH.md)."}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        {/* CARD 1: PASSWORD CHANGE */}
        <Card style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "var(--brand-100)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--brand-700)",
              }}
            >
              <KeyRound size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0 }}>
                {lang === "mr" ? "पासवर्ड बदला" : "Change Password"}
              </h2>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Minimum 12 characters, Argon2id encryption
              </span>
            </div>
          </div>

          {pwdMessage && (
            <div
              style={{
                padding: "10px 12px",
                borderRadius: "var(--radius-input)",
                fontSize: "0.8125rem",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                backgroundColor: pwdMessage.type === "error" ? "var(--danger-50, #FEF2F2)" : "var(--brand-50, #F0FDF4)",
                border: `1px solid ${pwdMessage.type === "error" ? "var(--danger-border, #FCA5A5)" : "var(--brand-500, #22C55E)"}`,
                color: pwdMessage.type === "error" ? "var(--danger-600, #991B1B)" : "var(--brand-900, #14532D)",
              }}
            >
              {pwdMessage.type === "error" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
              <span>{pwdMessage.text}</span>
            </div>
          )}

          <form onSubmit={handlePasswordChange} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <Input
              id="current-password"
              label={lang === "mr" ? "सध्याचा पासवर्ड (Current Password)" : "Current Password"}
              type={showPwd ? "text" : "password"}
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />

            <Input
              id="new-password"
              label={lang === "mr" ? "नवीन पासवर्ड (New Password, min 12 chars)" : "New Password (min 12 chars)"}
              type={showPwd ? "text" : "password"}
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••••••"
            />

            <Input
              id="confirm-password"
              label={lang === "mr" ? "नवीन पासवर्डची पुष्टी (Confirm New Password)" : "Confirm New Password"}
              type={showPwd ? "text" : "password"}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••••••"
            />

            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-secondary)",
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  padding: 0,
                }}
              >
                {showPwd ? <EyeOff size={14} /> : <Eye size={14} />}
                <span>{showPwd ? "Hide passwords" : "Show passwords"}</span>
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={pwdLoading}
              leftIcon={<Lock size={16} />}
              style={{ marginTop: "4px" }}
            >
              {lang === "mr" ? "पासवर्ड अपडेट करा" : "Update Password"}
            </Button>
          </form>
        </Card>

        {/* CARD 2: MFA TOTP SETUP & STATUS */}
        <Card style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "var(--brand-100)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--brand-700)",
              }}
            >
              <Smartphone size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0 }}>
                {lang === "mr" ? "द्वि-घटक प्रमाणीकरण (TOTP MFA)" : "Two-Factor Authentication (MFA)"}
              </h2>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Google Authenticator, Authy, or 1Password
              </span>
            </div>
          </div>

          {mfaMessage && (
            <div
              style={{
                padding: "10px 12px",
                borderRadius: "var(--radius-input)",
                fontSize: "0.8125rem",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                backgroundColor: mfaMessage.type === "error" ? "var(--danger-50, #FEF2F2)" : "var(--brand-50, #F0FDF4)",
                border: `1px solid ${mfaMessage.type === "error" ? "var(--danger-border, #FCA5A5)" : "var(--brand-500, #22C55E)"}`,
                color: mfaMessage.type === "error" ? "var(--danger-600, #991B1B)" : "var(--brand-900, #14532D)",
              }}
            >
              {mfaMessage.type === "error" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
              <span>{mfaMessage.text}</span>
            </div>
          )}

          {!mfaSetupData && !showDisableMfa && (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div
                style={{
                  padding: "12px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: "var(--surface-sunken)",
                  fontSize: "0.8125rem",
                  color: "var(--text-secondary)",
                }}
              >
                MFA adds a critical layer of defense for legal drafting and client record access. When enrolled, every
                login requires your password plus a 6-digit code.
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleInitiateMfaSetup}
                  isLoading={mfaSetupLoading}
                  leftIcon={<ShieldCheck size={16} />}
                >
                  {lang === "mr" ? "MFA सक्रिय करा (Enrol MFA)" : "Enrol MFA Authenticator"}
                </Button>

                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => setShowDisableMfa(true)}
                  style={{ color: "var(--danger-600)" }}
                >
                  {lang === "mr" ? "MFA बंद करा" : "Disable MFA"}
                </Button>
              </div>
            </div>
          )}

          {/* MFA SETUP FORM (STEP 2: ENROL & VERIFY) */}
          {mfaSetupData && (
            <form onSubmit={handleEnableMfa} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div
                style={{
                  padding: "10px 12px",
                  backgroundColor: "var(--surface-sunken)",
                  borderRadius: "var(--radius-input)",
                  fontSize: "0.8125rem",
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: "4px" }}>1. Secret Key (enter into your app):</div>
                <div
                  style={{
                    fontFamily: "monospace",
                    backgroundColor: "#FFFFFF",
                    padding: "6px 8px",
                    borderRadius: "4px",
                    border: "1px solid var(--line-medium)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span>{mfaSetupData.secret}</span>
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(mfaSetupData.secret)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--brand-600)" }}
                    title="Copy Secret"
                  >
                    <Copy size={14} />
                  </button>
                </div>
              </div>

              {/* Single-Use Recovery Codes */}
              {mfaSetupData.recovery_codes && mfaSetupData.recovery_codes.length > 0 && (
                <div
                  style={{
                    padding: "10px 12px",
                    backgroundColor: "#FFFBEB",
                    borderRadius: "var(--radius-input)",
                    border: "1px solid #FDE68A",
                    fontSize: "0.75rem",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "#92400E", marginBottom: "4px" }}>
                    2. Emergency Recovery Codes (Save these securely):
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px", fontFamily: "monospace" }}>
                    {mfaSetupData.recovery_codes.map((code, idx) => (
                      <div key={idx} style={{ color: "#78350F" }}>
                        • {code}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confirm with Password & TOTP Code */}
              <Input
                id="mfa-verify-code"
                label={lang === "mr" ? "ॲपमधील ६-अंकी कोड" : "6-digit code from Authenticator"}
                type="text"
                required
                maxLength={6}
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
              />

              <Input
                id="mfa-verify-password"
                label={lang === "mr" ? "तुमचा पासवर्ड" : "Your Password to confirm"}
                type="password"
                required
                value={mfaPassword}
                onChange={(e) => setMfaPassword(e.target.value)}
              />

              <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={mfaEnabling}
                  leftIcon={<CheckCircle2 size={16} />}
                >
                  {lang === "mr" ? "सत्यापित करा व सुरू करा" : "Verify & Activate MFA"}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="md"
                  onClick={() => setMfaSetupData(null)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          )}

          {/* DISABLE MFA FORM */}
          {showDisableMfa && (
            <form onSubmit={handleDisableMfa} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div
                style={{
                  padding: "10px 12px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: "var(--danger-50, #FEF2F2)",
                  color: "var(--danger-600, #991B1B)",
                  fontSize: "0.8125rem",
                }}
              >
                Disabling MFA lowers your chamber account security. You must supply your password and an active TOTP code.
              </div>

              <Input
                id="disable-mfa-code"
                label="6-digit TOTP code"
                type="text"
                required
                maxLength={6}
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
              />

              <Input
                id="disable-mfa-pwd"
                label="Your Password"
                type="password"
                required
                value={disablePassword}
                onChange={(e) => setDisablePassword(e.target.value)}
              />

              <div style={{ display: "flex", gap: "8px" }}>
                <Button
                  type="submit"
                  variant="danger"
                  size="md"
                  isLoading={disabling}
                >
                  Confirm Disable MFA
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="md"
                  onClick={() => setShowDisableMfa(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </Card>
      </div>
    </div>
  );
};
