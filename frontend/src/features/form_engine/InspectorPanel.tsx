import React from "react";
import { useI18n } from "../../shared/i18n";
import { Card, Badge, Button } from "../../shared/components";
import { Calculator, CheckCircle2, AlertTriangle, FileText, Download, ShieldCheck } from "lucide-react";

interface InspectorProps {
  formData: Record<string, any>;
  repeatersData: Record<string, any[]>;
  derivedValues: Record<string, any>;
  requiredFieldsCount: { filled: number; total: number };
  onExport: () => void;
  isSubmitting?: boolean;
}

export const InspectorPanel: React.FC<InspectorProps> = ({
  formData,
  repeatersData,
  derivedValues,
  requiredFieldsCount,
  onExport,
  isSubmitting = false,
}) => {
  const { lang, t } = useI18n();

  const total = parseFloat(formData["financial.total_consideration"] || 0);
  const advance = parseFloat(formData["financial.earnest_advance"] || 0);
  const balance = derivedValues["financial.balance_amount"] || 0;
  const areaSqm = formData["property.area_sqm"] || 0;
  const areaSqft = derivedValues["property.area_sqft"] || 0;

  const sellersCount = repeatersData["sellers"]?.length ?? 1;
  const purchasersCount = repeatersData["purchasers"]?.length ?? 1;
  const witnessesCount = repeatersData["witnesses"]?.length ?? 2;

  const percentComplete = Math.round(
    requiredFieldsCount.total > 0
      ? (requiredFieldsCount.filled / requiredFieldsCount.total) * 100
      : 100
  );
  const isReady = requiredFieldsCount.filled >= requiredFieldsCount.total;

  return (
    <aside
      aria-label={t("inspector.title")}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        width: "100%",
        fontFamily: "var(--font-ui)",
      }}
    >
      {/* Header card */}
      <Card
        padding="md"
        style={{
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--line-medium)",
          borderRadius: "var(--radius-card)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Calculator size={18} color="var(--brand-600)" />
            <h3 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 700, color: "var(--brand-900)" }}>
              {t("inspector.title")}
            </h3>
          </div>
          <Badge
            variant={isReady ? "active" : "neutral"}
            size="sm"
            label={`${percentComplete}%`}
            icon={isReady ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
          />
        </div>

        {/* Progress bar */}
        <div
          role="progressbar"
          aria-valuenow={percentComplete}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={t("form.fill_progress")}
          style={{
            width: "100%",
            height: "6px",
            backgroundColor: "var(--surface-sunken)",
            borderRadius: "var(--radius-pill)",
            overflow: "hidden",
            margin: "8px 0 4px 0",
          }}
        >
          <div
            style={{
              width: `${percentComplete}%`,
              height: "100%",
              backgroundColor: isReady ? "var(--brand-500)" : "var(--warning-500)",
              borderRadius: "var(--radius-pill)",
              transition: "width 300ms ease-out",
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <span>{t("form.fill_progress")}</span>
          <span style={{ fontWeight: 600 }}>
            {requiredFieldsCount.filled} / {requiredFieldsCount.total}
          </span>
        </div>
      </Card>

      {/* Financial Metrics */}
      <Card
        padding="md"
        style={{
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--line-medium)",
          borderRadius: "var(--radius-card)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        <div
          style={{
            fontSize: "0.8125rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "var(--text-secondary)",
            paddingBottom: "6px",
            borderBottom: "1px solid var(--line-subtle)",
          }}
        >
          {t("inspector.financial_summary")}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {t("inspector.total_consideration")}
          </span>
          <span style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
            ₹ {total > 0 ? total.toLocaleString("en-IN") : "0"}
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {t("inspector.advance_paid")}
          </span>
          <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--brand-600)", fontFamily: "var(--font-mono)" }}>
            ₹ {advance > 0 ? advance.toLocaleString("en-IN") : "0"}
          </span>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: "8px",
            borderTop: "1px dashed var(--line-subtle)",
          }}
        >
          <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {t("inspector.balance_payable")}
          </span>
          <span
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              color: balance > 0 ? "var(--brand-600)" : "var(--text-primary)",
              fontFamily: "var(--font-mono)",
            }}
          >
            ₹ {balance.toLocaleString("en-IN")}
          </span>
        </div>
      </Card>

      {/* Property Metrics */}
      <Card
        padding="md"
        style={{
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--line-medium)",
          borderRadius: "var(--radius-card)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        <div
          style={{
            fontSize: "0.8125rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "var(--text-secondary)",
            paddingBottom: "6px",
            borderBottom: "1px solid var(--line-subtle)",
          }}
        >
          {t("inspector.property_summary")}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {lang === "mr" ? "क्षेत्रफळ (चौ. मी.)" : "Area (Sq. M.)"}
          </span>
          <span style={{ fontSize: "0.875rem", fontWeight: 600, fontFamily: "var(--font-mono)" }}>
            {areaSqm || "0"} sq.m.
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {t("inspector.equivalent_area")}
          </span>
          <span style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--brand-600)", fontFamily: "var(--font-mono)" }}>
            {areaSqft} sq.ft.
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "8px", borderTop: "1px dashed var(--line-subtle)" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {lang === "mr" ? "भूखंड व मौजा" : "Plot & Mouza"}
          </span>
          <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {formData["property.plot_no"] || "—"} / {formData["property.mouza"] || "—"}
          </span>
        </div>
      </Card>

      {/* Parties & Witnesses Count */}
      <Card
        padding="md"
        style={{
          backgroundColor: "var(--surface-subtle)",
          border: "1px solid var(--line-subtle)",
          borderRadius: "var(--radius-card)",
          display: "flex",
          justifyContent: "space-around",
          textAlign: "center",
        }}
      >
        <div>
          <div style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--brand-900)" }}>
            {sellersCount}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>
            {t("inspector.sellers")}
          </div>
        </div>
        <div style={{ width: "1px", backgroundColor: "var(--line-medium)" }} />
        <div>
          <div style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--brand-900)" }}>
            {purchasersCount}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>
            {t("inspector.purchasers")}
          </div>
        </div>
        <div style={{ width: "1px", backgroundColor: "var(--line-medium)" }} />
        <div>
          <div style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--brand-900)" }}>
            {witnessesCount}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>
            {t("inspector.witnesses")}
          </div>
        </div>
      </Card>

      {/* Direct Action */}
      <Button
        variant="primary"
        size="lg"
        pill
        isLoading={isSubmitting}
        onClick={onExport}
        leftIcon={<Download size={18} />}
        style={{ width: "100%", marginTop: "4px" }}
      >
        {t("actions.generate")}
      </Button>

      {/* Legal disclaimer strip */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "8px",
          padding: "10px",
          borderRadius: "var(--radius-input)",
          backgroundColor: "var(--surface-sunken)",
          fontSize: "0.6875rem",
          color: "var(--text-secondary)",
          lineHeight: 1.4,
        }}
      >
        <ShieldCheck size={14} className="shrink-0 mt-0.5 text-[var(--brand-600)]" />
        <span>{t("disclaimer")}</span>
      </div>
    </aside>
  );
};

