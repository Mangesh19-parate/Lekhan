import React, { useState, useEffect, useMemo } from "react";
import { TemplateManifest } from "./types";
import { LiveAmountInWords } from "./LiveAmountInWords";
import { RepeaterGroup } from "./RepeaterGroup";
import { useI18n } from "../../shared/i18n";
import { FileText, CheckCircle, AlertTriangle } from "lucide-react";

interface Props {
  manifest: TemplateManifest;
  onSubmit: (data: any) => Promise<void>;
  isSubmitting?: boolean;
}

export const DynamicForm: React.FC<Props> = ({ manifest, onSubmit, isSubmitting = false }) => {
  const { lang, t } = useI18n();
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [repeatersData, setRepeatersData] = useState<Record<string, any[]>>({});

  // Initialize defaults
  useEffect(() => {
    const initial: Record<string, any> = {};
    Object.entries(manifest.fields).forEach(([key, field]) => {
      initial[key] = field.default ?? "";
    });
    setFormData(initial);

    const initRepeaters: Record<string, any[]> = {};
    Object.entries(manifest.repeaters).forEach(([key, rep]) => {
      const initialCount = Math.max(1, rep.min);
      initRepeaters[key] = Array.from({ length: initialCount }, () => ({}));
    });
    setRepeatersData(initRepeaters);
  }, [manifest]);

  // Handle single field change
  const handleFieldChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  // Compute derived fields live
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

  return (
    <form onSubmit={handleSubmit} className="max-w-[760px] mx-auto space-y-8">
      {/* Disclaimer Banner per DESIGN.md §4.5 */}
      <div className="bg-[var(--surface-sunken)] p-3.5 rounded-[var(--radius-card)] border-l-4 border-[var(--brand-500)] text-xs text-[var(--text-secondary)] flex items-start gap-2.5">
        <FileText className="w-4 h-4 text-[var(--brand-600)] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[var(--text-primary)]">
            {lang === "mr" ? "अधिकृत मसुदा मार्गदर्शक:" : "Official Draft Guidelines:"}
          </span>{" "}
          {t("disclaimer")}
        </div>
      </div>

      {/* Sections and Fields */}
      {manifest.sections.map((section) => (
        <div
          key={section.id}
          className="bg-[var(--surface-card)] rounded-[var(--radius-card)] p-6 shadow-[var(--shadow-card)] border border-[var(--line-subtle)] space-y-4"
        >
          <div className="border-b border-[var(--line-subtle)] pb-2.5">
            <h2 className="text-lg font-bold text-[var(--brand-600)]">
              {lang === "mr" ? section.title_mr : section.title_en}
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {section.field_names.map((fKey) => {
              const fDef = manifest.fields[fKey];
              if (!fDef) return null;

              const isTotalAmount = fKey === "financial.total_consideration";
              const isAdvanceAmount = fKey === "financial.earnest_advance";

              return (
                <div key={fKey} className="space-y-1.5">
                  <label className="block text-xs font-semibold text-[var(--text-primary)]">
                    {lang === "mr" ? fDef.label_mr || fKey : fDef.label_en || fKey}
                    {fDef.required && (
                      <span className="text-xs text-[var(--danger-600)] ml-1">
                        ({t("form.required")})
                      </span>
                    )}
                  </label>

                  <input
                    type={fDef.type === "decimal" || fDef.type === "integer" ? "number" : "text"}
                    value={formData[fKey] ?? ""}
                    onChange={(e) => handleFieldChange(fKey, e.target.value)}
                    required={fDef.required}
                    className="w-full h-10 px-3 text-sm rounded-[var(--radius-input)] border border-[var(--line-subtle)] bg-[var(--surface-card)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)] transition-all"
                  />

                  {/* Live Amount in words for financial inputs */}
                  {(isTotalAmount || isAdvanceAmount) && (
                    <LiveAmountInWords amount={formData[fKey]} language={lang} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Special Section Derived Indicators */}
          {section.id === "financial_details" && (
            <div className="pt-3 border-t border-[var(--line-subtle)] flex items-center justify-between text-sm">
              <span className="font-medium text-[var(--text-secondary)]">
                {t("form.balance_due")}:
              </span>
              <span className="font-bold text-[var(--brand-600)] text-base">
                ₹ {derivedValues["financial.balance_amount"].toLocaleString("en-IN")}
              </span>
            </div>
          )}

          {section.id === "property_details" && (
            <div className="pt-3 border-t border-[var(--line-subtle)] flex items-center justify-between text-sm">
              <span className="font-medium text-[var(--text-secondary)]">
                {t("form.area_sqft")}:
              </span>
              <span className="font-bold text-[var(--brand-600)] text-base">
                {derivedValues["property.area_sqft"]} sq. ft.
              </span>
            </div>
          )}
        </div>
      ))}

      {/* Repeaters */}
      {Object.entries(manifest.repeaters).map(([repKey, repDef]) => (
        <div
          key={repKey}
          className="bg-[var(--surface-card)] rounded-[var(--radius-card)] p-6 shadow-[var(--shadow-card)] border border-[var(--line-subtle)]"
        >
          <RepeaterGroup
            id={repKey}
            label={lang === "mr" ? repDef.label_mr || repKey : repDef.label_en || repKey}
            min={repDef.min}
            max={repDef.max}
            fields={repDef.fields}
            items={repeatersData[repKey] || []}
            onChange={(items) => setRepeatersData((prev) => ({ ...prev, [repKey]: items }))}
          />
        </div>
      ))}

      {/* Form Submission Bar */}
      <div className="sticky bottom-4 bg-[var(--brand-900)] text-[var(--text-on-dark)] p-4 rounded-[var(--radius-card)] shadow-[var(--shadow-dialog)] flex items-center justify-between">
        <div className="text-xs opacity-80">
          {manifest.name_mr} ({manifest.document_type})
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="h-10 px-6 rounded-[var(--radius-pill)] bg-[var(--brand-500)] text-[var(--text-on-dark)] font-semibold text-sm hover:bg-[#008f5a] disabled:opacity-50 transition-all cursor-pointer flex items-center gap-2"
        >
          {isSubmitting ? (
            <span>{t("actions.calculating")}</span>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              <span>{t("actions.generate")}</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};

