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
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: "h-8 px-3 text-xs gap-1.5",
      md: "h-10 px-4 text-sm gap-2",
      lg: "h-11 px-6 text-base gap-2.5",
    }[size];

    const variantClasses = {
      primary: "bg-brand-500 text-white hover:bg-brand-600 border border-transparent shadow-sm focus:ring-brand-500",
      secondary: "bg-card text-brand-600 hover:bg-brand-50 border border-brand-500/30 focus:ring-brand-500 dark:bg-card dark:text-brand-400 dark:border-brand-500/40 dark:hover:bg-brand-900/40",
      ghost: "bg-transparent text-text-primary hover:bg-sunken border border-transparent focus:ring-brand-500",
      danger: "bg-danger-600 text-white hover:bg-danger-500 border border-transparent shadow-sm focus:ring-danger-500",
    }[variant];

    const radiusClass = pill ? "rounded-pill" : "rounded-input";
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`inline-flex items-center justify-center font-semibold font-ui select-none whitespace-nowrap transition-all duration-150 active:scale-95 disabled:pointer-events-none disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-sunken ${sizeClasses} ${variantClasses} ${radiusClass} ${className}`}
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
