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
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, "-")}` : undefined);
    const helperId = helperText ? `${inputId}-helper` : undefined;
    const errorId = error ? `${inputId}-error` : undefined;

    return (
      <div className={`flex flex-col gap-1.5 w-full ${className}`}>
        {label && (
          <div className="flex items-center justify-between">
            <label
              htmlFor={inputId}
              className="text-xs font-semibold text-text-primary select-none inline-flex items-center gap-1 font-ui"
            >
              <span>{label}</span>
              {required && (
                <span className="text-[11px] font-bold text-danger uppercase">
                  {requiredMarker ? `(${requiredMarker})` : "*"}
                </span>
              )}
            </label>
          </div>
        )}

        <div className="relative flex items-center w-full">
          {leftAddon && (
            <div className="absolute left-3 flex items-center pointer-events-none text-text-secondary z-10">
              {leftAddon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-describedby={[helperId, errorId].filter(Boolean).join(" ") || undefined}
            aria-invalid={!!error}
            className={`w-full h-10 rounded-input border text-sm font-ui transition-all duration-150 focus:outline-none focus:ring-2 disabled:bg-sunken disabled:cursor-not-allowed disabled:opacity-60 bg-subtle dark:bg-sunken/40 text-text-primary placeholder:text-text-tertiary ${
              leftAddon ? "pl-9" : "pl-3"
            } ${rightAddon ? "pr-9" : "pr-3"} ${
              error
                ? "border-danger bg-danger-tint/30 text-danger-600 focus:ring-danger-500 focus:border-danger"
                : "border-line-subtle hover:border-line-medium focus:border-brand-500 focus:ring-brand-500/25"
            }`}
            {...props}
          />

          {rightAddon && (
            <div className="absolute right-3 flex items-center text-text-secondary z-10">
              {rightAddon}
            </div>
          )}
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

Input.displayName = "Input";
