import React from "react";

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = "100%",
  height = "20px",
  borderRadius,
  className = "",
}) => {
  return (
    <div
      style={{
        width,
        height,
        borderRadius: borderRadius || "var(--radius-input)",
      }}
      className={`relative overflow-hidden bg-sunken dark:bg-card/60 animate-pulse ${className}`}
    />
  );
};

export const FormSkeleton: React.FC = () => {
  return (
    <div className="flex flex-col gap-6 w-full">
      <Skeleton height="36px" width="40%" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <Skeleton height="14px" width="30%" />
          <Skeleton height="40px" />
        </div>
        <div className="flex flex-col gap-2">
          <Skeleton height="14px" width="30%" />
          <Skeleton height="40px" />
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <Skeleton height="14px" width="25%" />
        <Skeleton height="80px" />
      </div>
      <div className="flex justify-end gap-3 pt-4">
        <Skeleton height="40px" width="100px" borderRadius="var(--radius-pill)" />
        <Skeleton height="40px" width="120px" borderRadius="var(--radius-pill)" />
      </div>
    </div>
  );
};
