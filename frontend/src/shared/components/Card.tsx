import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "sunken" | "subtle" | "highlight";
  padding?: "none" | "sm" | "md" | "lg";
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, variant = "default", padding = "md", className = "", ...props }, ref) => {
    const paddingClasses = {
      none: "p-0",
      sm: "p-3",
      md: "p-5",
      lg: "p-7",
    }[padding];

    const variantClasses = {
      default: "bg-card border border-line-subtle shadow-card text-text-primary",
      sunken: "bg-sunken border border-line-subtle text-text-primary",
      subtle: "bg-subtle border border-line-subtle text-text-primary",
      highlight: "bg-card border-2 border-brand-500 shadow-elevated text-text-primary",
    }[variant];

    return (
      <div
        ref={ref}
        className={`rounded-card transition-colors duration-150 ${paddingClasses} ${variantClasses} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";
