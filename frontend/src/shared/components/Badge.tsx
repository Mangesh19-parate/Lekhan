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
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "neutral",
  label,
  sublabel,
  icon,
  size = "md",
  className = "",
}) => {
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs gap-1" : "px-2.5 py-1 text-xs gap-1.5";

  const config = {
    approved: {
      classes: "bg-approved-100 text-brand-900 border border-approved-border dark:bg-approved-100/20 dark:text-approved-400 dark:border-approved-400/40",
      defaultIcon: <Award size={13} className="text-approved-500" />,
    },
    under_review: {
      classes: "bg-warning-tint text-warning-600 border border-warning-border dark:bg-warning-500/10 dark:text-warning-500 dark:border-warning-500/30",
      defaultIcon: <Clock size={13} />,
    },
    draft: {
      classes: "bg-subtle text-text-secondary border border-line-medium dark:bg-sunken dark:text-text-muted dark:border-line-subtle",
      defaultIcon: <FileText size={13} />,
    },
    active: {
      classes: "bg-brand-100 text-brand-600 border border-brand-500 dark:bg-brand-900/50 dark:text-brand-400 dark:border-brand-500/40",
      defaultIcon: <CheckCircle2 size={13} />,
    },
    danger: {
      classes: "bg-danger-tint text-danger-600 border border-danger-border dark:bg-danger-500/10 dark:text-danger-500 dark:border-danger-500/30",
      defaultIcon: <XCircle size={13} />,
    },
    neutral: {
      classes: "bg-sunken text-text-secondary border border-line-subtle dark:bg-sunken/80 dark:text-text-tertiary",
      defaultIcon: <AlertTriangle size={13} />,
    },
  }[variant];

  return (
    <span
      className={`inline-flex items-center font-medium font-ui rounded-pill tracking-normal whitespace-nowrap select-none transition-colors ${sizeClasses} ${config.classes} ${className}`}
    >
      <span className="shrink-0 flex items-center">{icon || config.defaultIcon}</span>
      <span>{label}</span>
      {sublabel && <span className="opacity-70 font-normal ml-0.5">({sublabel})</span>}
    </span>
  );
};
