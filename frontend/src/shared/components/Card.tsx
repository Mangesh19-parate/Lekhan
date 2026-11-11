import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "sunken" | "subtle" | "highlight";
  padding?: "none" | "sm" | "md" | "lg";
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, variant = "default", padding = "md", className = "", style, ...props }, ref) => {
    const paddingStyle = {
      none: "0",
      sm: "12px",
      md: "20px",
      lg: "28px",
    }[padding];

    const getVariantStyles = () => {
      switch (variant) {
        case "sunken":
          return {
            backgroundColor: "var(--surface-sunken)",
            border: "1px solid var(--line-subtle)",
            boxShadow: "none",
          };
        case "subtle":
          return {
            backgroundColor: "var(--surface-subtle)",
            border: "1px solid var(--line-subtle)",
            boxShadow: "none",
          };
        case "highlight":
          return {
            backgroundColor: "var(--surface-card)",
            border: "1.5px solid var(--brand-500)",
            boxShadow: "var(--shadow-elevated)",
          };
        case "default":
        default:
          return {
            backgroundColor: "var(--surface-card)",
            border: "1px solid var(--line-subtle)",
            boxShadow: "var(--shadow-card)",
          };
      }
    };

    return (
      <div
        ref={ref}
        className={`lekhan-card ${className}`}
        style={{
          borderRadius: "var(--radius-card)",
          padding: paddingStyle,
          transition: "border-color var(--transition-fast), box-shadow var(--transition-fast)",
          ...getVariantStyles(),
          ...style,
        }}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

