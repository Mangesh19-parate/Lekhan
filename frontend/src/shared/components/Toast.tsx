import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertCircle, Info, X, Copy, Check } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  title: string;
  description?: string;
  correlationId?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  durationMs?: number;
}

interface ToastContextType {
  toast: (msg: Omit<ToastMessage, "id">) => void;
}

const ToastContext = createContext<ToastContextType>({
  toast: () => {},
});

export const useToast = () => useContext(ToastContext);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (msg: Omit<ToastMessage, "id">) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      const newToast: ToastMessage = { ...msg, id };

      setToasts((prev) => [...prev, newToast]);

      const duration = msg.durationMs ?? (msg.type === "error" ? 8000 : 4000);
      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const handleCopyCorrelationId = (cid: string) => {
    navigator.clipboard.writeText(cid);
    setCopiedId(cid);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast container (bottom-left per DESIGN.md §4.8) */}
      <div
        style={{
          position: "fixed",
          bottom: "20px",
          left: "20px",
          zIndex: 1100,
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          maxWidth: "420px",
          width: "calc(100% - 40px)",
          pointerEvents: "none",
        }}
      >
        {toasts.map((t) => {
          const isError = t.type === "error";
          const isSuccess = t.type === "success";

          return (
            <div
              key={t.id}
              role="status"
              aria-live="polite"
              style={{
                pointerEvents: "auto",
                backgroundColor: "var(--surface-card)",
                color: "var(--text-primary)",
                border: `1px solid ${isError ? "var(--danger-border)" : isSuccess ? "var(--success-border)" : "var(--line-medium)"}`,
                borderRadius: "var(--radius-card)",
                boxShadow: "var(--shadow-elevated)",
                padding: "14px 16px",
                display: "flex",
                alignItems: "flex-start",
                gap: "12px",
                animation: "slideInUp 200ms cubic-bezier(0.16, 1, 0.3, 1)",
              }}
            >
              <div className="shrink-0 mt-0.5">
                {isSuccess && <CheckCircle2 size={18} color="var(--success-600)" />}
                {isError && <AlertCircle size={18} color="var(--danger-600)" />}
                {!isSuccess && !isError && <Info size={18} color="var(--brand-500)" />}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{t.title}</div>
                {t.description && (
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                    {t.description}
                  </div>
                )}
                {t.correlationId && (
                  <div
                    style={{
                      marginTop: "6px",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.75rem",
                      color: "var(--text-tertiary)",
                    }}
                  >
                    <span>ID: {t.correlationId}</span>
                    <button
                      type="button"
                      onClick={() => handleCopyCorrelationId(t.correlationId!)}
                      style={{
                        background: "none",
                        border: "none",
                        padding: "2px 4px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "2px",
                        color: "var(--brand-600)",
                        fontWeight: 600,
                      }}
                    >
                      {copiedId === t.correlationId ? <Check size={12} /> : <Copy size={12} />}
                      <span>{copiedId === t.correlationId ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                )}
              </div>

              {t.action && (
                <button
                  type="button"
                  onClick={() => {
                    t.action!.onClick();
                    removeToast(t.id);
                  }}
                  style={{
                    backgroundColor: "var(--surface-sunken)",
                    border: "none",
                    borderRadius: "var(--radius-pill)",
                    padding: "4px 10px",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: "var(--brand-600)",
                    cursor: "pointer",
                  }}
                >
                  {t.action.label}
                </button>
              )}

              <button
                type="button"
                onClick={() => removeToast(t.id)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-tertiary)",
                  cursor: "pointer",
                  padding: "2px",
                }}
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

