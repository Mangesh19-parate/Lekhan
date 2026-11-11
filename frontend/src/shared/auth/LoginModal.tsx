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
  const { login } = useAuth();
  const { toast } = useToast();

  const [email, setEmail] = useState("drafter@lekhan.local");
  const [password, setPassword] = useState("ValidPassword123!");
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    try {
      await login(email, password);
      toast({
        type: "success",
        title: "प्रवेश यशस्वी (Login Successful)",
        description: `Signed in as ${email}`,
      });
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Login failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="प्रणाली प्रवेश (Lekhan Login)"
      description="Secure advocate and drafter authentication per docs/AUTH.md"
      maxWidth="460px"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
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
    </Modal>
  );
};
