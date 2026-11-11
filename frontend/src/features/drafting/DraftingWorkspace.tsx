import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useI18n } from "../../shared/i18n";
import { useToast, Button, Badge, Modal } from "../../shared/components";
import { useAuth } from "../../shared/auth/AuthContext";
import { DynamicForm } from "../form_engine/DynamicForm";
import { InspectorPanel } from "../form_engine/InspectorPanel";
import { PartySearchModal } from "../parties/PartySearchModal";
import { PropertySearchModal } from "../properties/PropertySearchModal";
import { TemplateSelectorModal, TemplateCatalogItem } from "../form_engine/TemplateSelectorModal";
import { defaultManifest } from "../form_engine/sampleManifest";
import {
  FileText,
  Save,
  CheckCircle2,
  SlidersHorizontal,
  Sparkles,
  Users,
  MapPin,
  IndianRupee,
  Landmark,
  ShieldCheck,
  ChevronRight,
  PanelRightClose,
  PanelRight,
} from "lucide-react";

const SAMPLE_NAGPUR_PLOT = {
  "property.mouza": "सोनेगाव (Sonegaon)",
  "property.khasra_no": "45/2",
  "property.plot_no": "12",
  "property.layout_name": "शिवकृपा लेआउट (Shivkrupa Layout)",
  "property.sheet_no": "14",
  "property.area_sqm": 150.0,
  "boundaries.east": "९.०० मी. रुंद अंतर्गत रस्ता",
  "boundaries.west": "प्लॉट क्र. १३",
  "boundaries.north": "प्लॉट क्र. ११",
  "boundaries.south": "लेआउट सीमा",
  "financial.total_consideration": 2500000,
  "financial.earnest_advance": 500000,
};

interface DraftingWorkspaceProps {
  onNavigate: (viewId: string) => void;
  activeTemplateId?: string;
  initialDraftData?: any;
}

