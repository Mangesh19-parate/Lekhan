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
      <div className="fixed bottom-5 left-5 z-[1100] flex flex-col gap-2 max-w-sm w-[calc(100%-40px)] pointer-events-none">
        {toasts.map((t) => {
          const isError = t.type === "error";
          const isSuccess = t.type === "success";

          return (
            <div
              key={t.id}
              role="status"
              aria-live="polite"
              className={`pointer-events-auto bg-card text-text-primary border rounded-card shadow-dialog p-4 flex items-start gap-3 animate-fade-in font-ui ${
                isError
                  ? "border-danger-border bg-danger-tint/20 dark:bg-card"
                  : isSuccess
                  ? "border-success-border bg-success-tint/20 dark:bg-card"
                  : "border-line-medium bg-card"
              }`}
            >
              <div className="shrink-0 mt-0.5">
                {isSuccess && <CheckCircle2 size={18} className="text-success-600 dark:text-success-500" />}
                {isError && <AlertCircle size={18} className="text-danger-600 dark:text-danger-500" />}
                {!isSuccess && !isError && <Info size={18} className="text-brand-500" />}
              </div>

              <div className="flex-1 min-w-0">
                <div className="font-semibold text-sm">{t.title}</div>
                {t.description && (
                  <div className="text-xs text-text-secondary mt-0.5">{t.description}</div>
                )}
                {t.correlationId && (
                  <div className="mt-1.5 flex items-center gap-1.5 text-xs text-text-tertiary">
                    <span className="font-mono text-[11px]">ID: {t.correlationId}</span>
                    <button
                      type="button"
                      onClick={() => handleCopyCorrelationId(t.correlationId!)}
                      className="p-0.5 hover:text-text-primary rounded"
                      title="Copy correlation ID"
                    >
                      {copiedId === t.correlationId ? <Check size={12} /> : <Copy size={12} />}
                    </button>
                  </div>
                )}
                {t.action && (
                  <button
                    type="button"
                    onClick={t.action.onClick}
                    className="mt-2 text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline"
                  >
                    {t.action.label}
                  </button>
                )}
              </div>

              <button
                type="button"
                onClick={() => removeToast(t.id)}
                className="shrink-0 p-1 text-text-tertiary hover:text-text-primary rounded-input hover:bg-sunken transition-colors"
              >
                <X size={15} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};
