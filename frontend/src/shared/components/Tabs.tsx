import React from "react";

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
}

export interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
  size?: "sm" | "md";
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  activeId,
  onChange,
  className = "",
  size = "md",
}) => {
  return (
    <div
      role="tablist"
      className={`lekhan-tabs ${className}`}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "4px",
        padding: "4px",
        backgroundColor: "var(--surface-sunken)",
        borderRadius: "var(--radius-pill)",
        width: "fit-content",
      }}
    >
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            type="button"
            onClick={() => onChange(tab.id)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: size === "sm" ? "4px 12px" : "6px 16px",
              fontSize: size === "sm" ? "0.8125rem" : "0.875rem",
              fontWeight: isActive ? 600 : 500,
              color: isActive ? "var(--text-on-dark)" : "var(--text-secondary)",
              backgroundColor: isActive ? "var(--brand-500)" : "transparent",
              borderRadius: "var(--radius-pill)",
              border: "none",
              cursor: "pointer",
              transition: "all var(--transition-fast)",
              userSelect: "none",
              whiteSpace: "nowrap",
            }}
          >
            {tab.icon && <span className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                style={{
                  fontSize: "0.6875rem",
                  padding: "1px 6px",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: isActive ? "rgba(255,255,255,0.25)" : "var(--line-medium)",
                  color: isActive ? "#fff" : "var(--text-primary)",
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

