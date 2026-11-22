import React, { useState } from "react";
import { Modal, Input, Button } from "../components";
import { useAuth } from "./AuthContext";
import { useToast } from "../components/Toast";
import { LogIn, KeyRound, UserCheck, ShieldAlert } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const LoginModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { login, verifyMfaLogin } = useAuth();
  const { toast } = useToast();

  const [step, setStep] = useState<"credentials" | "mfa">("credentials");
  const [email, setEmail] = useState("drafter@lekhan.local");
  const [password, setPassword] = useState("ValidPassword123!");
  const [totpCode, setTotpCode] = useState("");
  const [recoveryCode, setRecoveryCode] = useState("");
  const [useRecovery, setUseRecovery] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleQuickFill = (role: "drafter" | "admin") => {
    if (role === "drafter") {
      setEmail("drafter@lekhan.local");
      setPassword("ValidPassword123!");
    } else {
      setEmail("admin@lekhan.local");
      setPassword("ValidPassword123!");
    }
    setErrorMsg(null);
  };

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await login(email, password);
      if (res.mfaRequired) {
        setStep("mfa");
        setErrorMsg(null);
      } else {
        toast({
          type: "success",
          title: "प्रवेश यशस्वी (Login Successful)",
          description: `Signed in as ${email}`,
        });
        onClose();
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed.";
      setErrorMsg(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    try {
      await verifyMfaLogin(
        useRecovery ? undefined : totpCode.trim(),
        useRecovery ? recoveryCode.trim() : undefined
      );
      toast({
        type: "success",
        title: "MFA प्रमाणीकरण यशस्वी (MFA Verified)",
        description: `Signed in as ${email}`,
      });
      onClose();
      setStep("credentials");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "MFA verification failed.";
      setErrorMsg(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        setStep("credentials");
        setErrorMsg(null);
        onClose();
      }}
      title={step === "mfa" ? "द्वि-घटक प्रमाणीकरण (Two-Factor Authentication)" : "प्रणाली प्रवेश (Lekhan Login)"}
      description={step === "mfa" ? "Enter the 6-digit TOTP from your authenticator app" : "Secure advocate and drafter authentication per docs/AUTH.md"}
      maxWidth="460px"
    >
      {step === "credentials" ? (
        <form onSubmit={handleCredentialsSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Synthetic Dev Quick Fill Banner */}
          <div
            style={{
              padding: "10px 14px",
              backgroundColor: "var(--surface-sunken)",
              borderRadius: "var(--radius-input)",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
              border: "1px solid var(--line-subtle)",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)" }}>
              Quick fill test credentials (Synthetic dev accounts):
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                pill
                onClick={() => handleQuickFill("drafter")}
                leftIcon={<UserCheck size={13} />}
              >
                Drafter (Nagpur)
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                pill
                onClick={() => handleQuickFill("admin")}
                leftIcon={<KeyRound size={13} />}
              >
                Admin Partner
              </Button>
            </div>
          </div>

          {errorMsg && (
            <div
              role="alert"
              style={{
                padding: "10px 14px",
                backgroundColor: "var(--danger-tint)",
                color: "var(--danger-600)",
                border: "1px solid var(--danger-border)",
                borderRadius: "var(--radius-input)",
                fontSize: "0.8125rem",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <ShieldAlert size={16} className="shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <Input
            id="login-email"
            label="ईमेल पत्ता (Email Address)"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="drafter@lekhan.local"
          />

          <Input
            id="login-password"
            label="पासवर्ड (Password)"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Button
            type="submit"
            variant="primary"
            pill
            size="md"
            isLoading={isLoading}
            leftIcon={<LogIn size={16} />}
            style={{ width: "100%", marginTop: "8px" }}
          >
            साइन इन करा (Sign In)
          </Button>
        </form>
      ) : (
        <form onSubmit={handleMfaSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {errorMsg && (
            <div
              role="alert"
              style={{
                padding: "10px 14px",
                backgroundColor: "var(--danger-tint)",
                color: "var(--danger-600)",
                border: "1px solid var(--danger-border)",
                borderRadius: "var(--radius-input)",
                fontSize: "0.8125rem",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <ShieldAlert size={16} className="shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {!useRecovery ? (
            <Input
              id="mfa-totp-code"
              label="६-अंकी कोड (6-Digit Authenticator Code)"
              type="text"
              required
              maxLength={6}
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
              placeholder="123456"
              autoFocus
            />
          ) : (
            <Input
              id="mfa-recovery-code"
              label="पुनर्प्राप्ती कोड (One-Time Recovery Code)"
              type="text"
              required
              value={recoveryCode}
              onChange={(e) => setRecoveryCode(e.target.value)}
              placeholder="XXXX-XXXX"
              autoFocus
            />
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <button
              type="button"
              onClick={() => {
                setUseRecovery(!useRecovery);
                setErrorMsg(null);
              }}
              style={{
                background: "none",
                border: "none",
                color: "var(--brand-600)",
                fontSize: "0.8125rem",
                cursor: "pointer",
                padding: 0,
                textDecoration: "underline",
              }}
            >
              {useRecovery ? "Use Authenticator TOTP App instead" : "Use One-Time Recovery Code"}
            </button>
            <button
              type="button"
              onClick={() => {
                setStep("credentials");
                setErrorMsg(null);
              }}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                fontSize: "0.8125rem",
                cursor: "pointer",
                padding: 0,
              }}
            >
              Back to Login
            </button>
          </div>

          <Button
            type="submit"
            variant="primary"
            pill
            size="md"
            isLoading={isLoading}
            leftIcon={<KeyRound size={16} />}
            style={{ width: "100%", marginTop: "8px" }}
          >
            सत्यापित करा (Verify MFA)
          </Button>
        </form>
      )}
    </Modal>
  );
};
