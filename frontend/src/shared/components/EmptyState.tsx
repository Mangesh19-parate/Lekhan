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
      className={`flex flex-col items-center justify-center text-center p-8 md:p-12 rounded-card bg-subtle dark:bg-sunken/40 border border-dashed border-line-medium ${className}`}
    >
      <div className="w-12 h-12 rounded-pill bg-sunken dark:bg-card flex items-center justify-center text-brand-600 dark:text-brand-400 mb-4 shadow-sm">
        {icon || <FolderOpen size={24} />}
      </div>
      <h3 className="text-base font-semibold text-text-primary mb-1 font-ui">
        {title}
      </h3>
      <p className="text-sm text-text-secondary max-w-sm mb-5 font-ui">
        {description}
      </p>
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
};
