import React from "react";
import { ChevronDown, AlertCircle } from "lucide-react";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  helperText?: string;
  error?: string;
  requiredMarker?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ id, label, options, helperText, error, required, requiredMarker, className = "", style, disabled, ...props }, ref) => {
    const selectId = id || (label ? `select-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);
    const helperId = helperText ? `${selectId}-helper` : undefined;
    const errorId = error ? `${selectId}-error` : undefined;

    return (
      <div className={`lekhan-select-group ${className}`} style={{ display: "flex", flexDirection: "column", gap: "6px", width: "100%" }}>
        {label && (
          <label
            htmlFor={selectId}
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
              <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--danger-600)" }}>
                {requiredMarker ? `(${requiredMarker})` : "*"}
              </span>
            )}
          </label>
        )}

        <div style={{ position: "relative", display: "flex", alignItems: "center", width: "100%" }}>
          <select
            ref={ref}
            id={selectId}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={[errorId, helperId].filter(Boolean).join(" ") || undefined}
            required={required}
            className={`lekhan-select-field ${error ? "has-error" : ""}`}
            style={{
              width: "100%",
              height: "40px",
              padding: "0 36px 0 12px",
              fontSize: "0.875rem",
              fontFamily: "var(--font-ui)",
              color: "var(--text-primary)",
              backgroundColor: disabled ? "var(--surface-sunken)" : "var(--surface-card)",
              border: `1px solid ${error ? "var(--danger-600)" : "var(--line-medium)"}`,
              borderRadius: "var(--radius-input)",
              appearance: "none",
              cursor: disabled ? "not-allowed" : "pointer",
              transition: "border-color var(--transition-fast), box-shadow var(--transition-fast)",
              boxSizing: "border-box",
              opacity: disabled ? 0.6 : 1,
              ...style,
            }}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <ChevronDown
            size={16}
            style={{
              position: "absolute",
              right: "12px",
              pointerEvents: "none",
              color: "var(--text-secondary)",
            }}
          />
        </div>

        {error && (
          <div id={errorId} role="alert" style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.75rem", color: "var(--danger-600)", fontWeight: 500 }}>
            <AlertCircle size={14} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!error && helperText && (
          <div id={helperId} style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
            {helperText}
          </div>
        )}
      </div>
    );
  }
);

Select.displayName = "Select";

