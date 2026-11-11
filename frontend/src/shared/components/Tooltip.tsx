import React, { useState } from "react";

export interface TooltipProps {
  content: string;
  children: React.ReactElement;
  position?: "top" | "bottom" | "left" | "right";
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children, position = "top" }) => {
  const [visible, setVisible] = useState(false);

  const getPositionStyles = () => {
    switch (position) {
      case "bottom":
        return {
          top: "100%",
          left: "50%",
          transform: "translateX(-50%)",
          marginTop: "6px",
        };
      case "left":
        return {
          right: "100%",
          top: "50%",
          transform: "translateY(-50%)",
          marginRight: "6px",
        };
      case "right":
        return {
          left: "100%",
          top: "50%",
          transform: "translateY(-50%)",
          marginLeft: "6px",
        };
      case "top":
      default:
        return {
          bottom: "100%",
          left: "50%",
          transform: "translateX(-50%)",
          marginBottom: "6px",
        };
    }
  };

  return (
    <div
      style={{ position: "relative", display: "inline-flex" }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          style={{
            position: "absolute",
            zIndex: 1000,
            backgroundColor: "var(--brand-900)",
            color: "var(--text-on-dark)",
            padding: "4px 8px",
            fontSize: "0.75rem",
            fontWeight: 500,
            borderRadius: "var(--radius-input)",
            whiteSpace: "nowrap",
            boxShadow: "var(--shadow-card)",
            pointerEvents: "none",
            animation: "fadeIn 120ms ease-out",
            ...getPositionStyles(),
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
};

