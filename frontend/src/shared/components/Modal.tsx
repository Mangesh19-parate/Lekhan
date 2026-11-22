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

const SIZE_CLASSES: Record<string, string> = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-900/60 dark:bg-black/75 backdrop-blur-sm animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        style={maxWidth ? { maxWidth } : undefined}
        className={`w-full ${SIZE_CLASSES[size] || "max-w-lg"} bg-card border border-line-subtle rounded-card shadow-dialog flex flex-col max-h-[90vh] overflow-hidden font-ui`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-line-subtle bg-subtle dark:bg-sunken/40">
          <div>
            <h2 id="modal-title" className="text-base font-semibold text-text-primary">
              {title}
            </h2>
            {description && (
              <p className="text-xs text-text-secondary mt-0.5">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="p-1 rounded-input text-text-secondary hover:text-text-primary hover:bg-sunken transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex-1 text-sm text-text-primary space-y-4">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2.5 p-4 border-t border-line-subtle bg-subtle dark:bg-sunken/40">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
