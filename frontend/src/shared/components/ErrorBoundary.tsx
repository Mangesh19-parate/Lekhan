import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log component stack trace for diagnostic purposes
    console.error("Lekhan UI Uncaught Error:", error, errorInfo);
  }

  private handleReset = () => {
    try {
      localStorage.removeItem("lekhan_current_view");
    } catch {
      // Ignore
    }
    window.location.href = "/";
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "var(--surface-canvas, #F2F0EB)",
            fontFamily: "'Inter', 'Noto Sans Devanagari', -apple-system, sans-serif",
            padding: "24px",
          }}
        >
          <div
            style={{
              maxWidth: "520px",
              width: "100%",
              backgroundColor: "var(--surface-card, #FFFFFF)",
              borderRadius: "12px",
              border: "1px solid var(--line-subtle, #E5E7EB)",
              padding: "36px",
              boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)",
              textAlign: "center",
            }}
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                backgroundColor: "#FEE2E2",
                color: "#DC2626",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 20px auto",
              }}
            >
              <AlertTriangle size={28} />
            </div>

            <h1
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--brand-900, #0E2F1F)",
                margin: "0 0 8px 0",
              }}
            >
              {this.props.fallbackTitle || "प्रणाली त्रुटी — दृश्य लोड होऊ शकले नाही"}
            </h1>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-secondary, #4B5563)",
                lineHeight: 1.5,
                margin: "0 0 20px 0",
              }}
            >
              {this.props.fallbackMessage ||
                "A client rendering issue occurred. Your draft data in progress has been safely preserved."}
            </p>

            {this.state.error?.message && (
              <div
                style={{
                  backgroundColor: "var(--surface-sunken, #F9FAFB)",
                  border: "1px solid var(--line-subtle, #E5E7EB)",
                  borderRadius: "6px",
                  padding: "10px 14px",
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono, monospace)",
                  color: "#6B7280",
                  textAlign: "left",
                  marginBottom: "24px",
                  wordBreak: "break-all",
                  maxHeight: "80px",
                  overflowY: "auto",
                }}
              >
                {this.state.error.message}
              </div>
            )}

            <div
              style={{
                display: "flex",
                gap: "12px",
                justifyContent: "center",
              }}
            >
              <button
                type="button"
                onClick={this.handleReload}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 16px",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderRadius: "6px",
                  backgroundColor: "var(--surface-card, #FFFFFF)",
                  color: "var(--text-primary, #1F2937)",
                  border: "1px solid var(--line-subtle, #D1D5DB)",
                  cursor: "pointer",
                }}
              >
                <RefreshCw size={15} />
                रिफ्रेश (Reload)
              </button>

              <button
                type="button"
                onClick={this.handleReset}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 16px",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderRadius: "6px",
                  backgroundColor: "var(--brand-600, #005C3B)",
                  color: "#FFFFFF",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                <Home size={15} />
                मुख्यपृष्ठावर जा (Overview)
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
