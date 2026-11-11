import React from "react";
import { AlertCircle } from "lucide-react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  requiredMarker?: string;
  leftAddon?: React.ReactNode;
  rightAddon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      id,
      label,
      helperText,
      error,
      required,
      requiredMarker,
      leftAddon,
      rightAddon,
      className = "",
      style,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);
    const helperId = helperText ? `${inputId}-helper` : undefined;
    const errorId = error ? `${inputId}-error` : undefined;

    return (
      <div className={`lekhan-input-group ${className}`} style={{ display: "flex", flexDirection: "column", gap: "6px", width: "100%" }}>
        {label && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label
              htmlFor={inputId}
              style={{
                fontSize: "0.8125rem",
                fontWeight: 600,
                color: "var(--text-primary)",
                userSelect: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              {label}
              {required && (
                <span
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    color: "var(--danger-600)",
                    textTransform: "uppercase",
                  }}
                >
                  {requiredMarker ? `(${requiredMarker})` : "*"}
                </span>
              )}
            </label>
          </div>
        )}

        <div
          style={{
            position: "relative",
            display: "flex",
            alignItems: "center",
            width: "100%",
          }}
        >
          {leftAddon && (
            <div
              style={{
                position: "absolute",
                left: "12px",
                display: "flex",
                alignItems: "center",
                pointerEvents: "none",
                color: "var(--text-tertiary)",
              }}
            >
              {leftAddon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={[errorId, helperId].filter(Boolean).join(" ") || undefined}
            required={required}
            className={`lekhan-input-field ${error ? "has-error" : ""}`}
            style={{
              width: "100%",
              height: "40px",
              padding: `0 ${rightAddon ? "40px" : "12px"} 0 ${leftAddon ? "38px" : "12px"}`,
              fontSize: "0.875rem",
              fontFamily: "var(--font-ui)",
              color: "var(--text-primary)",
              backgroundColor: disabled ? "var(--surface-sunken)" : "var(--surface-card)",
              border: `1px solid ${error ? "var(--danger-600)" : "var(--line-medium)"}`,
              borderRadius: "var(--radius-input)",
              transition: "border-color var(--transition-fast), box-shadow var(--transition-fast)",
              boxSizing: "border-box",
              cursor: disabled ? "not-allowed" : "text",
              opacity: disabled ? 0.6 : 1,
              ...style,
            }}
            {...props}
          />

          {rightAddon && (
            <div
              style={{
                position: "absolute",
                right: "12px",
                display: "flex",
                alignItems: "center",
                color: "var(--text-tertiary)",
              }}
            >
              {rightAddon}
            </div>
          )}
        </div>

        {error && (
          <div
            id={errorId}
            role="alert"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              fontSize: "0.75rem",
              color: "var(--danger-600)",
              fontWeight: 500,
            }}
          >
            <AlertCircle size={14} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!error && helperText && (
          <div
            id={helperId}
            style={{
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              lineHeight: 1.4,
            }}
          >
            {helperText}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

