import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useI18n } from "../../shared/i18n";
import { useToast, Button, Badge, Modal } from "../../shared/components";
import { useAuth } from "../../shared/auth/AuthContext";
import {
  api,
  apiClient,
  ApiError,
  JobDetailResponse,
  JobEnqueueResponse,
  ValidationResponse,
} from "../../shared/api";
import { DynamicForm } from "../form_engine/DynamicForm";
import { InspectorPanel } from "../form_engine/InspectorPanel";
import { PartySearchModal } from "../parties/PartySearchModal";
import { PropertySearchModal } from "../properties/PropertySearchModal";
import { TemplateSelectorModal, TemplateCatalogItem } from "../form_engine/TemplateSelectorModal";
import { defaultManifest } from "../form_engine/sampleManifest";
import { BUNDLED_MANIFESTS } from "../templates/bundledManifests";
import { TemplateManifest } from "../form_engine/types";
import {
  buildInitialFormData,
  buildInitialRepeatersData,
  normalizeManifest,
  unflattenFormData,
} from "../form_engine/manifestNormalizer";
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
  AlertCircle,
  Clock,
  RefreshCw,
  Calendar,
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
  "execution_date": new Date().toISOString().split("T")[0],
};

interface DraftingWorkspaceProps {
  onNavigate: (viewId: string) => void;
  activeTemplateId?: string;
  initialDraftData?: Record<string, unknown>;
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
  const [formData, setFormData] = useState<Record<string, unknown>>(() => {
    if (initialDraftData?.formData && typeof initialDraftData.formData === "object") {
      const data = { ...(initialDraftData.formData as Record<string, unknown>) };
      if (!data.execution_date) data.execution_date = new Date().toISOString().split("T")[0];
      return data;
    }
    const saved = localStorage.getItem("lekhan_current_form");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (!parsed.execution_date) parsed.execution_date = new Date().toISOString().split("T")[0];
        return parsed;
      } catch (e) { }
    }
    return buildInitialFormData(defaultManifest);
  });

  const [repeatersData, setRepeatersData] = useState<Record<string, Array<Record<string, unknown>>>>(() => {
    if (initialDraftData?.repeatersData && typeof initialDraftData.repeatersData === "object") {
      return initialDraftData.repeatersData as Record<string, Array<Record<string, unknown>>>;
    }
    const saved = localStorage.getItem("lekhan_current_repeaters");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) { }
    }
    const initRepeaters: Record<string, Array<Record<string, unknown>>> = {};
    Object.entries(defaultManifest.repeaters).forEach(([key, rep]) => {
      const initialCount = Math.max(1, rep.min);
      initRepeaters[key] = Array.from({ length: initialCount }, () => {
        const item: Record<string, unknown> = {};
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
  const [activeDraftId, setActiveDraftId] = useState<string | null>(
    initialDraftData?.id ? String(initialDraftData.id) : null
  );
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  type ProgressStep = "REQUESTED" | "RENDERED" | "VERIFIED" | "DONE";
  const PROGRESS_STEPS: ProgressStep[] = ["REQUESTED", "RENDERED", "VERIFIED", "DONE"];

  interface ProgressState {
    isOpen: boolean;
    jobId: string | null;
    documentId: string | null;
    currentStep: ProgressStep;
    status: "idle" | "running" | "succeeded" | "failed";
    errorCode: string | null;
    errorMessage: string | null;
  }

  const [progressState, setProgressState] = useState<ProgressState>({
    isOpen: false,
    jobId: null,
    documentId: null,
    currentStep: "REQUESTED",
    status: "idle",
    errorCode: null,
    errorMessage: null,
  });

  const pollTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current);
      }
    };
  }, []);

  // Template Modal & Active Manifest
  const [templateModalOpen, setTemplateModalOpen] = useState(false);
  const [activeManifest, setActiveManifest] = useState<TemplateManifest>(defaultManifest);
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

  const loadTemplateManifest = useCallback(async (templateId: string, resetFields: boolean) => {
    let raw: (Partial<TemplateManifest> & { template_id: string }) | null = null;
    try {
      raw = await apiClient<Partial<TemplateManifest> & { template_id: string }>(
        `/api/v1/templates/${encodeURIComponent(templateId)}/manifest`
      );
    } catch {
      // Offline / static hosting fallback: use bundled schema
      if (BUNDLED_MANIFESTS[templateId]) {
        raw = BUNDLED_MANIFESTS[templateId] as Partial<TemplateManifest> & { template_id: string };
      }
    }

    if (raw) {
      const normalized = normalizeManifest(raw);
      setActiveManifest(normalized);
      if (resetFields) {
        setFormData(buildInitialFormData(normalized));
        setRepeatersData(buildInitialRepeatersData(normalized));
        setActiveSectionId(
          normalized.sections[0]?.id || Object.keys(normalized.repeaters)[0] || ""
        );
      }
    } else {
      toast({
        type: "error",
        title: lang === "mr" ? "साचा लोड होऊ शकला नाही" : "Failed to load template schema",
        description: `Template '${templateId}' schema is unavailable offline.`,
      });
    }
  }, [lang, toast]);

  useEffect(() => {
    if (activeTemplateId && activeTemplateId !== defaultManifest.template_id) {
      loadTemplateManifest(activeTemplateId, !initialDraftData);
    }
  }, [activeTemplateId, initialDraftData, loadTemplateManifest]);

  // Modals for Party and Property Search & Reuse
  const [partyModalOpen, setPartyModalOpen] = useState(false);
  const [partyTargetRole, setPartyTargetRole] = useState<"seller" | "purchaser">("seller");
  const [partyTargetIndex, setPartyTargetIndex] = useState<number | undefined>(undefined);
  const [propertyModalOpen, setPropertyModalOpen] = useState(false);

  // Autosave to localStorage (offline cache) and server draft
  useEffect(() => {
    setSaveStatus("saving");
    const timer = setTimeout(async () => {
      localStorage.setItem("lekhan_current_form", JSON.stringify(formData));
      localStorage.setItem("lekhan_current_repeaters", JSON.stringify(repeatersData));

      // Auto-persist to server-side drafts table
      try {
        const hasData = Object.values(formData).some((v) => v !== undefined && v !== "");
        if (hasData) {
          const title = String(formData["property.description"] || formData["property.plot_no"] || `${activeTemplate.name_en} Draft`);
          if (activeDraftId) {
            await api.updateDraft(activeDraftId, {
              title,
              template_id: activeManifest.template_id,
              data: { formData, repeatersData },
            });
          } else {
            const newDraft = await api.createDraft({
              title,
              template_id: activeManifest.template_id,
              data: { formData, repeatersData },
            });
            setActiveDraftId(newDraft.id);
          }
        }
      } catch {
        // Offline mode: localStorage remains primary cache
      }
      setSaveStatus("saved");
    }, 1000);
    return () => clearTimeout(timer);
  }, [formData, repeatersData, activeDraftId, activeManifest.template_id, activeTemplate.name_en]);

  // Derived values calculation
  const derivedValues = useMemo(() => {
    const total = parseFloat(String(formData["financial.total_consideration"] ?? 0));
    const advance = parseFloat(String(formData["financial.earnest_advance"] ?? 0));
    const balance = Math.max(0, total - advance);

    const areaSqm = parseFloat(String(formData["property.area_sqm"] ?? 0));
    const areaSqft = (areaSqm * 10.7639104).toFixed(2);

    return {
      "financial.balance_amount": balance,
      "property.area_sqft": areaSqft,
    };
  }, [formData]);

  // Count required fields
  const requiredFieldsCount = useMemo(() => {
    const requiredKeys = Object.entries(activeManifest.fields)
      .filter(([_, def]) => def.required)
      .map(([k]) => k);
    const filled = requiredKeys.filter((k) => !!formData[k]).length;
    return { filled, total: requiredKeys.length };
  }, [activeManifest, formData]);

  const handleFieldChange = (key: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    if (fieldErrors[key]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const handleRepeatersChange = (key: string, items: Array<Record<string, unknown>>) => {
    setRepeatersData((prev) => ({ ...prev, [key]: items }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      let changed = false;
      Object.keys(next).forEach((errKey) => {
        if (errKey.startsWith(`${key}.`) || errKey === `${key}__count`) {
          delete next[errKey];
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  };

  const handleOpenPartySearch = (targetRole: string, index?: number) => {
    setPartyTargetRole(targetRole === "purchaser" ? "purchaser" : "seller");
    setPartyTargetIndex(index);
    setPartyModalOpen(true);
  };

  const handleSelectParty = (partyData: Record<string, unknown>) => {
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
    setFieldErrors((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((k) => {
        if (k.startsWith(`${repKey}.`)) delete next[k];
      });
      return next;
    });
    toast({
      type: "success",
      title: lang === "mr" ? "पक्षकार भरला (Party Applied)" : "Party Applied",
      description: String(partyData.full_name || "Party applied"),
    });
  };

  const handleSelectProperty = (propertyData: Record<string, unknown>) => {
    setFormData((prev) => ({ ...prev, ...propertyData }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      Object.keys(propertyData).forEach((k) => delete next[k]);
      return next;
    });
    toast({
      type: "success",
      title: lang === "mr" ? "मिळकत लागू केली (Property Applied)" : "Property Applied",
      description: String(propertyData["property.mouza"] || "Property attributes loaded."),
    });
  };

  const handleLoadSample = () => {
  setFormData((prev) => ({ ...prev, ...SAMPLE_NAGPUR_PLOT }));
  setRepeatersData({
    sellers: [
      {
        full_name: "आनंद बळवंत जोशी",
        gender: "male",
        age: "52",
        occupation: "व्यवसाय",
        address: "फ्लॅट क्र. 201, समर्थ संकुल, धरमपेठ, नागपूर",
        pan: "ABCDE1234F",
      },
    ],
    purchasers: [
      {
        full_name: "सुरेश रामराव पाटील",
        gender: "male",
        age: "41",
        occupation: "नोकरी",
        address: "प्लॉट क्र. 45, त्रिमूर्ती नगर, नागपूर",
        pan: "FGHIJ5678K",
      },
    ],
    instalments: [
      {
        amount: "500000",
        mode: "cheque",
        ref_no: "CHQ123456",
        bank_name: "स्टेट बँक ऑफ इंडिया",
        date: "2026-11-09",
      },
    ],
    witnesses: [
      {
        name: "विजय एकनाथ जोशी",
        address: "नागपूर",
      },
      {
        name: "सचिन मनोहर देशमुख",
        address: "नागपूर",
      },
    ],
  });
  setFieldErrors({});
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

const validateRequiredFields = (
  manifest: TemplateManifest,
  formValues: Record<string, unknown>,
  repValues: Record<string, Array<Record<string, unknown>>>
): Record<string, string> => {
  const errors: Record<string, string> = {};

  Object.entries(manifest.fields).forEach(([fKey, fDef]) => {
    if (fDef.required) {
      const val = formValues[fKey];
      if (val === undefined || val === null || String(val).trim() === "") {
        errors[fKey] = lang === "mr" ? "हे क्षेत्र आवश्यक आहे" : "This field is required";
      }
    }
  });

  Object.entries(manifest.repeaters).forEach(([repKey, repDef]) => {
    const items = repValues[repKey] || [];
    if (items.length < repDef.min) {
      errors[`${repKey}__count`] =
        lang === "mr"
          ? `किमान ${repDef.min} नोंद(ा) आवश्यक आहेत`
          : `At least ${repDef.min} entry/entries required`;
    }
    items.forEach((item, idx) => {
      Object.entries(repDef.fields || {}).forEach(([fKey, fDef]) => {
        if (fDef.required) {
          const val = item[fKey];
          if (val === undefined || val === null || String(val).trim() === "") {
            errors[`${repKey}.${idx}.${fKey}`] =
              lang === "mr" ? "हे क्षेत्र आवश्यक आहे" : "This field is required";
          }
        }
      });
    });
  });

    return errors;
  };

  const startPollingJob = (jobId: string, docIdFallback: string | null) => {
    if (pollTimerRef.current) {
      window.clearTimeout(pollTimerRef.current);
    }

    const poll = async () => {
      try {
        const job = await apiClient<JobDetailResponse>(`/api/v1/jobs/${encodeURIComponent(jobId)}`);

        let step: ProgressStep = "REQUESTED";
        if (job.status === "succeeded" || job.state === "COMPLETED") {
          step = "DONE";
        } else if (job.state === "VERIFIED" || job.state === "STORED") {
          step = "VERIFIED";
        } else if (job.state === "RENDERED") {
          step = "RENDERED";
        } else {
          step = "REQUESTED";
        }

        if (job.status === "succeeded") {
          setSubmitting(false);
          setProgressState((prev) => ({
            ...prev,
            currentStep: "DONE",
            status: "succeeded",
            documentId: job.document_id || docIdFallback || prev.documentId,
          }));

          const downloadUrl =
            job.download_url || `/api/v1/documents/${job.document_id || docIdFallback}/download`;
          const a = document.createElement("a");
          a.href = downloadUrl;
          a.download = `${activeManifest.template_id}_${job.document_id || docIdFallback || "draft"}.docx`;
          document.body.appendChild(a);
          a.click();
          a.remove();

          toast({
            type: "success",
            title: lang === "mr" ? "दस्त निर्मिती यशस्वी!" : "Document Generated Successfully",
            description: `ID: ${job.document_id || docIdFallback || jobId}`,
          });
          return;
        }

        if (job.status === "failed" || job.status === "dead") {
          setSubmitting(false);
          const errCode = job.error?.code || "JOB_FAILED";
          const errMsg =
            job.error?.message ||
            (lang === "mr" ? "दस्त निर्मिती अयशस्वी झाली." : "Document generation failed.");
          setProgressState((prev) => ({
            ...prev,
            status: "failed",
            errorCode: errCode,
            errorMessage: errMsg,
          }));
          toast({
            type: "error",
            title: lang === "mr" ? "दस्त निर्मितीमध्ये त्रुटी आली" : "Document Generation Failed",
            description: `[${errCode}] ${errMsg}`,
          });
          return;
        }

        setProgressState((prev) => ({
          ...prev,
          currentStep: step,
        }));

        pollTimerRef.current = window.setTimeout(poll, 1500);
      } catch (err: unknown) {
        setSubmitting(false);
        const errCode = err instanceof ApiError && err.code ? err.code : "POLL_FAILED";
        const errMsg = err instanceof Error ? err.message : "Failed to fetch job status.";
        setProgressState((prev) => ({
          ...prev,
          status: "failed",
          errorCode: errCode,
          errorMessage: errMsg,
        }));
        toast({
          type: "error",
          title: lang === "mr" ? "पडताळणी त्रुटी" : "Polling Failed",
          description: `[${errCode}] ${errMsg}`,
        });
      }
    };

    pollTimerRef.current = window.setTimeout(poll, 1500);
  };

  // Submit and DOCX Generation
  const handleSubmit = async (submitData?: Record<string, unknown>) => {
  const currentSubmitData = submitData || formData;
  setSubmitting(true);

  // 1. Block submit and show field-level errors if required fields are empty
  const errors = validateRequiredFields(activeManifest, currentSubmitData, repeatersData);
  if (Object.keys(errors).length > 0) {
    setFieldErrors(errors);
    setSubmitting(false);
    const errorKeys = Object.keys(errors);
    const missingNames = errorKeys
      .map((k) => {
        const fDef = activeManifest.fields[k];
        return fDef ? (lang === "mr" ? fDef.label_mr : fDef.label_en) || k : k;
      })
      .slice(0, 2)
      .join(", ");
    const remainingCount = errorKeys.length > 2 ? ` (+${errorKeys.length - 2} more)` : "";

    toast({
      type: "error",
      title: lang === "mr" ? "कृपया आवश्यक माहिती भरा" : "Required Fields Missing",
      description:
        lang === "mr"
          ? `${missingNames} भरणे बाकी आहे.${remainingCount}`
          : `Please fill: ${missingNames}${remainingCount}`,
    });
    const firstKey = Object.keys(errors)[0];
    const el = document.getElementById(firstKey) || document.getElementById(`input-${firstKey}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.focus();
    }
    return;
  }

  setFieldErrors({});

  try {
    // 2. Call /documents/validate/{template_id} before submitting
    const preparedValidationData = unflattenFormData(
      Object.fromEntries(
        Object.entries(currentSubmitData).map(([k, v]) => {
          const fDef = activeManifest.fields[k];
          if ((fDef?.type === "decimal" || fDef?.type === "integer") && typeof v === "string" && v.trim() !== "") {
            const num = parseFloat(v);
            return [k, isNaN(num) ? v : num];
          }
          return [k, v];
        })
      )
    );

    const validationRes = await apiClient<ValidationResponse>(
      `/api/v1/documents/validate/${encodeURIComponent(activeManifest.template_id)}`,
      {
        method: "POST",
        headers: csrfToken ? { "X-CSRF-Token": csrfToken } : undefined,
        body: JSON.stringify({ data: preparedValidationData }),
      }
    );

    if (!validationRes.valid || (validationRes.violations && validationRes.violations.length > 0)) {
      const firstViolation = validationRes.violations[0];
      const msg = firstViolation
        ? (lang === "mr" ? firstViolation.message_mr : firstViolation.message_en) ||
        firstViolation.message ||
        firstViolation.message_en ||
        firstViolation.message_mr ||
        "Validation rules failed"
        : "Validation rules failed";
      toast({
        type: "error",
        title: lang === "mr" ? "साचा प्रमाणीकरण त्रुटी" : "Validation Failed",
        description: msg,
      });
      setSubmitting(false);
      return;
    }

    // 3. Construct payload without ANY hardcoded fallbacks
    const mappedSellers = (repeatersData.sellers || []).map((s) => ({
      full_name: String(s.full_name || ""),
      gender: String(s.gender || "male"),
      age: s.age ? parseInt(String(s.age), 10) : 0,
      occupation: String(s.occupation || ""),
      address: String(s.address || ""),
      pan: String(s.pan || ""),
    }));

    const mappedPurchasers = (repeatersData.purchasers || []).map((p) => ({
      full_name: String(p.full_name || ""),
      gender: String(p.gender || "male"),
      age: p.age ? parseInt(String(p.age), 10) : 0,
      occupation: String(p.occupation || ""),
      address: String(p.address || ""),
      pan: String(p.pan || ""),
    }));

    const mappedInstalments = (repeatersData.instalments || []).map((inst) => ({
      amount: inst.amount ? parseFloat(String(inst.amount)) : 0,
      mode: String(inst.mode || "cheque"),
      ref_no: String(inst.ref_no || ""),
      bank_name: String(inst.bank_name || ""),
      date_str: String(inst.date || ""),
    }));

    const witness1 = repeatersData.witnesses?.[0]?.name
      ? `१) श्री. ${repeatersData.witnesses[0].name}${repeatersData.witnesses[0].address ? `, रा. ${repeatersData.witnesses[0].address}` : ""}`
      : "";

    const witness2 = repeatersData.witnesses?.[1]?.name
      ? `२) श्री. ${repeatersData.witnesses[1].name}${repeatersData.witnesses[1].address ? `, रा. ${repeatersData.witnesses[1].address}` : ""}`
      : "";

    const payload =
      activeManifest.template_id === "sale_deed_plot_mr"
        ? {
          template_id: activeManifest.template_id,
          execution_date: currentSubmitData["execution_date"] || formData["execution_date"] || "",
          sellers: mappedSellers,
          purchasers: mappedPurchasers,
          property_details: {
            mouza: currentSubmitData["property.mouza"] || "",
            khasra_no: currentSubmitData["property.khasra_no"] || "",
            plot_no: currentSubmitData["property.plot_no"] || "",
            layout_name: currentSubmitData["property.layout_name"] || "",
            sheet_no: currentSubmitData["property.sheet_no"] || "",
            area_sqm: currentSubmitData["property.area_sqm"] ? parseFloat(String(currentSubmitData["property.area_sqm"])) : 0,
          },
          boundaries: {
            east: currentSubmitData["boundaries.east"] || "",
            west: currentSubmitData["boundaries.west"] || "",
            north: currentSubmitData["boundaries.north"] || "",
            south: currentSubmitData["boundaries.south"] || "",
          },
          financial: {
            total_consideration: currentSubmitData["financial.total_consideration"]
              ? parseFloat(String(currentSubmitData["financial.total_consideration"]))
              : 0,
            earnest_advance: currentSubmitData["financial.earnest_advance"]
              ? parseFloat(String(currentSubmitData["financial.earnest_advance"]))
              : 0,
            instalments: mappedInstalments,
          },
          witness_1: witness1,
          witness_2: witness2,
        }
        : {
          template_id: activeManifest.template_id,
          ...unflattenFormData(currentSubmitData),
          ...repeatersData,
        };

    // 4. POST /documents
    const data = await apiClient<JobEnqueueResponse>("/api/v1/documents", {
      method: "POST",
      headers: csrfToken ? { "X-CSRF-Token": csrfToken } : undefined,
      body: JSON.stringify(payload),
    });

    const jobId = data.job_id || data.job?.id || "";
    const docId = data.document_id || null;

    // 5. Open Progress UI in REQUESTED state
    setProgressState({
      isOpen: true,
      jobId,
      documentId: docId,
      currentStep: "REQUESTED",
      status: "running",
      errorCode: null,
      errorMessage: null,
    });

    // 6. Start polling
    startPollingJob(jobId, docId);
  } catch (err: unknown) {
    setSubmitting(false);
    const errCode = err instanceof ApiError && err.code ? err.code : "SUBMISSION_FAILED";
    const message = err instanceof Error ? err.message : "Please check required fields.";
    setProgressState({
      isOpen: true,
      jobId: null,
      documentId: null,
      currentStep: "REQUESTED",
      status: "failed",
      errorCode: errCode,
      errorMessage: message,
    });
    toast({
      type: "error",
      title: lang === "mr" ? "दस्त निर्मितीमध्ये त्रुटी आली" : "Document Generation Failed",
      description: `[${errCode}] ${message}`,
    });
  }
};

const handleRetry = () => {
  setProgressState((prev) => ({
    ...prev,
    isOpen: false,
    status: "idle",
    errorCode: null,
    errorMessage: null,
  }));
  void handleSubmit(formData);
};

const handleCloseProgressModal = () => {
  if (pollTimerRef.current) {
    window.clearTimeout(pollTimerRef.current);
  }
  setSubmitting(false);
  setProgressState((prev) => ({ ...prev, isOpen: false }));
};

return (
  <div className="lekhan-drafting-shell" style={{ display: "flex", flex: 1, minHeight: 0, height: "calc(100vh - 56px)" }}>
    {/* 1. LEFT FORM SECTIONS NAV */}
    <nav
      className="lekhan-drafting-nav"
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

        {activeManifest.sections.map((sec) => {
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
              {sec.id === "execution_details" && <Calendar size={14} color={isActive ? "var(--brand-600)" : "var(--text-tertiary)"} />}
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {lang === "mr" ? sec.title_mr : sec.title_en}
              </span>
            </button>
          );
        })}

        {Object.entries(activeManifest.repeaters).map(([repKey, repDef]) => {
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
        manifest={activeManifest}
        formData={formData}
        repeatersData={repeatersData}
        onFieldChange={handleFieldChange}
        onRepeatersChange={handleRepeatersChange}
        onOpenPartySearch={handleOpenPartySearch}
        onSubmit={handleSubmit}
        isSubmitting={submitting}
        fieldErrors={fieldErrors}
      />
    </main>

    {/* 3. RIGHT COLLAPSIBLE INSPECTOR PANEL */}
    {inspectorOpen && (
      <aside className="lekhan-drafting-inspector" style={{ width: "320px", flexShrink: 0, borderLeft: "1px solid var(--line-subtle)", overflowY: "auto", backgroundColor: "var(--surface-card)" }}>
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

    {/* 4. Generation Progress & Polling Modal */}
    <Modal
      isOpen={progressState.isOpen}
      onClose={handleCloseProgressModal}
      title={lang === "mr" ? "दस्त निर्मिती प्रगती" : "Document Generation Progress"}
      description={
        progressState.status === "failed"
          ? lang === "mr"
            ? "दस्त निर्मिती प्रक्रियेमध्ये त्रुटी आली."
            : "Generation encountered an error."
          : lang === "mr"
            ? "पार्श्वभूमीमध्ये दस्तऐवज प्रक्रिया आणि पडताळणी सुरू आहे..."
            : "Generating and verifying legal document in the background..."
      }
      footer={
        progressState.status === "failed" ? (
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", width: "100%" }}>
            <Button variant="secondary" onClick={handleCloseProgressModal}>
              {lang === "mr" ? "रद्द करा" : "Close"}
            </Button>
            <Button
              variant="primary"
              data-testid="job-retry-button"
              onClick={handleRetry}
              leftIcon={<RefreshCw size={14} />}
            >
              {lang === "mr" ? "पुन्हा प्रयत्न करा (Retry)" : "Retry"}
            </Button>
          </div>
        ) : progressState.status === "succeeded" ? (
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", width: "100%" }}>
            <Button variant="primary" onClick={handleCloseProgressModal}>
              {lang === "mr" ? "पूर्ण झाले (Done)" : "Done"}
            </Button>
          </div>
        ) : (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
              {lang === "mr" ? "१.५ सेकंदाने तपासणी चालू आहे..." : "Polling every 1.5 s..."}
            </span>
            <Button variant="secondary" size="sm" onClick={handleCloseProgressModal}>
              {lang === "mr" ? "पार्श्वभूमीत ठेवा" : "Run in Background"}
            </Button>
          </div>
        )
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "20px", padding: "8px 0" }}>
        {/* Progress Timeline: REQUESTED -> RENDERED -> VERIFIED -> DONE */}
        <div
          data-testid="generation-progress-timeline"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "14px",
            backgroundColor: "var(--surface-sunken)",
            padding: "16px",
            borderRadius: "var(--radius-card)",
            border: "1px solid var(--line-subtle)",
          }}
        >
          {PROGRESS_STEPS.map((stepKey, idx) => {
            const currentIdx = PROGRESS_STEPS.indexOf(progressState.currentStep);
            const isPast = idx < currentIdx || (progressState.status === "succeeded" && idx <= currentIdx);
            const isCurrent = idx === currentIdx && progressState.status !== "succeeded" && progressState.status !== "failed";
            const isFailedCurrent = idx === currentIdx && progressState.status === "failed";

            const stepLabels: Record<ProgressStep, { en: string; mr: string }> = {
              REQUESTED: { en: "1. Job Enqueued (REQUESTED)", mr: "१. विनंती नोंदवली (REQUESTED)" },
              RENDERED: { en: "2. Template Rendered (RENDERED)", mr: "२. मसुदा भरला (RENDERED)" },
              VERIFIED: { en: "3. Integrity Verified (VERIFIED)", mr: "३. पडताळणी पूर्ण (VERIFIED)" },
              DONE: { en: "4. Document Ready (DONE)", mr: "४. दस्त तयार (DONE)" },
            };

            return (
              <div
                key={stepKey}
                data-testid={`progress-step-${stepKey.toLowerCase()}`}
                data-step-status={isPast ? "completed" : isCurrent ? "active" : isFailedCurrent ? "failed" : "pending"}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  opacity: isPast || isCurrent || isFailedCurrent ? 1 : 0.45,
                  transition: "opacity 0.2s ease",
                }}
              >
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "var(--radius-pill)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: isPast
                      ? "var(--brand-100, #E6F4EA)"
                      : isCurrent
                        ? "var(--brand-500, #00875A)"
                        : isFailedCurrent
                          ? "var(--danger-100, #FEE2E2)"
                          : "var(--surface-card)",
                    border: `1px solid ${isPast
                      ? "var(--brand-600)"
                      : isCurrent
                        ? "var(--brand-600)"
                        : isFailedCurrent
                          ? "var(--danger-600)"
                          : "var(--line-medium)"
                      }`,
                    color: isPast
                      ? "var(--brand-700)"
                      : isCurrent
                        ? "#FFFFFF"
                        : isFailedCurrent
                          ? "var(--danger-700)"
                          : "var(--text-tertiary)",
                    flexShrink: 0,
                  }}
                >
                  {isPast ? (
                    <CheckCircle2 size={16} color="var(--brand-600)" />
                  ) : isCurrent ? (
                    <Clock size={16} color="#FFFFFF" className="animate-spin" />
                  ) : isFailedCurrent ? (
                    <AlertCircle size={16} color="var(--danger-600)" />
                  ) : (
                    <span style={{ fontSize: "0.75rem", fontWeight: 700 }}>{idx + 1}</span>
                  )}
                </div>

                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: "0.875rem",
                      fontWeight: isCurrent || isPast ? 700 : 500,
                      color: isFailedCurrent
                        ? "var(--danger-700)"
                        : isPast || isCurrent
                          ? "var(--brand-900)"
                          : "var(--text-secondary)",
                    }}
                  >
                    {lang === "mr" ? stepLabels[stepKey].mr : stepLabels[stepKey].en}
                  </div>
                </div>

                {isCurrent && (
                  <Badge variant="active" size="sm" label={lang === "mr" ? "प्रक्रिया सुरू" : "In Progress"} />
                )}
                {isPast && (
                  <Badge variant="approved" size="sm" label={lang === "mr" ? "पूर्ण" : "Completed"} />
                )}
                {isFailedCurrent && (
                  <Badge variant="danger" size="sm" label={lang === "mr" ? "त्रुटी" : "Failed"} />
                )}
              </div>
            );
          })}
        </div>

        {/* Failure Alert Banner with Error Code & Description */}
        {progressState.status === "failed" && (
          <div
            data-testid="job-failure-banner"
            style={{
              backgroundColor: "var(--danger-50, #fef2f2)",
              border: "1px solid var(--danger-300, #fca5a5)",
              borderRadius: "var(--radius-card)",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--danger-700, #b91c1c)" }}>
              <AlertCircle size={18} />
              <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>
                {lang === "mr" ? "दस्त निर्मितीमध्ये त्रुटी उद्भवली" : "Document Generation Failed"}
              </span>
            </div>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
              <strong>{lang === "mr" ? "त्रुटी कोड (Error Code):" : "Error Code:"} </strong>
              <code
                data-testid="job-error-code"
                style={{
                  backgroundColor: "var(--danger-100)",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  color: "var(--danger-800)",
                }}
              >
                {progressState.errorCode || "JOB_FAILED"}
              </code>
            </div>
            {progressState.errorMessage && (
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                {progressState.errorMessage}
              </div>
            )}
          </div>
        )}

        {/* Success Banner */}
        {progressState.status === "succeeded" && (
          <div
            data-testid="job-success-banner"
            style={{
              backgroundColor: "var(--surface-sunken)",
              border: "1px solid var(--brand-500)",
              borderRadius: "var(--radius-card)",
              padding: "14px 16px",
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <CheckCircle2 size={20} color="var(--brand-600)" />
            <div style={{ fontSize: "0.8125rem", color: "var(--brand-900)" }}>
              <strong>{lang === "mr" ? "दस्त निर्मिती व डाऊनलोड यशस्वी!" : "DOCX Generated & Downloaded!"}</strong>
              <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                {activeManifest.template_id}.docx
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>

    {/* Modals */}
    <TemplateSelectorModal
      isOpen={templateModalOpen}
      onClose={() => setTemplateModalOpen(false)}
      selectedTemplateId={activeTemplate.template_id}
      onSelectTemplate={(tmpl) => {
        setActiveTemplate(tmpl);
        setTemplateModalOpen(false);
        void loadTemplateManifest(tmpl.template_id, true);
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
