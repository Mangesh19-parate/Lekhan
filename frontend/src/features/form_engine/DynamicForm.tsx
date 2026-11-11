import React, { useState, useEffect, useMemo } from "react";
import { TemplateManifest } from "./types";
import { LiveAmountInWords } from "./LiveAmountInWords";
import { RepeaterGroup } from "./RepeaterGroup";
import { useI18n } from "../../shared/i18n";
import { Card, Input, Button, Badge } from "../../shared/components";
import { FileText, CheckCircle2, ChevronRight, Layers, Landmark, MapPin, IndianRupee, Users, Search } from "lucide-react";

interface Props {
  manifest: TemplateManifest;
  onSubmit: (data: any) => Promise<void>;
  isSubmitting?: boolean;
  formData?: Record<string, any>;
  repeatersData?: Record<string, any[]>;
  onFieldChange?: (key: string, value: any) => void;
  onRepeatersChange?: (repKey: string, items: any[]) => void;
  activeSectionId?: string;
  onSelectSection?: (sectionId: string) => void;
  onOpenPropertySearch?: () => void;
  onOpenPartySearch?: (targetRole: string, index?: number) => void;
  advisoryElement?: React.ReactNode;
}

export const DynamicForm: React.FC<Props> = ({
  manifest,
  onSubmit,
  isSubmitting = false,
  formData: externalFormData,
  repeatersData: externalRepeatersData,
  onFieldChange: externalOnFieldChange,
  onRepeatersChange: externalOnRepeatersChange,
  activeSectionId,
  onSelectSection,
  onOpenPropertySearch,
  onOpenPartySearch,
  advisoryElement,
}) => {
  const { lang, t } = useI18n();

  // Internal state if parent does not provide controlled state
  const [internalFormData, setInternalFormData] = useState<Record<string, any>>({});
  const [internalRepeatersData, setInternalRepeatersData] = useState<Record<string, any[]>>({});

  const formData = externalFormData || internalFormData;
  const repeatersData = externalRepeatersData || internalRepeatersData;

  // Initialize defaults if uncontrolled
  useEffect(() => {
    if (!externalFormData) {
      const initial: Record<string, any> = {};
      Object.entries(manifest.fields).forEach(([key, field]) => {
        initial[key] = field.default ?? "";
      });
      setInternalFormData(initial);
    }

    if (!externalRepeatersData) {
      const initRepeaters: Record<string, any[]> = {};
      Object.entries(manifest.repeaters).forEach(([key, rep]) => {
        const initialCount = Math.max(1, rep.min);
        initRepeaters[key] = Array.from({ length: initialCount }, () => ({}));
      });
      setInternalRepeatersData(initRepeaters);
    }
  }, [manifest, externalFormData, externalRepeatersData]);

  const handleFieldChange = (key: string, value: any) => {
    if (externalOnFieldChange) {
      externalOnFieldChange(key, value);
    } else {
      setInternalFormData((prev) => ({ ...prev, [key]: value }));
    }
  };

  const handleRepeatersChange = (key: string, items: any[]) => {
    if (externalOnRepeatersChange) {
      externalOnRepeatersChange(key, items);
    } else {
      setInternalRepeatersData((prev) => ({ ...prev, [key]: items }));
    }
  };

  // Derived calculations live
  const derivedValues = useMemo(() => {
    const total = parseFloat(formData["financial.total_consideration"] || 0);
    const advance = parseFloat(formData["financial.earnest_advance"] || 0);
    const balance = Math.max(0, total - advance);

    const areaSqm = parseFloat(formData["property.area_sqm"] || 0);
    const areaSqft = (areaSqm * 10.7639104).toFixed(2);

    return {
      "financial.balance_amount": balance,
      "property.area_sqft": areaSqft,
    };
  }, [formData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      ...formData,
      ...derivedValues,
      ...repeatersData,
    };
    onSubmit(payload);
  };

  const getSectionIcon = (id: string) => {
    switch (id) {
      case "property_details":
        return <Landmark size={18} color="var(--brand-600)" />;
      case "boundaries":
        return <MapPin size={18} color="var(--brand-600)" />;
      case "financial_details":
        return <IndianRupee size={18} color="var(--brand-600)" />;
      default:
        return <Layers size={18} color="var(--brand-600)" />;
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Official Guidelines Callout */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "12px",
          padding: "14px 16px",
          backgroundColor: "var(--surface-sunken)",
          borderLeft: "4px solid var(--brand-500)",
          borderRadius: "var(--radius-card)",
          fontSize: "0.8125rem",
          color: "var(--text-secondary)",
          lineHeight: 1.5,
        }}
      >
        <FileText size={18} color="var(--brand-600)" className="shrink-0 mt-0.5" />
        <div>
          <span style={{ fontWeight: 700, color: "var(--brand-900)" }}>
            {lang === "mr" ? "अधिकृत मसुदा मार्गदर्शक:" : "Official Legal Drafting Guidelines:"}
          </span>{" "}
          {t("disclaimer")}
        </div>
      </div>

      {/* Advisory Banner (PRD FR-15) */}
      {advisoryElement}

      {/* Manifest Sections */}
      {manifest.sections.map((section) => {
        const isFocused = activeSectionId === section.id;
        const requiredCount = section.field_names.filter((f) => manifest.fields[f]?.required).length;
        const filledCount = section.field_names.filter(
          (f) => manifest.fields[f]?.required && !!formData[f]
        ).length;
        const isSectionComplete = requiredCount > 0 && filledCount >= requiredCount;

        return (
          <Card
            key={section.id}
            id={`section-${section.id}`}
            padding="lg"
            variant={isFocused ? "highlight" : "default"}
            style={{
              scrollMarginTop: "80px",
              display: "flex",
              flexDirection: "column",
              gap: "18px",
            }}
            onClick={() => onSelectSection && onSelectSection(section.id)}
          >
            {/* Section Header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingBottom: "12px",
                borderBottom: "1px solid var(--line-subtle)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "var(--radius-pill)",
                    backgroundColor: "var(--brand-50)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {getSectionIcon(section.id)}
                </div>
                <div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: "1.125rem",
                      fontWeight: 700,
                      color: "var(--brand-600)",
                      fontFamily: "var(--font-ui)",
                    }}
                  >
                    {lang === "mr" ? section.title_mr : section.title_en}
                  </h2>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {section.id === "property_details" && onOpenPropertySearch && (
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    pill
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenPropertySearch();
                    }}
                    leftIcon={<Search size={14} />}
                  >
                    {lang === "mr" ? "जतन केलेली मिळकत" : "Reuse Property"}
                  </Button>
                )}
                {requiredCount > 0 && (
                  <Badge
                    variant={isSectionComplete ? "active" : "neutral"}
                    size="sm"
                    label={
                      isSectionComplete
                        ? lang === "mr" ? "पूर्ण" : "Complete"
                        : `${filledCount}/${requiredCount} ${t("form.required")}`
                    }
                    icon={isSectionComplete ? <CheckCircle2 size={12} /> : undefined}
                  />
                )}
              </div>
            </div>

            {/* Field Grid */}
            <div
              className="lekhan-field-grid"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                gap: "16px",
              }}
            >
              {section.field_names.map((fKey) => {
                const fDef = manifest.fields[fKey];
                if (!fDef) return null;

                const isTotalAmount = fKey === "financial.total_consideration";
                const isAdvanceAmount = fKey === "financial.earnest_advance";

                return (
                  <div key={fKey} style={{ display: "flex", flexDirection: "column" }}>
                    <Input
                      id={fKey}
                      label={lang === "mr" ? fDef.label_mr || fKey : fDef.label_en || fKey}
                      type={fDef.type === "decimal" || fDef.type === "integer" ? "number" : "text"}
                      value={formData[fKey] ?? ""}
                      onChange={(e) => handleFieldChange(fKey, e.target.value)}
                      required={fDef.required}
                      requiredMarker={t("form.required")}
                      helperText={lang === "mr" ? fDef.help_text_mr : fDef.help_text_en}
                      placeholder={fDef.type === "decimal" ? "0.00" : undefined}
                    />

                    {/* Live Amount in words for financial inputs */}
                    {(isTotalAmount || isAdvanceAmount) && (
                      <LiveAmountInWords amount={formData[fKey]} language={lang} />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Section Summary Row */}
            {section.id === "financial_details" && (
              <div
                style={{
                  marginTop: "6px",
                  padding: "12px 16px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: "var(--surface-sunken)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                  {t("form.balance_due")}:
                </span>
                <span
                  style={{
                    fontSize: "1.0625rem",
                    fontWeight: 700,
                    color: "var(--brand-600)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  ₹ {derivedValues["financial.balance_amount"].toLocaleString("en-IN")}
                </span>
              </div>
            )}

            {section.id === "property_details" && (
              <div
                style={{
                  marginTop: "6px",
                  padding: "12px 16px",
                  borderRadius: "var(--radius-input)",
                  backgroundColor: "var(--surface-sunken)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                  {t("form.area_sqft")}:
                </span>
                <span
                  style={{
                    fontSize: "1.0625rem",
                    fontWeight: 700,
                    color: "var(--brand-600)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {derivedValues["property.area_sqft"]} sq. ft.
                </span>
              </div>
            )}
          </Card>
        );
      })}

      {/* Repeaters (Instalments, Witnesses, etc.) */}
      {Object.entries(manifest.repeaters).map(([repKey, repDef]) => (
        <Card
          key={repKey}
          id={`section-${repKey}`}
          padding="lg"
          style={{ scrollMarginTop: "80px" }}
        >
          <RepeaterGroup
            id={repKey}
            label={lang === "mr" ? repDef.label_mr || repKey : repDef.label_en || repKey}
            min={repDef.min}
            max={repDef.max}
            fields={repDef.fields}
            items={repeatersData[repKey] || []}
            onChange={(items) => handleRepeatersChange(repKey, items)}
            onOpenPartySearch={onOpenPartySearch}
          />
        </Card>
      ))}

      {/* Sticky Bottom Actions Bar (Mobile & Quick Export) */}
      <div
        className="lekhan-bottom-bar"
        style={{
          position: "sticky",
          bottom: "16px",
          zIndex: 50,
          backgroundColor: "var(--brand-900)",
          color: "var(--text-on-dark)",
          padding: "14px 20px",
          borderRadius: "var(--radius-card)",
          boxShadow: "var(--shadow-dialog)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ fontSize: "0.8125rem", opacity: 0.85, fontWeight: 500 }}>
            {lang === "mr" ? manifest.name_mr : manifest.name_en}
          </div>
          <Badge
            variant="approved"
            size="sm"
            label="Legal Std"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          pill
          size="md"
          isLoading={isSubmitting}
          leftIcon={<CheckCircle2 size={16} />}
          style={{ minWidth: "160px" }}
        >
          {isSubmitting ? t("actions.calculating") : t("actions.generate")}
        </Button>
      </div>
    </form>
  );
};