export const DraftingWorkspace: React.FC<DraftingWorkspaceProps> = ({
  onNavigate,
  activeTemplateId,
  initialDraftData,
}) => {
  const { lang, t } = useI18n();
  const { toast } = useToast();
  const { isAuthenticated, csrfToken } = useAuth();

  // Form State
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    if (initialDraftData?.formData) return initialDraftData.formData;
    const saved = localStorage.getItem("lekhan_current_form");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {}
    }
    const initial: Record<string, any> = {};
    Object.entries(defaultManifest.fields).forEach(([key, field]) => {
      initial[key] = field.default ?? "";
    });
    return initial;
  });

  const [repeatersData, setRepeatersData] = useState<Record<string, any[]>>(() => {
    if (initialDraftData?.repeatersData) return initialDraftData.repeatersData;
    const saved = localStorage.getItem("lekhan_current_repeaters");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {}
    }
    const initRepeaters: Record<string, any[]> = {};
    Object.entries(defaultManifest.repeaters).forEach(([key, rep]) => {
      const initialCount = Math.max(1, rep.min);
      initRepeaters[key] = Array.from({ length: initialCount }, () => {
        const item: Record<string, any> = {};
        Object.keys(rep.fields).forEach((fKey) => {
          item[fKey] = rep.fields[fKey].default ?? "";
        });
        return item;
      });
    });
    return initRepeaters;
  });

  // UI Panels
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [activeSectionId, setActiveSectionId] = useState<string>("property_details");
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving">("saved");
  const [submitting, setSubmitting] = useState(false);

  // Template Modal
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [activeTemplate, setActiveTemplate] = useState<TemplateCatalogItem>({
    template_id: defaultManifest.template_id,
    name_en: defaultManifest.name_en,
    name_mr: defaultManifest.name_mr,
    version: defaultManifest.version,
    status: "approved",
    language: defaultManifest.language,
    document_type: defaultManifest.document_type,
    property_type: defaultManifest.property_type,
    has_docx: true,
  });

  // Modals for Party and Property Search & Reuse
  const [partyModalOpen, setPartyModalOpen] = useState(false);
  const [partyTargetRole, setPartyTargetRole] = useState<"seller" | "purchaser">("seller");
  const [partyTargetIndex, setPartyTargetIndex] = useState<number | undefined>(undefined);
  const [propertyModalOpen, setPropertyModalOpen] = useState(false);

  // Debounced Autosave to localStorage
  useEffect(() => {
    setSaveStatus("saving");
    const timer = setTimeout(() => {
      localStorage.setItem("lekhan_current_form", JSON.stringify(formData));
      localStorage.setItem("lekhan_current_repeaters", JSON.stringify(repeatersData));
      setSaveStatus("saved");
    }, 500);
    return () => clearTimeout(timer);
  }, [formData, repeatersData]);

  // Derived values calculation
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

  // Count required fields
  const requiredFieldsCount = useMemo(() => {
    const requiredKeys = Object.entries(defaultManifest.fields)
      .filter(([_, def]) => def.required)
      .map(([k]) => k);
    const filled = requiredKeys.filter((k) => !!formData[k]).length;
    return { filled, total: requiredKeys.length };
  }, [formData]);

  const handleFieldChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleRepeatersChange = (key: string, items: any[]) => {
    setRepeatersData((prev) => ({ ...prev, [key]: items }));
  };

  const handleOpenPartySearch = (targetRole: string, index?: number) => {
    setPartyTargetRole(targetRole === "purchaser" ? "purchaser" : "seller");
    setPartyTargetIndex(index);
    setPartyModalOpen(true);
  };

  const handleSelectParty = (partyData: any) => {
    const repKey = partyTargetRole === "purchaser" ? "purchasers" : "sellers";
    setRepeatersData((prev) => {
      const list = [...(prev[repKey] || [])];
      if (partyTargetIndex !== undefined && partyTargetIndex < list.length) {
        list[partyTargetIndex] = { ...list[partyTargetIndex], ...partyData };
      } else {
        list.push(partyData);
      }
      return { ...prev, [repKey]: list };
    });
    toast({
      type: "success",
      title: lang === "mr" ? "पक्षकार भरला (Party Applied)" : "Party Applied",
      description: partyData.full_name,
    });
  };

  const handleSelectProperty = (propertyData: Record<string, any>) => {
    setFormData((prev) => ({ ...prev, ...propertyData }));
    toast({
      type: "success",
      title: lang === "mr" ? "मिळकत लागू केली (Property Applied)" : "Property Applied",
      description: propertyData["property.mouza"] || "Property attributes loaded.",
    });
  };

  const handleLoadSample = () => {
    setFormData((prev) => ({ ...prev, ...SAMPLE_NAGPUR_PLOT }));
    toast({
      type: "success",
      title: lang === "mr" ? "नागपूर भूखंड नमुना भरला" : "Nagpur Plot Sample Loaded",
      description: "Sample Khasra 45/2, Sonegaon plot loaded into form.",
    });
  };

  const scrollToSection = (secId: string) => {
    setActiveSectionId(secId);
    const el = document.getElementById(`section-${secId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Submit and DOCX Generation
  const handleSubmit = async (submitData: Record<string, any>) => {
    setSubmitting(true);
    try {
      const mappedSellers = (repeatersData.sellers && repeatersData.sellers.length > 0)
        ? repeatersData.sellers.map((s) => ({
            full_name: s.full_name || "आनंद बळवंत जोशी",
            gender: s.gender || "male",
            age: parseInt(s.age, 10) || 40,
            occupation: s.occupation || "व्यवसाय",
            address: s.address || "नागपूर",
            pan: s.pan || "ABCDE1234F",
          }))
        : [
            {
              full_name: "आनंद बळवंत जोशी",
              gender: "male",
              age: 52,
              occupation: "व्यवसाय",
              address: "फ्लॅट क्र. 201, समर्थ संकुल, धरमपेठ, नागपूर",
              pan: "ABCDE1234F",
            },
          ];

      const mappedPurchasers = (repeatersData.purchasers && repeatersData.purchasers.length > 0)
        ? repeatersData.purchasers.map((p) => ({
            full_name: p.full_name || "सुरेश रामराव पाटील",
            gender: p.gender || "male",
            age: parseInt(p.age, 10) || 40,
            occupation: p.occupation || "व्यवसाय",
            address: p.address || "नागपूर",
            pan: p.pan || "FGHIJ5678K",
          }))
        : [
            {
              full_name: "सुरेश रामराव पाटील",
              gender: "male",
              age: 41,
              occupation: "नोकरी",
              address: "प्लॉट क्र. 45, त्रिमूर्ती नगर, नागपूर",
              pan: "FGHIJ5678K",
            },
          ];

      const mappedInstalments = (repeatersData.instalments || []).map((inst) => ({
        amount: parseFloat(inst.amount) || 100000.0,
        mode: inst.mode || "cheque",
        ref_no: inst.ref_no || "CHQ123456",
        bank_name: inst.bank_name || "स्टेट बँक ऑफ इंडिया",
        date_str: inst.date || "09/11/2026",
      }));

      const witness1 = repeatersData.witnesses?.[0]?.name
        ? `१) श्री. ${repeatersData.witnesses[0].name}, रा. ${repeatersData.witnesses[0].address || "नागपूर"}`
        : "१) श्री. विजय एकनाथ जोशी, रा. नागपूर";

      const witness2 = repeatersData.witnesses?.[1]?.name
        ? `२) श्री. ${repeatersData.witnesses[1].name}, रा. ${repeatersData.witnesses[1].address || "नागपूर"}`
        : "२) श्री. सचिन मनोहर देशमुख, रा. नागपूर";

      const payload = {
        execution_date: "०९ नोव्हेंबर २०२६",
        sellers: mappedSellers,
        purchasers: mappedPurchasers,
        property_details: {
          mouza: submitData["property.mouza"] || "सोनेगाव",
          khasra_no: submitData["property.khasra_no"] || "45/2",
          plot_no: submitData["property.plot_no"] || "12",
          layout_name: submitData["property.layout_name"] || "शिवकृपा लेआउट",
          sheet_no: submitData["property.sheet_no"] || "14",
          area_sqm: parseFloat(submitData["property.area_sqm"]) || 150.0,
        },
        boundaries: {
          east: submitData["boundaries.east"] || "रस्ता",
          west: submitData["boundaries.west"] || "प्लॉट क्र. १३",
          north: submitData["boundaries.north"] || "प्लॉट क्र. ११",
          south: submitData["boundaries.south"] || "लेआउट सीमा",
        },
        financial: {
          total_consideration: parseFloat(submitData["financial.total_consideration"]) || 2500000.0,
          earnest_advance: parseFloat(submitData["financial.earnest_advance"]) || 500000.0,
          instalments: mappedInstalments,
        },
        witness_1: witness1,
        witness_2: witness2,
      };

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (csrfToken) headers["X-CSRF-Token"] = csrfToken;

      const res = await fetch("/api/v1/documents", {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        const downloadUrl = data.download_url || `/api/v1/documents/${data.document_id}/download`;
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `Sale_Deed_${payload.property_details.plot_no}_${payload.property_details.mouza}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        toast({
          type: "success",
          title: lang === "mr" ? "दस्त निर्मिती यशस्वी!" : "Document Generated Successfully",
          description: `क्रमांक: ${data.doc_no || data.document_id}`,
        });
        return;
      }

      // Fallback direct spike
      const spikeRes = await fetch("/api/v1/documents/generate-spike", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!spikeRes.ok) throw new Error("Document generation failed.");
      const blob = await spikeRes.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Sale_Deed_${payload.property_details.plot_no}_${payload.property_details.mouza}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();

      toast({
        type: "success",
        title: lang === "mr" ? "दस्त डाऊनलोड झाला!" : "DOCX Downloaded Successfully",
        description: `Sale_Deed_${payload.property_details.plot_no}_${payload.property_details.mouza}.docx`,
      });
    } catch (err: any) {
      toast({
        type: "error",
        title: lang === "mr" ? "दस्त निर्मितीमध्ये त्रुटी आली" : "Document Generation Failed",
        description: err?.message || "Please check required fields.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: "flex", flex: 1, minHeight: 0, height: "calc(100vh - 56px)" }}>
      {/* 1. LEFT FORM SECTIONS NAV */}
      <nav
        style={{
          width: "220px",
          flexShrink: 0,
          backgroundColor: "var(--surface-sunken)",
          borderRight: "1px solid var(--line-subtle)",
          padding: "16px 12px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          overflowY: "auto",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <div style={{ fontSize: "0.6875rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-tertiary)", padding: "0 8px 6px 8px" }}>
            {lang === "mr" ? "दस्त विभाग" : "Sections"}
          </div>

          {defaultManifest.sections.map((sec) => {
            const isActive = activeSectionId === sec.id;
            return (
              <button
                key={sec.id}
                type="button"
                onClick={() => scrollToSection(sec.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "7px 10px",
                  borderRadius: "var(--radius-input)",
                  border: "none",
                  backgroundColor: isActive ? "var(--brand-100)" : "transparent",
                  color: isActive ? "var(--brand-900)" : "var(--text-secondary)",
                  fontSize: "0.8125rem",
                  fontWeight: isActive ? 700 : 500,
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                {sec.id === "property_details" && <Landmark size={14} color={isActive ? "var(--brand-600)" : "var(--text-tertiary)"} />}
                {sec.id === "boundaries" && <MapPin size={14} color={isActive ? "var(--brand-600)" : "var(--text-tertiary)"} />}
                {sec.id === "financial_details" && <IndianRupee size={14} color={isActive ? "var(--brand-600)" : "var(--text-tertiary)"} />}
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {lang === "mr" ? sec.title_mr : sec.title_en}
                </span>
              </button>
            );
          })}

          {Object.entries(defaultManifest.repeaters).map(([repKey, repDef]) => {
            const isActive = activeSectionId === repKey;
            return (
              <button
                key={repKey}
                type="button"
                onClick={() => scrollToSection(repKey)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "7px 10px",
                  borderRadius: "var(--radius-input)",
                  border: "none",
                  backgroundColor: isActive ? "var(--brand-100)" : "transparent",
                  color: isActive ? "var(--brand-900)" : "var(--text-secondary)",
                  fontSize: "0.8125rem",
                  fontWeight: isActive ? 700 : 500,
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <Users size={14} color={isActive ? "var(--brand-600)" : "var(--text-tertiary)"} />
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {lang === "mr" ? repDef.label_mr || repKey : repDef.label_en || repKey}
                </span>
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px", paddingTop: "12px", borderTop: "1px solid var(--line-subtle)" }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleLoadSample}
            leftIcon={<Sparkles size={13} />}
            style={{ width: "100%", justifyContent: "flex-start", fontSize: "0.75rem" }}
          >
            {t("actions.load_sample")}
          </Button>

          <Button
            size="sm"
            variant="secondary"
            onClick={() => setPropertyModalOpen(true)}
            leftIcon={<MapPin size={13} />}
            style={{ width: "100%", justifyContent: "flex-start", fontSize: "0.75rem" }}
          >
            {lang === "mr" ? "मिळकत शोधा (Reuse)" : "Find Property"}
          </Button>
        </div>
      </nav>

      {/* 2. CENTER WORKSPACE FORM */}
      <main style={{ flex: 1, overflowY: "auto", padding: "24px 32px", display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Template selector banner */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "var(--surface-card)", padding: "12px 18px", borderRadius: "var(--radius-card)", border: "1px solid var(--line-subtle)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <FileText size={20} color="var(--brand-600)" />
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--brand-900)" }}>
                {lang === "mr" ? activeTemplate.name_mr : activeTemplate.name_en}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                Approved Template ({activeTemplate.template_id}) | Legal Size (12240x20160 dxa)
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <Button size="sm" variant="secondary" onClick={() => setTemplateModalOpen(true)}>
              {lang === "mr" ? "साचा बदला" : "Change Template"}
            </Button>
            <button
              type="button"
              onClick={() => setInspectorOpen((prev) => !prev)}
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                padding: "6px",
                borderRadius: "var(--radius-input)",
                color: "var(--text-secondary)",
              }}
              title="Toggle Live Calculation Panel"
            >
              {inspectorOpen ? <PanelRightClose size={18} /> : <PanelRight size={18} />}
            </button>
          </div>
        </div>

        {/* Dynamic Form Engine */}
        <DynamicForm
          manifest={defaultManifest}
          formData={formData}
          repeatersData={repeatersData}
          onFieldChange={handleFieldChange}
          onRepeatersChange={handleRepeatersChange}
          onOpenPartySearch={handleOpenPartySearch}
          onSubmit={handleSubmit}
          isSubmitting={submitting}
        />
      </main>

      {/* 3. RIGHT COLLAPSIBLE INSPECTOR PANEL */}
      {inspectorOpen && (
        <aside style={{ width: "320px", flexShrink: 0, borderLeft: "1px solid var(--line-subtle)", overflowY: "auto", backgroundColor: "var(--surface-card)" }}>
          <InspectorPanel
            formData={formData}
            derivedValues={derivedValues}
            repeatersData={repeatersData}
            requiredFieldsCount={requiredFieldsCount}
            onExport={() => handleSubmit(formData)}
            isSubmitting={submitting}
          />
        </aside>
      )}

      {/* Modals */}
      <TemplateSelectorModal
        isOpen={templateModalOpen}
        onClose={() => setTemplateModalOpen(false)}
        selectedTemplateId={activeTemplate.template_id}
        onSelectTemplate={(tmpl) => {
          setActiveTemplate(tmpl);
          setTemplateModalOpen(false);
        }}
      />

      <PartySearchModal
        isOpen={partyModalOpen}
        onClose={() => setPartyModalOpen(false)}
        onSelectParty={handleSelectParty}
        targetRole={partyTargetRole}
      />

      <PropertySearchModal
        isOpen={propertyModalOpen}
        onClose={() => setPropertyModalOpen(false)}
        onSelectProperty={handleSelectProperty}
      />
    </div>
  );
};
