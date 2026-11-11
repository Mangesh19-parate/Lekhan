import React from "react";

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = "100%",
  height = "20px",
  borderRadius = "var(--radius-input)",
  className = "",
  style,
}) => {
  return (
    <div
      className={`lekhan-skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: "var(--surface-sunken)",
        position: "relative",
        overflow: "hidden",
        ...style,
      }}
    />
  );
};

export const FormSkeleton: React.FC = () => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      <Skeleton height="36px" width="40%" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <Skeleton height="14px" width="30%" />
          <Skeleton height="40px" />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <Skeleton height="14px" width="30%" />
          <Skeleton height="40px" />
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <Skeleton height="14px" width="25%" />
        <Skeleton height="80px" />
      </div>
    </div>
  );
};

