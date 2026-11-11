import React from "react";
import { CheckCircle2, Clock, AlertTriangle, FileText, Award, XCircle } from "lucide-react";

export type BadgeVariant = "approved" | "under_review" | "draft" | "active" | "danger" | "neutral";

export interface BadgeProps {
  variant?: BadgeVariant;
  label: string;
  sublabel?: string;
  icon?: React.ReactNode;
  size?: "sm" | "md";
  className?: string;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "neutral",
  label,
  sublabel,
  icon,
  size = "md",
  className = "",
  style,
}) => {
  const getVariantStyles = (): { bg: string; color: string; border: string; defaultIcon: React.ReactNode } => {
    switch (variant) {
      case "approved":
        // Strict DESIGN.md rule: Gold reserved ONLY for Approved by <role>
        return {
          bg: "var(--approved-100)",
          color: "var(--brand-900)",
          border: "1px solid var(--approved-border)",
          defaultIcon: <Award size={14} color="var(--approved-500)" />,
        };
      case "under_review":
        return {
          bg: "var(--warning-tint)",
          color: "var(--warning-600)",
          border: "1px solid var(--warning-border)",
          defaultIcon: <Clock size={14} />,
        };
      case "draft":
        return {
          bg: "var(--surface-subtle)",
          color: "var(--text-secondary)",
          border: "1px solid var(--line-medium)",
          defaultIcon: <FileText size={14} />,
        };
      case "active":
        return {
          bg: "var(--brand-100)",
          color: "var(--brand-600)",
          border: "1px solid var(--brand-500)",
          defaultIcon: <CheckCircle2 size={14} />,
        };
      case "danger":
        return {
          bg: "var(--danger-tint)",
          color: "var(--danger-600)",
          border: "1px solid var(--danger-border)",
          defaultIcon: <XCircle size={14} />,
        };
      case "neutral":
      default:
        return {
          bg: "var(--surface-sunken)",
          color: "var(--text-secondary)",
          border: "1px solid var(--line-subtle)",
          defaultIcon: <AlertTriangle size={14} />,
        };
    }
  };

  const { bg, color, border, defaultIcon } = getVariantStyles();
  const isSm = size === "sm";

  return (
    <span
      className={`lekhan-badge ${className}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: isSm ? "4px" : "6px",
        padding: isSm ? "2px 8px" : "4px 10px",
        borderRadius: "var(--radius-pill)",
        backgroundColor: bg,
        color: color,
        border: border,
        fontSize: isSm ? "0.6875rem" : "0.75rem",
        fontWeight: 600,
        fontFamily: "var(--font-ui)",
        letterSpacing: 0,
        userSelect: "none",
        whiteSpace: "nowrap",
        lineHeight: 1.2,
        ...style,
      }}
    >
      <span className="shrink-0 flex items-center">{icon || defaultIcon}</span>
      <span>{label}</span>
      {sublabel && (
        <span style={{ opacity: 0.75, fontWeight: 500, fontSize: "0.9em" }}>
          ({sublabel})
        </span>
      )}
    </span>
  );
};

