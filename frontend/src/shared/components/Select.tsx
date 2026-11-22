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
  (
    {
      id,
      label,
      options,
      helperText,
      error,
      required,
      requiredMarker,
      className = "",
      disabled,
      ...props
    },
    ref
  ) => {
    const selectId = id || (label ? `select-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);
    const helperId = helperText ? `${selectId}-helper` : undefined;
    const errorId = error ? `${selectId}-error` : undefined;

    return (
      <div className={`flex flex-col gap-1.5 w-full ${className}`}>
        {label && (
          <label
            htmlFor={selectId}
            className="text-xs font-semibold text-text-primary select-none inline-flex items-center gap-1 font-ui"
          >
            <span>{label}</span>
            {required && (
              <span className="text-[11px] font-bold text-danger uppercase">
                {requiredMarker ? `(${requiredMarker})` : "*"}
              </span>
            )}
          </label>
        )}

        <div className="relative flex items-center w-full">
          <select
            ref={ref}
            id={selectId}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={[errorId, helperId].filter(Boolean).join(" ") || undefined}
            required={required}
            className={`w-full h-10 pl-3 pr-9 rounded-input border text-sm font-ui appearance-none transition-all duration-150 focus:outline-none focus:ring-2 disabled:bg-sunken disabled:cursor-not-allowed disabled:opacity-60 bg-subtle dark:bg-sunken/40 text-text-primary ${
              error
                ? "border-danger text-danger-600 focus:ring-danger-500 focus:border-danger"
                : "border-line-subtle hover:border-line-medium focus:border-brand-500 focus:ring-brand-500/25"
            }`}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          <div className="absolute right-3 flex items-center pointer-events-none text-text-secondary">
            <ChevronDown size={16} />
          </div>
        </div>

        {error && (
          <div
            id={errorId}
            role="alert"
            className="flex items-center gap-1.5 text-xs font-medium text-danger mt-0.5"
          >
            <AlertCircle size={13} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!error && helperText && (
          <p id={helperId} className="text-xs text-text-secondary font-ui mt-0.5">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = "Select";
