import React, { useEffect } from "react";
import { Plus, Trash2, ArrowUp, ArrowDown, UserPlus, Search } from "lucide-react";
import { FieldDefinition } from "./types";
import { useI18n } from "../../shared/i18n";
import { Button, Input, Card, EmptyState } from "../../shared/components";

interface Props {
  id: string;
  label: string;
  min: number;
  max: number;
  fields: Record<string, FieldDefinition>;
  items: any[];
  onChange: (items: any[]) => void;
  onOpenPartySearch?: (targetRole: string, index?: number) => void;
}

export const RepeaterGroup: React.FC<Props> = ({
  id,
  label,
  min,
  max,
  fields,
  items,
  onChange,
  onOpenPartySearch,
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

  const handleMove = (index: number, direction: "up" | "down") => {
    const targetIdx = direction === "up" ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= items.length) return;
    const updated = [...items];
    const [moved] = updated.splice(index, 1);
    updated.splice(targetIdx, 0, moved);
    onChange(updated);
  };

  const handleChange = (index: number, fieldKey: string, value: any) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [fieldKey]: value };
    onChange(updated);
  };

  // Keyboard shortcut: Ctrl+Enter adds row
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        const activeEl = document.activeElement;
        const container = document.getElementById(`repeater-${id}`);
        if (container && container.contains(activeEl)) {
          e.preventDefault();
          handleAdd();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [items, max, id]);

  return (
    <div id={`repeater-${id}`} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: "1.0625rem",
              fontWeight: 700,
              color: "var(--brand-600)",
              fontFamily: "var(--font-ui)",
            }}
          >
            {label}
          </h3>
          <p style={{ margin: "2px 0 0 0", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            {lang === "mr"
              ? `किमान ${min}, कमाल ${max} नोंदी (सध्या: ${items.length})`
              : `Min ${min}, Max ${max} entries (Current: ${items.length})`}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {onOpenPartySearch && (id === "sellers" || id === "purchasers") && (
            <Button
              type="button"
              size="sm"
              variant="secondary"
              pill
              onClick={() => onOpenPartySearch(id === "purchasers" ? "purchaser" : "seller")}
              leftIcon={<Search size={14} />}
            >
              {lang === "mr" ? "जतन केलेले पक्षकार" : "Reuse Saved"}
            </Button>
          )}
          <Button
            type="button"
            size="sm"
            variant="secondary"
            pill
            onClick={handleAdd}
            disabled={items.length >= max}
            leftIcon={<Plus size={14} />}
            title={lang === "mr" ? "नवीन नोंद जोडा (Ctrl+Enter)" : "Add entry (Ctrl+Enter)"}
          >
            {t("actions.add_item")}
          </Button>
        </div>
      </div>

      {/* Empty State */}
      {items.length === 0 ? (
        <EmptyState
          icon={<UserPlus size={24} />}
          title={label}
          description={
            lang === "mr"
              ? "या विभागात अद्याप कोणतीही नोंद नाही. नोंद जोडण्यासाठी वरील बटण दाबा."
              : "No entries recorded in this section yet. Click 'Add Entry' to proceed."
          }
          action={
            <Button size="sm" onClick={handleAdd} leftIcon={<Plus size={14} />}>
              {t("actions.add_item")}
            </Button>
          }
        />
      ) : (
        /* Cards list */
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {items.map((item, idx) => (
            <Card
              key={idx}
              padding="md"
              style={{
                backgroundColor: "var(--surface-card)",
                border: "1px solid var(--line-medium)",
                borderRadius: "var(--radius-card)",
              }}
            >
              {/* Card top bar */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  paddingBottom: "10px",
                  borderBottom: "1px solid var(--line-subtle)",
                  marginBottom: "14px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: "var(--brand-900)",
                      backgroundColor: "var(--surface-sunken)",
                      padding: "2px 8px",
                      borderRadius: "var(--radius-pill)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    #{idx + 1}
                  </span>
                  <span
                    style={{
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {label} {idx + 1}
                  </span>
                </div>

                {/* Actions: Reorder & Remove */}
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <button
                    type="button"
                    onClick={() => handleMove(idx, "up")}
                    disabled={idx === 0}
                    aria-label={t("actions.move_up")}
                    title={t("actions.move_up")}
                    style={{
                      background: "none",
                      border: "none",
                      padding: "4px",
                      cursor: idx === 0 ? "not-allowed" : "pointer",
                      opacity: idx === 0 ? 0.3 : 0.7,
                      color: "var(--text-primary)",
                      borderRadius: "var(--radius-input)",
                    }}
                  >
                    <ArrowUp size={14} />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleMove(idx, "down")}
                    disabled={idx === items.length - 1}
                    aria-label={t("actions.move_down")}
                    title={t("actions.move_down")}
                    style={{
                      background: "none",
                      border: "none",
                      padding: "4px",
                      cursor: idx === items.length - 1 ? "not-allowed" : "pointer",
                      opacity: idx === items.length - 1 ? 0.3 : 0.7,
                      color: "var(--text-primary)",
                      borderRadius: "var(--radius-input)",
                    }}
                  >
                    <ArrowDown size={14} />
                  </button>
                  {items.length > min && (
                    <button
                      type="button"
                      onClick={() => handleRemove(idx)}
                      aria-label={t("actions.remove")}
                      title={t("actions.remove")}
                      style={{
                        background: "none",
                        border: "none",
                        padding: "4px",
                        cursor: "pointer",
                        color: "var(--danger-600)",
                        borderRadius: "var(--radius-input)",
                        marginLeft: "6px",
                      }}
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>
              </div>

              {/* Form fields in grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: "12px",
                }}
              >
                {Object.entries(fields).map(([fKey, fDef]) => (
                  <Input
                    key={fKey}
                    id={`${id}-${idx}-${fKey}`}
                    label={lang === "mr" ? fDef.label_mr || fKey : fDef.label_en || fKey}
                    type={fDef.type === "decimal" || fDef.type === "integer" ? "number" : fDef.type === "date" ? "date" : "text"}
                    value={item[fKey] ?? ""}
                    onChange={(e) => handleChange(idx, fKey, e.target.value)}
                    required={fDef.required}
                    requiredMarker={t("form.required")}
                    placeholder={fDef.type === "date" ? "dd/mm/yyyy" : undefined}
                  />
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
