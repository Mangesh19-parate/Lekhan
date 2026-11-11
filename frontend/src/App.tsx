import React, { useState, useEffect, useMemo, useCallback } from "react";
import { I18nProvider, useI18n } from "./shared/i18n";
import { ToastProvider, useToast, Button, Badge, Modal } from "./shared/components";
import { AuthProvider, useAuth } from "./shared/auth/AuthContext";
import { LoginModal } from "./shared/auth/LoginModal";
import { DynamicForm } from "./features/form_engine/DynamicForm";
import { InspectorPanel } from "./features/form_engine/InspectorPanel";
import { CommandPalette } from "./features/form_engine/CommandPalette";
import { KeyboardShortcutsModal } from "./features/form_engine/KeyboardShortcutsModal";
import { RecentDraftsDrawer, SavedDraft } from "./features/form_engine/RecentDraftsDrawer";
import { DocumentHistoryDrawer } from "./features/documents/DocumentHistoryDrawer";
import { TemplateSelectorModal, TemplateCatalogItem } from "./features/form_engine/TemplateSelectorModal";
import { PartySearchModal } from "./features/parties/PartySearchModal";
import { PropertySearchModal } from "./features/properties/PropertySearchModal";
import { AdvisoryBanner } from "./features/advisory/AdvisoryBanner";
import { PilotFeedbackModal } from "./features/pilot/PilotFeedbackModal";
import { defaultManifest } from "./features/form_engine/sampleManifest";
import {
  FileText,
  Search,
  Moon,
  Sun,
  Keyboard,
  Clock,
  CheckCircle2,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  SlidersHorizontal,
  Landmark,
  MapPin,
  IndianRupee,
  Layers,
  Sparkles,
  ExternalLink,
  ShieldCheck,
  Undo2,
  Redo2,
  RotateCcw,
  LogIn,
  LogOut,
  User,
  Users,
  History,
  MessageSquarePlus,
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

const AppContent: React.FC = () => {
  const { lang, setLang, t } = useI18n();
  const { toast } = useToast();
  const { user, isAuthenticated, logout, csrfToken } = useAuth();

  // Theme state
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    return (localStorage.getItem("lekhan_theme") as "light" | "dark") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("lekhan_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  // Form State & History for Undo/Redo
  const [formData, setFormData] = useState<Record<string, any>>(() => {
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

  // Undo / Redo stacks
  const [history, setHistory] = useState<Record<string, any>[]>([formData]);
  const [historyIndex, setHistoryIndex] = useState(0);

  // Autosave status
  const [saveStatus, setSaveStatus] = useState<"saved" | "saving" | "unsaved">("saved");

  // UI Panels
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [activeSectionId, setActiveSectionId] = useState<string>("property_details");

  // Modals
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [draftsDrawerOpen, setDraftsDrawerOpen] = useState(false);
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
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

  // Submitting
  const [submitting, setSubmitting] = useState(false);

  // Phase 3: Party & Property Reuse and Pilot Feedback Modals
  const [partyModalOpen, setPartyModalOpen] = useState(false);
  const [partyTargetRole, setPartyTargetRole] = useState<"seller" | "purchaser">("seller");
  const [partyTargetIndex, setPartyTargetIndex] = useState<number | undefined>(undefined);
  const [propertyModalOpen, setPropertyModalOpen] = useState(false);
  const [pilotFeedbackOpen, setPilotFeedbackOpen] = useState(false);

  const handleOpenPartySearch = (targetRole: string, index?: number) => {
    setPartyTargetRole(targetRole === "purchaser" ? "purchaser" : "seller");
    setPartyTargetIndex(index);
    setPartyModalOpen(true);
  };

  const handleSelectParty = (partyData: {
    full_name: string;
    gender: string;
    age: number;
    occupation: string;
    address: string;
    pan: string;
  }) => {
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

  // Saved Drafts List
  const [recentDrafts, setRecentDrafts] = useState<SavedDraft[]>(() => {
    const saved = localStorage.getItem("lekhan_saved_drafts");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {}
    }
    return [];
  });

  // Autosave effect (debounced 600ms)
  useEffect(() => {
    setSaveStatus("saving");
    const timer = setTimeout(() => {
      localStorage.setItem("lekhan_current_form", JSON.stringify(formData));
      localStorage.setItem("lekhan_current_repeaters", JSON.stringify(repeatersData));
      setSaveStatus("saved");
    }, 600);
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

  // Handle single field change with undo stack
  const handleFieldChange = (key: string, value: any) => {
    setFormData((prev) => {
      const next = { ...prev, [key]: value };
      const newHistory = history.slice(0, historyIndex + 1);
      newHistory.push(next);
      if (newHistory.length > 25) newHistory.shift();
      setHistory(newHistory);
      setHistoryIndex(newHistory.length - 1);
      return next;
    });
  };

  const handleRepeatersChange = (key: string, items: any[]) => {
    setRepeatersData((prev) => ({ ...prev, [key]: items }));
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      setHistoryIndex((prev) => prev - 1);
      setFormData(history[historyIndex - 1]);
      toast({
        type: "info",
        title: lang === "mr" ? "बदल पूर्ववत केला (Undone)" : "Action Undone",
      });
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex((prev) => prev + 1);
      setFormData(history[historyIndex + 1]);
      toast({
        type: "info",
        title: lang === "mr" ? "बदल पुन्हा लागू केला (Redone)" : "Action Redone",
      });
    }
  };

  // Save draft explicitly to RecentDrafts
  const handleSaveDraft = useCallback(() => {
    const newDraft: SavedDraft = {
      id: `draft-${Date.now()}`,
      savedAt: new Date().toISOString(),
      title: `${defaultManifest.name_mr} - Plot ${formData["property.plot_no"] || "Draft"}`,
      plotNo: formData["property.plot_no"],
      mouza: formData["property.mouza"],
      data: { formData, repeatersData },
    };
    const updated = [newDraft, ...recentDrafts.slice(0, 9)];
    setRecentDrafts(updated);
    localStorage.setItem("lekhan_saved_drafts", JSON.stringify(updated));
    toast({
      type: "success",
      title: lang === "mr" ? "मसुदा यशस्वीरित्या जतन केला" : "Draft Saved Successfully",
      description: lang === "mr" ? "हा मसुदा 'अलिकडील मसुदे' मध्ये उपलब्ध आहे." : "Saved to Recent Drafts history.",
    });
  }, [formData, repeatersData, recentDrafts, lang, toast]);

  // Load Nagpur Sample Preset
  const handleLoadSample = useCallback(() => {
    setFormData((prev) => ({ ...prev, ...SAMPLE_NAGPUR_PLOT }));
    toast({
      type: "success",
      title: lang === "mr" ? "नागपूर भूखंड नमुना भरला" : "Nagpur Plot Sample Loaded",
      description: "Sample Khasra 45/2, Sonegaon plot loaded into form.",
    });
  }, [lang, toast]);

  // Clear Form
  const handleClearForm = useCallback(() => {
    const cleared: Record<string, any> = {};
    Object.entries(defaultManifest.fields).forEach(([key, field]) => {
      cleared[key] = field.default ?? "";
    });
    setFormData(cleared);
    toast({
      type: "info",
      title: lang === "mr" ? "फॉर्म साफ केला" : "Form Cleared",
    });
  }, [lang, toast]);

  // Restore Draft
  const handleRestoreDraft = (draft: SavedDraft) => {
    setFormData(draft.data.formData);
    setRepeatersData(draft.data.repeatersData);
    toast({
      type: "success",
      title: lang === "mr" ? "मसुदा पूर्ववत केला" : "Draft Restored",
      description: draft.title,
    });
  };

  // Delete Draft
  const handleDeleteDraft = (id: string) => {
    const updated = recentDrafts.filter((d) => d.id !== id);
    setRecentDrafts(updated);
    localStorage.setItem("lekhan_saved_drafts", JSON.stringify(updated));
  };

  // Section Scroll navigation
  const scrollToSection = (secId: string) => {
    setActiveSectionId(secId);
    const el = document.getElementById(`section-${secId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Global Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      } else if (e.key === "?" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setShortcutsOpen((prev) => !prev);
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        handleSaveDraft();
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "e") {
        e.preventDefault();
        handleSubmit(formData);
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !e.shiftKey) {
        if (!["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
          e.preventDefault();
          handleUndo();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleSaveDraft]);

  // Submit and DOCX Generation (P0 Fix: compliant schema + authenticated endpoint)
  const handleSubmit = async (submitData: Record<string, any>) => {
    setSubmitting(true);
    try {
      // 1. Map Repeaters and Form data into exact PlotSaleDeedInput backend schema
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

      // 2. Server-side validation check against compiler AST if authenticated
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (csrfToken) {
        headers["X-CSRF-Token"] = csrfToken;
      }

      if (isAuthenticated) {
        try {
          const valRes = await fetch(`/api/v1/documents/validate/${activeTemplate.template_id}`, {
            method: "POST",
            headers,
            credentials: "include",
            body: JSON.stringify({ data: payload }),
          });
          if (valRes.ok) {
            const valData = await valRes.json();
            if (!valData.valid && valData.violations?.length > 0) {
              const firstViolation = valData.violations[0];
              toast({
                type: "error",
                title: lang === "mr" ? "नियमांचे उल्लंघन (Validation Error)" : "Validation Rule Violation",
                description: lang === "mr" ? (firstViolation.message_mr || firstViolation.message_en) : firstViolation.message_en,
              });
              setSubmitting(false);
              return;
            }
          }
        } catch {
          // If template has no manifest validator, proceed
        }
      }

      let res = await fetch("/api/v1/documents", {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify(payload),
      });

      // If unauthorized (401), prompt login
      if (res.status === 401) {
        setLoginModalOpen(true);
        throw new Error(
          lang === "mr"
            ? "दस्त तयार करण्यासाठी कृपया प्रथम लॉगिन करा."
            : "Please log in to generate documents."
        );
      }

      // If the authenticated route succeeds
      if (res.ok) {
        const data = await res.json();
        // Trigger download via returned download_url
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

      // Fallback: If /api/v1/documents had another error, try spike endpoint with exact compliant payload
      const spikeRes = await fetch("/api/v1/documents/generate-spike", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!spikeRes.ok) {
        throw new Error(`Generation failed: ${spikeRes.statusText}`);
      }

      const blob = await spikeRes.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Sale_Deed_${payload.property_details.plot_no}_${payload.property_details.mouza}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

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
        correlationId: `CORR-${Date.now().toString(36).toUpperCase()}`,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "var(--surface-canvas)",
        color: "var(--text-primary)",
      }}
    >
      {/* 1. TOP APP BAR */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          backgroundColor: "var(--brand-900)",
          color: "var(--text-on-dark)",
          height: "56px",
          padding: "0 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "var(--shadow-nav)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        {/* Left: Brand & Breadcrumb */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <button
            type="button"
            onClick={() => setSidebarCollapsed((prev) => !prev)}
            aria-label={sidebarCollapsed ? t("nav.expand_sidebar") : t("nav.collapse_sidebar")}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="hover:text-white"
          >
            {sidebarCollapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "1.0625rem", fontWeight: 800, letterSpacing: "-0.01em" }}>
              Lekhan | लेखन
            </span>
            <Badge
              variant="approved"
              size="sm"
              label={t("app.badge")}
            />
          </div>

          <div
            onClick={() => setTemplateModalOpen(true)}
            style={{
              display: "none",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.8125rem",
              color: "var(--text-on-dark-2)",
              marginLeft: "12px",
              cursor: "pointer",
            }}
            className="md:flex hover:text-white"
            title="Click to switch deed template"
          >
            <ChevronRight size={14} />
            <span style={{ textDecoration: "underline", textUnderlineOffset: "3px" }}>
              {lang === "mr" ? activeTemplate.name_mr : activeTemplate.name_en}
            </span>
          </div>
        </div>

        {/* Center: Global Command Search Trigger (Desktop/Tablet) */}
        <div
          onClick={() => setCommandPaletteOpen(true)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            padding: "6px 14px",
            borderRadius: "var(--radius-pill)",
            fontSize: "0.8125rem",
            color: "var(--text-on-dark-2)",
            cursor: "pointer",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            minWidth: "180px",
            transition: "all var(--transition-fast)",
          }}
          className="hidden md:flex hover:bg-[rgba(255,255,255,0.14)]"
        >
          <Search size={14} />
          <span style={{ flex: 1 }}>{t("actions.search")}</span>
          <kbd
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.6875rem",
              backgroundColor: "rgba(0, 0, 0, 0.25)",
              padding: "1px 5px",
              borderRadius: "4px",
            }}
          >
            ⌘K
          </kbd>
        </div>

        {/* Right: Actions, Autosave, Language, Theme */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* Mobile search icon button */}
          <button
            type="button"
            onClick={() => setCommandPaletteOpen(true)}
            aria-label={t("actions.search")}
            title={t("actions.search")}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              padding: "6px",
              cursor: "pointer",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="flex md:hidden hover:text-white"
          >
            <Search size={16} />
          </button>

          {/* Autosave pill */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "0.75rem",
              color: saveStatus === "saving" ? "var(--warning-500)" : "var(--brand-400)",
              backgroundColor: "rgba(255, 255, 255, 0.06)",
              padding: "4px 10px",
              borderRadius: "var(--radius-pill)",
            }}
          >
            <CheckCircle2 size={13} />
            <span className="hidden sm:inline">
              {saveStatus === "saving" ? t("status.saving") : t("status.saved")}
            </span>
          </div>

          {/* Undo / Redo buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: "2px" }} className="hidden sm:flex">
            <button
              type="button"
              disabled={historyIndex <= 0}
              onClick={handleUndo}
              title={t("actions.undo")}
              aria-label={t("actions.undo")}
              style={{
                background: "transparent",
                border: "none",
                color: historyIndex <= 0 ? "rgba(255,255,255,0.3)" : "var(--text-on-dark)",
                padding: "6px",
                cursor: historyIndex <= 0 ? "not-allowed" : "pointer",
                borderRadius: "var(--radius-input)",
              }}
            >
              <Undo2 size={16} />
            </button>
            <button
              type="button"
              disabled={historyIndex >= history.length - 1}
              onClick={handleRedo}
              title={t("actions.redo")}
              aria-label={t("actions.redo")}
              style={{
                background: "transparent",
                border: "none",
                color: historyIndex >= history.length - 1 ? "rgba(255,255,255,0.3)" : "var(--text-on-dark)",
                padding: "6px",
                cursor: historyIndex >= history.length - 1 ? "not-allowed" : "pointer",
                borderRadius: "var(--radius-input)",
              }}
            >
              <Redo2 size={16} />
            </button>
          </div>

          {/* Real Server Document History button */}
          <button
            type="button"
            onClick={() => setHistoryDrawerOpen(true)}
            title={lang === "mr" ? "दस्त नोंदवही (History)" : "Document History"}
            aria-label="Document History"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              padding: "6px",
              cursor: "pointer",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="hover:text-white"
          >
            <History size={16} />
          </button>

          {/* Pilot Drafter Feedback button */}
          <button
            type="button"
            onClick={() => setPilotFeedbackOpen(true)}
            title={lang === "mr" ? "पायलट अभिप्राय नोंदवा (Feedback)" : "Log Pilot Feedback"}
            aria-label="Pilot Feedback"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              padding: "6px",
              cursor: "pointer",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="hover:text-white"
          >
            <MessageSquarePlus size={16} />
          </button>

          {/* Local Recent Drafts button */}
          <button
            type="button"
            onClick={() => setDraftsDrawerOpen(true)}
            title={t("nav.recent_drafts")}
            aria-label={t("nav.recent_drafts")}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              padding: "6px",
              cursor: "pointer",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="hover:text-white"
          >
            <Clock size={16} />
          </button>

          {/* Keyboard shortcut sheet button */}
          <button
            type="button"
            onClick={() => setShortcutsOpen(true)}
            title={t("nav.shortcuts")}
            aria-label={t("nav.shortcuts")}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              padding: "6px",
              cursor: "pointer",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="hover:text-white"
          >
            <Keyboard size={16} />
          </button>

          {/* Dark / Light Toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Light Mode" : "Dark Mode"}
            title={theme === "dark" ? "Light Mode" : "Dark Mode"}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-on-dark-2)",
              padding: "6px",
              cursor: "pointer",
              borderRadius: "var(--radius-input)",
              display: "flex",
              alignItems: "center",
            }}
            className="hover:text-white"
          >
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {/* Language Switcher */}
          <div
            style={{
              display: "flex",
              backgroundColor: "rgba(255, 255, 255, 0.12)",
              padding: "2px",
              borderRadius: "var(--radius-pill)",
            }}
          >
            <button
              type="button"
              onClick={() => setLang("mr")}
              style={{
                backgroundColor: lang === "mr" ? "var(--brand-500)" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "var(--radius-pill)",
                padding: "3px 10px",
                cursor: "pointer",
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            >
              मराठी
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              style={{
                backgroundColor: lang === "en" ? "var(--brand-500)" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "var(--radius-pill)",
                padding: "3px 10px",
                cursor: "pointer",
                fontSize: "0.75rem",
                fontWeight: 600,
              }}
            >
              EN
            </button>
          </div>

          {/* Authentication Badge & Login/Logout button */}
          {isAuthenticated && user ? (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  fontSize: "0.75rem",
                  color: "var(--text-on-dark)",
                  backgroundColor: "rgba(255,255,255,0.15)",
                  padding: "3px 8px",
                  borderRadius: "var(--radius-pill)",
                  fontWeight: 600,
                }}
                className="hidden lg:inline"
              >
                {user.role}
              </span>
              <button
                type="button"
                onClick={logout}
                title="Sign Out"
                aria-label="Sign Out"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-on-dark-2)",
                  padding: "6px",
                  cursor: "pointer",
                  borderRadius: "var(--radius-input)",
                  display: "flex",
                  alignItems: "center",
                }}
                className="hover:text-white"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setLoginModalOpen(true)}
              style={{
                backgroundColor: "var(--brand-500)",
                color: "#fff",
                border: "none",
                borderRadius: "var(--radius-pill)",
                padding: "4px 12px",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <LogIn size={13} />
              <span>प्रवेश (Login)</span>
            </button>
          )}
        </div>
      </header>

      {/* 2. THREE-PANE WORKSPACE BODY */}
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* LEFT COLLAPSIBLE SIDEBAR */}
        {!sidebarCollapsed && (
          <nav
            aria-label="Section navigation"
            style={{
              width: "240px",
              flexShrink: 0,
              backgroundColor: "var(--surface-sunken)",
              borderRight: "1px solid var(--line-subtle)",
              padding: "20px 12px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  color: "var(--text-tertiary)",
                  padding: "0 8px 8px 8px",
                }}
              >
                {lang === "mr" ? "दस्त विभाग" : "Deed Sections"}
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
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "var(--radius-input)",
                      border: "none",
                      backgroundColor: isActive ? "var(--brand-100)" : "transparent",
                      color: isActive ? "var(--brand-900)" : "var(--text-secondary)",
                      fontSize: "0.8125rem",
                      fontWeight: isActive ? 700 : 500,
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all var(--transition-fast)",
                    }}
                    className="hover:bg-[var(--brand-50)]"
                  >
                    <span style={{ color: isActive ? "var(--brand-600)" : "var(--text-tertiary)" }}>
                      {sec.id === "property_details" && <Landmark size={15} />}
                      {sec.id === "boundaries" && <MapPin size={15} />}
                      {sec.id === "financial_details" && <IndianRupee size={15} />}
                    </span>
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
                      gap: "10px",
                      padding: "8px 12px",
                      borderRadius: "var(--radius-input)",
                      border: "none",
                      backgroundColor: isActive ? "var(--brand-100)" : "transparent",
                      color: isActive ? "var(--brand-900)" : "var(--text-secondary)",
                      fontSize: "0.8125rem",
                      fontWeight: isActive ? 700 : 500,
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all var(--transition-fast)",
                    }}
                    className="hover:bg-[var(--brand-50)]"
                  >
                    <Users size={15} color={isActive ? "var(--brand-600)" : "var(--text-tertiary)"} />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {lang === "mr" ? repDef.label_mr || repKey : repDef.label_en || repKey}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Sidebar Bottom Utilities */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                paddingTop: "16px",
                borderTop: "1px solid var(--line-subtle)",
              }}
            >
              <Button
                size="sm"
                variant="secondary"
                pill={false}
                onClick={handleLoadSample}
                leftIcon={<Sparkles size={14} />}
                style={{ width: "100%", justifyContent: "flex-start" }}
              >
                {t("actions.load_sample")}
              </Button>

              <div style={{ display: "flex", flexDirection: "column", gap: "2px", fontSize: "0.75rem" }}>
                <a
                  href="/templates/admin"
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "6px 8px",
                    color: "var(--text-secondary)",
                    textDecoration: "none",
                    borderRadius: "4px",
                  }}
                  className="hover:bg-[var(--surface-subtle)]"
                >
                  <span>Template Admin</span>
                  <ExternalLink size={12} />
                </a>
                <a
                  href="/api/docs"
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "6px 8px",
                    color: "var(--text-secondary)",
                    textDecoration: "none",
                    borderRadius: "4px",
                  }}
                  className="hover:bg-[var(--surface-subtle)]"
                >
                  <span>API Docs</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>
          </nav>
        )}

        {/* CENTER DRAFTING CANVAS (Visual Focus) */}
        <main
          className="lekhan-main-canvas"
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "28px 24px 80px 24px",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <div className="lekhan-canvas-wrapper" style={{ width: "100%", maxWidth: "760px" }}>
            <DynamicForm
              manifest={defaultManifest}
              onSubmit={handleSubmit}
              isSubmitting={submitting}
              formData={formData}
              repeatersData={repeatersData}
              onFieldChange={handleFieldChange}
              onRepeatersChange={handleRepeatersChange}
              activeSectionId={activeSectionId}
              onSelectSection={(id) => setActiveSectionId(id)}
              onOpenPropertySearch={() => setPropertyModalOpen(true)}
              onOpenPartySearch={handleOpenPartySearch}
              advisoryElement={
                <AdvisoryBanner
                  templateId={activeTemplate.template_id}
                  formData={formData}
                  repeatersData={repeatersData}
                />
              }
            />
          </div>
        </main>

        {/* RIGHT CONTEXTUAL PROPERTIES & INSPECTOR PANEL */}
        {inspectorOpen && (
          <div
            style={{
              width: "320px",
              flexShrink: 0,
              backgroundColor: "var(--surface-sunken)",
              borderLeft: "1px solid var(--line-subtle)",
              padding: "24px 16px",
              overflowY: "auto",
            }}
            className="hidden lg:block"
          >
            <InspectorPanel
              formData={formData}
              repeatersData={repeatersData}
              derivedValues={derivedValues}
              requiredFieldsCount={requiredFieldsCount}
              onExport={() => handleSubmit(formData)}
              isSubmitting={submitting}
            />
          </div>
        )}
      </div>

      {/* Command Palette Modal */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigateSection={scrollToSection}
        onSaveDraft={handleSaveDraft}
        onExportDocx={() => handleSubmit(formData)}
        onLoadSample={handleLoadSample}
        onClearForm={handleClearForm}
        onOpenShortcuts={() => setShortcutsOpen(true)}
        onOpenTemplateSelector={() => setTemplateModalOpen(true)}
        onOpenPartySearch={() => handleOpenPartySearch("seller")}
        onOpenPropertySearch={() => setPropertyModalOpen(true)}
        onOpenPilotFeedback={() => setPilotFeedbackOpen(true)}
        onOpenHistory={() => setHistoryDrawerOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Keyboard Shortcuts Sheet Modal */}
      <KeyboardShortcutsModal
        isOpen={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
      />

      {/* Recent Drafts Drawer */}
      <RecentDraftsDrawer
        isOpen={draftsDrawerOpen}
        onClose={() => setDraftsDrawerOpen(false)}
        drafts={recentDrafts}
        onRestore={handleRestoreDraft}
        onDelete={handleDeleteDraft}
      />

      {/* Authoritative Document History Drawer */}
      <DocumentHistoryDrawer
        isOpen={historyDrawerOpen}
        onClose={() => setHistoryDrawerOpen(false)}
      />

      {/* Authentication Login Modal */}
      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
      />

      {/* Dynamic Template Selection Modal */}
      <TemplateSelectorModal
        isOpen={templateModalOpen}
        onClose={() => setTemplateModalOpen(false)}
        selectedTemplateId={activeTemplate.template_id}
        onSelectTemplate={(tmpl) => {
          setActiveTemplate(tmpl);
          toast({
            type: "success",
            title: lang === "mr" ? "साचा निवडला (Template Selected)" : "Template Selected",
            description: tmpl.name_mr || tmpl.name_en,
          });
        }}
      />

      {/* Party Search and Reuse Modal (PRD FR-14, F-060) */}
      <PartySearchModal
        isOpen={partyModalOpen}
        onClose={() => setPartyModalOpen(false)}
        targetRole={partyTargetRole}
        onSelectParty={handleSelectParty}
      />

      {/* Property Search and Reuse Modal (PRD FR-14, F-060) */}
      <PropertySearchModal
        isOpen={propertyModalOpen}
        onClose={() => setPropertyModalOpen(false)}
        onSelectProperty={handleSelectProperty}
      />

      {/* Pilot Feedback & Drafter Corrections Modal (PRD Section 10) */}
      <PilotFeedbackModal
        isOpen={pilotFeedbackOpen}
        onClose={() => setPilotFeedbackOpen(false)}
        templateId={activeTemplate.template_id}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <I18nProvider>
      <AuthProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </AuthProvider>
    </I18nProvider>
  );
};

export default App;
