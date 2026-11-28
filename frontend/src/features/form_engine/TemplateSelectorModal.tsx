import React, { useState, useEffect } from "react";
import { Modal, Button, Badge } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { FileText, CheckCircle2, ChevronRight, Layers } from "lucide-react";

export interface TemplateCatalogItem {
  template_id: string;
  name_en: string;
  name_mr: string;
  version: number;
  status: string;
  language: string;
  document_type: string;
  property_type: string;
  has_docx: boolean;
  has_renderer?: boolean;
  can_generate?: boolean;
}

const FALLBACK_TEMPLATES: TemplateCatalogItem[] = [
  {
    template_id: "sale_deed_plot_mr",
    name_en: "Sale Deed (Plot in NIT/NMC Layout)",
    name_mr: "खरेदीखत (भूखंड - ना.सु.प्र./ना.म.पा. लेआउट)",
    version: 1,
    status: "approved",
    language: "mr",
    document_type: "sale_deed",
    property_type: "plot",
    has_docx: true,
    has_renderer: true,
    can_generate: true,
  },
  {
    template_id: "agreement_to_sell_plot_mr",
    name_en: "Agreement to Sell (Plot / Isar Pawati)",
    name_mr: "साठेखत / इसारपावती (भूखंड)",
    version: 1,
    status: "draft",
    language: "mr",
    document_type: "agreement_to_sell",
    property_type: "plot",
    has_docx: true,
    has_renderer: false,
    can_generate: false,
  },
  {
    template_id: "sale_deed_flat_mr",
    name_en: "Sale Deed (Apartment / Flat)",
    name_mr: "खरेदीखत (सदनिका / फ्लॅट)",
    version: 1,
    status: "draft",
    language: "mr",
    document_type: "sale_deed",
    property_type: "flat",
    has_docx: true,
    has_renderer: false,
    can_generate: false,
  },
  {
    template_id: "sale_deed_flat_en",
    name_en: "Sale Deed (Residential Flat - English)",
    name_mr: "विक्री विलेख (सदनिका - इंग्रजी)",
    version: 1,
    status: "draft",
    language: "en",
    document_type: "sale_deed",
    property_type: "flat",
    has_docx: true,
    has_renderer: false,
    can_generate: false,
  },
  {
    template_id: "general_poa_mr",
    name_en: "General Power of Attorney",
    name_mr: "कुलमुखत्यारपत्र (General Power of Attorney)",
    version: 1,
    status: "draft",
    language: "mr",
    document_type: "power_of_attorney",
    property_type: "general",
    has_docx: true,
    has_renderer: false,
    can_generate: false,
  },
  {
    template_id: "general_poa_en",
    name_en: "General Power of Attorney (English)",
    name_mr: "कुलमुखत्यारपत्र (इंग्रजी)",
    version: 1,
    status: "draft",
    language: "en",
    document_type: "power_of_attorney",
    property_type: "general",
    has_docx: true,
    has_renderer: false,
    can_generate: false,
  },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  selectedTemplateId: string;
  onSelectTemplate: (template: TemplateCatalogItem) => void;
}

