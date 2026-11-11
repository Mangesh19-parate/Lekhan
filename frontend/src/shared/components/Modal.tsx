import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

const SIZE_MAP: Record<string, string> = {
  sm: "440px",
  md: "560px",
  lg: "720px",
  xl: "880px",
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth,
  size = "md",
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const resolvedMaxWidth = maxWidth || SIZE_MAP[size] || "560px";

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
        backgroundColor: "var(--surface-overlay)",
        backdropFilter: "blur(3px)",
        animation: "fadeIn 150ms ease-out",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        style={{
          width: "100%",
          maxWidth: resolvedMaxWidth,
          backgroundColor: "var(--surface-card)",
          borderRadius: "var(--radius-card)",
          boxShadow: "var(--shadow-dialog)",
          border: "1px solid var(--line-medium)",
          display: "flex",
          flexDirection: "column",
          maxHeight: "90vh",
          overflow: "hidden",
          animation: "scaleUp 180ms cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "18px 24px",
            borderBottom: "1px solid var(--line-subtle)",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            backgroundColor: "var(--surface-subtle)",
          }}
        >
          <div>
            <h2
              id="modal-title"
              style={{
                margin: 0,
                fontSize: "1.125rem",
                fontWeight: 700,
                color: "var(--brand-900)",
                fontFamily: "var(--font-ui)",
              }}
            >
              {title}
            </h2>
            {description && (
              <p
                style={{
                  margin: "4px 0 0 0",
                  fontSize: "0.8125rem",
                  color: "var(--text-secondary)",
                }}
              >
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-secondary)",
              padding: "6px",
              borderRadius: "var(--radius-input)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background-color var(--transition-fast), color var(--transition-fast)",
            }}
            className="hover:bg-[var(--surface-sunken)] hover:text-[var(--text-primary)]"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div
          style={{
            padding: "24px",
            overflowY: "auto",
            flex: 1,
            fontSize: "0.875rem",
            color: "var(--text-primary)",
          }}
        >
          {children}
        </div>

        {/* Optional Footer */}
        {footer && (
          <div
            style={{
              padding: "16px 24px",
              borderTop: "1px solid var(--line-subtle)",
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              gap: "12px",
              backgroundColor: "var(--surface-subtle)",
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

