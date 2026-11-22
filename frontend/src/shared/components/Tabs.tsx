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
      className={`inline-flex items-center gap-1 p-1 bg-sunken rounded-pill font-ui select-none ${className}`}
    >
      {items.map((tab) => {
        const isActive = tab.id === activeId;
        const sizeClasses = size === "sm" ? "px-3 py-1 text-xs gap-1.5" : "px-4 py-1.5 text-sm gap-2";
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`inline-flex items-center rounded-pill font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-brand-500/30 ${sizeClasses} ${
              isActive
                ? "bg-brand-500 text-white shadow-sm"
                : "text-text-secondary hover:text-text-primary hover:bg-card/50"
            }`}
          >
            {tab.icon && <span className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge != null && (
              <span
                className={`ml-1 text-[11px] px-1.5 py-0.2 rounded-pill font-bold ${
                  isActive ? "bg-white/20 text-white" : "bg-card text-text-secondary"
                }`}
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