export const TemplateSelectorModal: React.FC<Props> = ({
  isOpen,
  onClose,
  selectedTemplateId,
  onSelectTemplate,
}) => {
  const { lang } = useI18n();
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>(FALLBACK_TEMPLATES);
  const [filterLang, setFilterLang] = useState<"all" | "mr" | "en">("all");

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const res = await fetch("/api/v1/templates", {
          method: "GET",
          credentials: "include",
        });
        if (res.ok) {
          const data: TemplateCatalogItem[] = await res.json();
          if (data && data.length > 0) {
            setTemplates(data);
          }
        }
      } catch {
        // Use fallback templates
      }
    };
    if (isOpen) {
      fetchTemplates();
    }
  }, [isOpen]);

  const filtered = templates.filter((t) => {
    if (filterLang === "all") return true;
    return t.language === filterLang;
  });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={lang === "mr" ? "दस्तऐवज साचा निवडा (Select Template)" : "Select Approved Template"}
      description="Choose from officially approved deed templates in the legal library"
      maxWidth="620px"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {/* Language Filter */}
        <div style={{ display: "flex", gap: "6px" }}>
          <Button
            size="sm"
            variant={filterLang === "all" ? "primary" : "secondary"}
            pill
            onClick={() => setFilterLang("all")}
          >
            All Templates ({templates.length})
          </Button>
          <Button
            size="sm"
            variant={filterLang === "mr" ? "primary" : "secondary"}
            pill
            onClick={() => setFilterLang("mr")}
          >
            मराठी (MR)
          </Button>
          <Button
            size="sm"
            variant={filterLang === "en" ? "primary" : "secondary"}
            pill
            onClick={() => setFilterLang("en")}
          >
            English (EN)
          </Button>
        </div>

        {/* Template List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "400px", overflowY: "auto" }}>
          {filtered.map((item) => {
            const isSelected = item.template_id === selectedTemplateId;
            const canGenerate = item.status === "approved" && item.has_docx && item.has_renderer !== false;

            const getBadgeProps = () => {
              switch (item.status) {
                case "approved":
                  return {
                    variant: "approved" as const,
                    label: lang === "mr" ? "मंजूर (Approved)" : "Approved",
                  };
                case "under_review":
                  return {
                    variant: "under_review" as const,
                    label: lang === "mr" ? "पुनरावलोकन" : "Under Review",
                  };
                case "retired":
                  return {
                    variant: "danger" as const,
                    label: lang === "mr" ? "कालबाह्य" : "Retired",
                  };
                case "draft":
                default:
                  return {
                    variant: "draft" as const,
                    label: lang === "mr" ? "मसुदा (Draft)" : "Draft",
                  };
              }
            };

            const badgeProps = getBadgeProps();

            return (
              <div
                key={item.template_id}
                onClick={() => {
                  if (!canGenerate) return;
                  onSelectTemplate(item);
                  onClose();
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 16px",
                  borderRadius: "var(--radius-card)",
                  backgroundColor: isSelected ? "var(--brand-100)" : "var(--surface-sunken)",
                  border: isSelected ? "1.5px solid var(--brand-500)" : "1px solid var(--line-subtle)",
                  cursor: canGenerate ? "pointer" : "not-allowed",
                  opacity: canGenerate ? 1 : 0.65,
                  transition: "all var(--transition-fast)",
                }}
                className={canGenerate ? "hover:border-[var(--brand-500)]" : ""}
                title={
                  !canGenerate
                    ? item.status !== "approved"
                      ? "Draft status: Only officially approved templates can generate deeds."
                      : "Generation unavailable: DOCX template or renderer not active."
                    : undefined
                }
              >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <FileText
                    size={20}
                    color={isSelected ? "var(--brand-600)" : "var(--text-secondary)"}
                    className="shrink-0"
                  />
                  <div>
                    <div style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      {lang === "mr" ? item.name_mr || item.name_en : item.name_en}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                      <span>Type: {item.document_type}</span>
                      <span style={{ marginLeft: "8px" }}>• Property: {item.property_type}</span>
                      <span style={{ marginLeft: "8px" }}>• Lang: {item.language.toUpperCase()}</span>
                    </div>
                    {!canGenerate && (
                      <div style={{ fontSize: "0.71875rem", color: "var(--warning-600)", marginTop: "3px" }}>
                        {lang === "mr"
                          ? "मसुदा साचा — अधिकृत मंजुरीनंतरच दस्त निर्मिती उपलब्ध होईल"
                          : "Draft template — Generation disabled until officially approved"}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Badge variant={badgeProps.variant} size="sm" label={badgeProps.label} />
                  {isSelected ? (
                    <CheckCircle2 size={18} color="var(--brand-600)" />
                  ) : (
                    <ChevronRight size={16} color="var(--text-tertiary)" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Modal>
  );
};
