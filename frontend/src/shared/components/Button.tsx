import React from "react";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  pill?: boolean;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = "primary",
      size = "md",
      pill = true,
      isLoading = false,
      disabled = false,
      leftIcon,
      rightIcon,
      className = "",
      style,
      ...props
    },
    ref
  ) => {
    // Determine sizing
    const sizeStyles = {
      sm: { height: "32px", padding: "0 12px", fontSize: "0.8125rem", gap: "6px" },
      md: { height: "40px", padding: "0 18px", fontSize: "0.875rem", gap: "8px" },
      lg: { height: "46px", padding: "0 24px", fontSize: "0.9375rem", gap: "10px" },
    }[size];

    // Determine variant colors based on design tokens
    const getVariantStyles = () => {
      switch (variant) {
        case "primary":
          return {
            backgroundColor: "var(--brand-500)",
            color: "var(--text-on-dark)",
            border: "1px solid transparent",
          };
        case "secondary":
          return {
            backgroundColor: "var(--surface-card)",
            color: "var(--brand-600)",
            border: "1px solid var(--line-medium)",
          };
        case "ghost":
          return {
            backgroundColor: "transparent",
            color: "var(--text-primary)",
            border: "1px solid transparent",
          };
        case "danger":
          return {
            backgroundColor: "var(--danger-600)",
            color: "var(--text-on-dark)",
            border: "1px solid transparent",
          };
      }
    };

    const variantStyle = getVariantStyles();
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`lekhan-button variant-${variant} ${className}`}
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 600,
          fontFamily: "var(--font-ui)",
          letterSpacing: 0,
          borderRadius: pill ? "var(--radius-pill)" : "var(--radius-input)",
          cursor: isDisabled ? "not-allowed" : "pointer",
          opacity: isDisabled ? 0.5 : 1,
          transition: "background-color var(--transition-fast), border-color var(--transition-fast), transform var(--transition-press)",
          userSelect: "none",
          whiteSpace: "nowrap",
          position: "relative",
          ...sizeStyles,
          ...variantStyle,
          ...style,
        }}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
        {!isLoading && leftIcon && <span className="shrink-0">{leftIcon}</span>}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";

