import React from "react";
import { FolderOpen } from "lucide-react";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = "",
}) => {
  return (
    <div
      className={`lekhan-empty-state ${className}`}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "48px 24px",
        borderRadius: "var(--radius-card)",
        backgroundColor: "var(--surface-subtle)",
        border: "1px dashed var(--line-medium)",
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "var(--radius-pill)",
          backgroundColor: "var(--surface-sunken)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--brand-600)",
          marginBottom: "16px",
        }}
      >
        {icon || <FolderOpen size={24} />}
      </div>
      <h3
        style={{
          margin: 0,
          fontSize: "1rem",
          fontWeight: 600,
          color: "var(--text-primary)",
          fontFamily: "var(--font-ui)",
        }}
      >
        {title}
      </h3>
      <p
        style={{
          margin: "6px 0 20px 0",
          fontSize: "0.8125rem",
          color: "var(--text-secondary)",
          maxWidth: "360px",
          lineHeight: 1.5,
        }}
      >
        {description}
      </p>
      {action}
    </div>
  );
};

