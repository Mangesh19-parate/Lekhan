import React from "react";
import { Plus, Trash2 } from "lucide-react";
import { FieldDefinition } from "./types";
import { useI18n } from "../../shared/i18n";

interface Props {
  id: string;
  label: string;
  min: number;
  max: number;
  fields: Record<string, FieldDefinition>;
  items: any[];
  onChange: (items: any[]) => void;
}

export const RepeaterGroup: React.FC<Props> = ({
  id,
  label,
  min,
  max,
  fields,
  items,
  onChange,
}) => {
  const { lang, t } = useI18n();

  const handleAdd = () => {
    if (items.length < max) {
      const newItem: any = {};
      Object.keys(fields).forEach((k) => {
        newItem[k] = fields[k].default ?? "";
      });
      onChange([...items, newItem]);
    }
  };

  const handleRemove = (index: number) => {
    if (items.length > min) {
      const updated = items.filter((_, i) => i !== index);
      onChange(updated);
    }
  };

  const handleChange = (index: number, fieldKey: string, value: any) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [fieldKey]: value };
    onChange(updated);
  };

  return (
    <div className="space-y-4 pt-2">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-[var(--brand-600)]">{label}</h3>
          <p className="text-xs text-[var(--text-secondary)]">
            {lang === "mr"
              ? `किमान ${min}, कमाल ${max} नोंदी (सध्या: ${items.length})`
              : `Min ${min}, Max ${max} entries (Current: ${items.length})`}
          </p>
        </div>
        <button
          type="button"
          onClick={handleAdd}
          disabled={items.length >= max}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-pill)] border border-[var(--brand-500)] text-[var(--brand-500)] text-xs font-semibold hover:bg-[var(--brand-100)] disabled:opacity-40 transition-all cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{t("actions.add_item")}</span>
        </button>
      </div>

      <div className="space-y-3">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="p-4 rounded-[var(--radius-card)] bg-[var(--surface-card)] border border-[var(--line-subtle)] shadow-[var(--shadow-card)] transition-all"
          >
            <div className="flex items-center justify-between pb-3 border-b border-[var(--line-subtle)]">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--brand-800)]">
                {label} #{idx + 1}
              </span>
              {items.length > min && (
                <button
                  type="button"
                  onClick={() => handleRemove(idx)}
                  className="text-[var(--danger-600)] hover:text-red-800 p-1 rounded hover:bg-[var(--danger-tint)] transition-colors"
                  title={t("actions.remove")}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3">
              {Object.entries(fields).map(([fKey, fDef]) => (
                <div key={fKey} className="space-y-1">
                  <label className="block text-xs font-semibold text-[var(--text-primary)]">
                    {lang === "mr" ? fDef.label_mr || fKey : fDef.label_en || fKey}
                    {fDef.required && (
                      <span className="text-xs text-[var(--danger-600)] ml-1">
                        ({t("form.required")})
                      </span>
                    )}
                  </label>
                  <input
                    type="text"
                    value={item[fKey] || ""}
                    onChange={(e) => handleChange(idx, fKey, e.target.value)}
                    className="w-full px-3 py-1.5 text-sm rounded-[var(--radius-input)] border border-[var(--line-subtle)] bg-[var(--surface-card)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)] transition-all"
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

