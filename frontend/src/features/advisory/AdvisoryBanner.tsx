import React, { useState, useEffect, useRef } from "react";
import { Badge } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { AlertTriangle, Info, ShieldAlert, ChevronDown, ChevronUp, Scale } from "lucide-react";

export interface AdvisoryAlertItem {
  id: string;
  rule_name: string;
  severity: "advisory" | "warning";
  title_en: string;
  title_mr: string;
  advice_en: string;
  advice_mr: string;
  statutory_ref: string;
  action_needed?: string;
}

interface Props {
  templateId?: string;
  formData: Record<string, any>;
  repeatersData?: Record<string, any[]>;
}

export const AdvisoryBanner: React.FC<Props> = ({
  templateId = "sale_deed_plot_mr",
  formData,
  repeatersData,
}) => {
  const { lang, t } = useI18n();
  const [alerts, setAlerts] = useState<AdvisoryAlertItem[]>([]);
  const [isExpanded, setIsExpanded] = useState(true);
  const debounceRef = useRef<number | null>(null);

  useEffect(() => {
    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }

    debounceRef.current = window.setTimeout(async () => {
      try {
        const payloadData = {
          ...formData,
          financial: {
            total_consideration: formData["financial.total_consideration"],
            earnest_advance: formData["financial.earnest_advance"],
          },
          sellers: repeatersData?.sellers || [],
          purchasers: repeatersData?.purchasers || [],
          property: {
            mouza: formData["property.mouza"],
            khasra_no: formData["property.khasra_no"],
            plot_no: formData["property.plot_no"],
            area_sqm: formData["property.area_sqm"],
          },
        };

        const res = await fetch("/api/v1/advisory/evaluate", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            template_id: templateId,
            data: payloadData,
          }),
        });

        if (res.ok) {
          const list: AdvisoryAlertItem[] = await res.json();
          setAlerts(list);
        }
      } catch (err) {
        // Advisory evaluation is strictly non-blocking; do not throw
        console.warn("Advisory evaluation skipped:", err);
      }
    }, 400);

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [templateId, formData, repeatersData]);

  if (alerts.length === 0) {
    return null;
  }

  const hasWarning = alerts.some((a) => a.severity === "warning");

  return (
    <div
      style={{
        borderRadius: "var(--radius-card)",
        border: `1px solid ${hasWarning ? "var(--color-warning-border)" : "var(--brand-200)"}`,
        backgroundColor: hasWarning ? "var(--color-warning-bg)" : "var(--brand-50)",
        padding: "12px 16px",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        transition: "all 0.2s ease",
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "var(--radius-pill)",
              backgroundColor: hasWarning ? "var(--color-warning-fg)" : "var(--brand-600)",
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {hasWarning ? <AlertTriangle size={15} /> : <Scale size={15} />}
          </div>
          <div>
            <span
              style={{
                fontSize: "0.875rem",
                fontWeight: 700,
                color: hasWarning ? "var(--color-warning-fg)" : "var(--brand-900)",
              }}
            >
              {lang === "mr"
                ? `कायदेशीर सल्ला व दक्षता सूचना (${alerts.length})`
                : `Statutory Legal Advisories (${alerts.length})`}
            </span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginLeft: "8px" }}>
              {lang === "mr" ? "बिगर-अडथळा सूचना (Non-blocking)" : "Non-blocking Advocate Checklist"}
            </span>
          </div>
        </div>

        <button
          type="button"
          style={{
            background: "none",
            border: "none",
            color: "var(--text-secondary)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
          }}
          aria-label={isExpanded ? "Collapse" : "Expand"}
        >
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Expanded Alert List */}
      {isExpanded && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "4px" }}>
          {alerts.map((alert) => {
            const isWarn = alert.severity === "warning";
            const title = lang === "mr" ? alert.title_mr : alert.title_en;
            const advice = lang === "mr" ? alert.advice_mr : alert.advice_en;

            return (
              <div
                key={alert.id}
                style={{
                  padding: "10px 14px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: "var(--surface-card)",
                  border: "1px solid var(--line-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontWeight: 700, fontSize: "0.8125rem", color: isWarn ? "var(--color-warning-fg)" : "var(--brand-800)" }}>
                      {title}
                    </span>
                  </div>
                  <Badge
                    variant={isWarn ? "under_review" : "neutral"}
                    size="sm"
                    label={alert.statutory_ref}
                  />
                </div>

                <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {advice}
                </p>

                {alert.action_needed && (
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-tertiary)", fontWeight: 500, borderTop: "1px dashed var(--line-subtle)", paddingTop: "4px", marginTop: "2px" }}>
                    <strong>{lang === "mr" ? "कृती आवश्यक:" : "Action:"}</strong> {alert.action_needed}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
