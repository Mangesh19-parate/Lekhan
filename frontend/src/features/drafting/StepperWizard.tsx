import React, { useState, useMemo } from "react";
import { Check, ChevronRight, FileText, Globe, Home, Building2, Store, Trees, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { Button, Card, Badge } from "../../shared/components";
import { useI18n } from "../../shared/i18n";

export interface StepperWizardProps {
  onSelectTemplate: (templateId: string) => void;
  onCancel?: () => void;
}

export const StepperWizard: React.FC<StepperWizardProps> = ({ onSelectTemplate, onCancel }) => {
  const { lang: uiLang } = useI18n();

  // Wizard state: Step 1 (Language) -> Step 2 (Property Type) -> Step 3 (Document Type)
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [selectedLanguage, setSelectedLanguage] = useState<"mr" | "en" | "hi">("mr");
  const [selectedPropertyType, setSelectedPropertyType] = useState<string>("plot");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("sale_deed_plot_mr");

  // Property types catalog
  const propertyTypes = [
    {
      id: "plot",
      icon: <Trees size={20} />,
      titleMr: "भूखंड / लेआउट (Plot / NA Layout)",
      titleEn: "Plot / Non-Agricultural Land",
      descMr: "ना.सु.प्र. / ना.म.पा. मंजूर अभिन्यास भूखंड",
      descEn: "NIT / Municipal Sanctioned Layout Plots",
    },
    {
      id: "flat",
      icon: <Building2 size={20} />,
      titleMr: "निवासी सदनिका (Residential Flat / Apartment)",
      titleEn: "Residential Flat / Apartment",
      descMr: "अपार्टमेंट / गृहनिर्माण संस्था फ्लॅट",
      descEn: "Co-operative Housing Society & RERA Flats",
    },
    {
      id: "shop",
      icon: <Store size={20} />,
      titleMr: "व्यावसायिक दुकान / गाळा (Commercial Shop)",
      titleEn: "Commercial Shop / Office Unit",
      descMr: "शॉप ॲक्ट व व्यावसायिक संकुल गाळे",
      descEn: "Commercial Complex Shops & Retail Units",
    },
    {
      id: "agricultural",
      icon: <Trees size={20} />,
      titleMr: "शेतजमीन (Agricultural Land / शेती)",
      titleEn: "Agricultural Farmland",
      descMr: "७/१२ उतारा, गट क्र. व वहिवाट रस्ता",
      descEn: "Revenue 7/12 Records, Gat No. & Cart Track",
    },
    {
      id: "residential",
      icon: <Home size={20} />,
      titleMr: "स्वतंत्र घर / बंगला (Residential House)",
      titleEn: "Independent Residential House",
      descMr: "इमारत बांधकाम व जमिनीसह मालकी",
      descEn: "Civil Structure & Freehold Land Conveyance",
    },
    {
      id: "general",
      icon: <FileText size={20} />,
      titleMr: "सर्वसाधारण / कुलमुखत्यार (General & Powers)",
      titleEn: "General / Powers of Attorney",
      descMr: "कुलमुखत्यारपत्र, हमीपत्र, समजोता करार",
      descEn: "Powers of Attorney, Guarantees & Agreements",
    },
  ];

  // Document templates catalog mapped to property type and language
  const catalog = [
    // Wave 1 Baseline
    { id: "sale_deed_plot_mr", docType: "sale_deed", propType: "plot", lang: "mr", titleMr: "खरेदीखत (भूखंड)", titleEn: "Sale Deed (Plot)", status: "approved" },
    { id: "agreement_to_sell_plot_mr", docType: "agreement_to_sell", propType: "plot", lang: "mr", titleMr: "साठेखत / इसारपावती (भूखंड)", titleEn: "Agreement to Sell (Plot)", status: "approved" },
    { id: "sale_deed_flat_mr", docType: "sale_deed", propType: "flat", lang: "mr", titleMr: "खरेदीखत (सदनिका / फ्लॅट)", titleEn: "Sale Deed (Flat)", status: "approved" },
    { id: "sale_deed_flat_en", docType: "sale_deed", propType: "flat", lang: "en", titleMr: "विक्री विलेख (सदनिका - इंग्रजी)", titleEn: "Deed of Absolute Sale (Flat)", status: "approved" },
    { id: "agreement_to_sell_flat_mr", docType: "agreement_to_sell", propType: "flat", lang: "mr", titleMr: "सदनिका साठेखत", titleEn: "Agreement to Sell (Flat)", status: "approved" },
    { id: "agreement_to_sell_flat_en", docType: "agreement_to_sell", propType: "flat", lang: "en", titleMr: "सदनिका साठेखत (इंग्रजी)", titleEn: "Agreement to Sell Flat (English)", status: "approved" },
    { id: "sale_deed_shop_mr", docType: "sale_deed", propType: "shop", lang: "mr", titleMr: "दुकान खरेदीखत (Commercial Shop)", titleEn: "Sale Deed (Shop)", status: "approved" },
    { id: "sale_deed_agricultural_mr", docType: "sale_deed", propType: "agricultural", lang: "mr", titleMr: "शेतजमीन खरेदीखत (Agricultural)", titleEn: "Sale Deed (Agricultural)", status: "approved" },
    { id: "general_poa_mr", docType: "general_poa", propType: "general", lang: "mr", titleMr: "कुलमुखत्यारपत्र (General POA)", titleEn: "General Power of Attorney (MR)", status: "approved" },
    { id: "general_poa_en", docType: "general_poa", propType: "general", lang: "en", titleMr: "कुलमुखत्यारपत्र (इंग्रजी)", titleEn: "General Power of Attorney (EN)", status: "approved" },

    // Wave 2 Complete Library
    { id: "gift_deed_mr", docType: "gift_deed", propType: "plot", lang: "mr", titleMr: "दानपत्र (बक्षीसपत्र)", titleEn: "Gift Deed", status: "draft" },
    { id: "gift_deed_en", docType: "gift_deed", propType: "plot", lang: "en", titleMr: "दानपत्र (इंग्रजी)", titleEn: "Gift Deed (English)", status: "draft" },
    { id: "exchange_deed_mr", docType: "exchange_deed", propType: "plot", lang: "mr", titleMr: "अदलाबदल पत्र (Exchange Deed)", titleEn: "Deed of Exchange", status: "draft" },
    { id: "exchange_deed_en", docType: "exchange_deed", propType: "plot", lang: "en", titleMr: "अदलाबदल पत्र (इंग्रजी)", titleEn: "Deed of Exchange (English)", status: "draft" },
    { id: "house_sale_deed_mr", docType: "sale_deed", propType: "residential", lang: "mr", titleMr: "घर / इमारत खरेदीखत", titleEn: "House Sale Deed", status: "draft" },
    { id: "house_sale_deed_en", docType: "sale_deed", propType: "residential", lang: "en", titleMr: "घर खरेदीखत (इंग्रजी)", titleEn: "House Sale Deed (English)", status: "draft" },
    { id: "family_partition_mr", docType: "family_partition", propType: "agricultural", lang: "mr", titleMr: "कौटुंबिक वाटणीपत्र", titleEn: "Family Partition Deed", status: "draft" },
    { id: "family_partition_en", docType: "family_partition", propType: "agricultural", lang: "en", titleMr: "कौटुंबिक वाटणीपत्र (इंग्रजी)", titleEn: "Family Partition Deed (English)", status: "draft" },
    { id: "will_mr", docType: "will", propType: "residential", lang: "mr", titleMr: "मृत्युपत्र / इच्छापत्र (Will)", titleEn: "Last Will & Testament", status: "draft" },
    { id: "will_en", docType: "will", propType: "residential", lang: "en", titleMr: "मृत्युपत्र (इंग्रजी)", titleEn: "Last Will & Testament (English)", status: "draft" },
    { id: "leave_and_licence_mr", docType: "leave_and_licence", propType: "residential", lang: "mr", titleMr: "लिव्ह अँड लायसन्स करार", titleEn: "Leave & Licence Agreement", status: "draft" },
    { id: "leave_and_licence_en", docType: "leave_and_licence", propType: "residential", lang: "en", titleMr: "लिव्ह अँड लायसन्स (इंग्रजी)", titleEn: "Leave & Licence Agreement (English)", status: "draft" },
    { id: "rent_residential_mr", docType: "rent_residential", propType: "residential", lang: "mr", titleMr: "निवासी भाडेकरारनामा", titleEn: "Residential Tenancy Agreement", status: "draft" },
    { id: "rent_residential_en", docType: "rent_residential", propType: "residential", lang: "en", titleMr: "निवासी भाडेकरार (इंग्रजी)", titleEn: "Residential Tenancy Agreement (English)", status: "draft" },
    { id: "rent_shop_mr", docType: "rent_shop", propType: "shop", lang: "mr", titleMr: "दुकान भाडेकरारनामा", titleEn: "Shop Rent Agreement", status: "draft" },
    { id: "rent_shop_en", docType: "rent_shop", propType: "shop", lang: "en", titleMr: "दुकान भाडेकरार (इंग्रजी)", titleEn: "Shop Rent Agreement (English)", status: "draft" },
    { id: "mortgage_deed_mr", docType: "mortgage_deed", propType: "plot", lang: "mr", titleMr: "गहाणखत (Deed of Mortgage)", titleEn: "Deed of Mortgage", status: "draft" },
    { id: "mortgage_deed_en", docType: "mortgage_deed", propType: "plot", lang: "en", titleMr: "गहाणखत (इंग्रजी)", titleEn: "Deed of Mortgage (English)", status: "draft" },
    { id: "special_poa_mr", docType: "special_poa", propType: "general", lang: "mr", titleMr: "विशेष कुलमुखत्यारपत्र (Special POA)", titleEn: "Special Power of Attorney", status: "draft" },
    { id: "special_poa_en", docType: "special_poa", propType: "general", lang: "en", titleMr: "विशेष कुलमुखत्यार (इंग्रजी)", titleEn: "Special Power of Attorney (English)", status: "draft" },
    { id: "irrevocable_poa_mr", docType: "special_poa", propType: "plot", lang: "mr", titleMr: "अपरिवर्तनीय कुलमुखत्यारपत्र", titleEn: "Irrevocable Power of Attorney", status: "draft" },
    { id: "irrevocable_poa_en", docType: "special_poa", propType: "plot", lang: "en", titleMr: "अपरिवर्तनीय कुलमुखत्यार (इंग्रजी)", titleEn: "Irrevocable Power of Attorney (English)", status: "draft" },
  ];

  // Filter templates matching Step 1 (language) and Step 2 (property type)
  const filteredTemplates = useMemo(() => {
    return catalog.filter((t) => t.lang === selectedLanguage && t.propType === selectedPropertyType);
  }, [catalog, selectedLanguage, selectedPropertyType]);

  // Set default template when filtered list changes
  React.useEffect(() => {
    if (filteredTemplates.length > 0) {
      if (!filteredTemplates.some((t) => t.id === selectedTemplateId)) {
        setSelectedTemplateId(filteredTemplates[0].id);
      }
    }
  }, [filteredTemplates, selectedTemplateId]);

  const activeTemplate = catalog.find((t) => t.id === selectedTemplateId) || catalog[0];

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto p-4 md:p-6 font-ui">
      {/* Step Indicator Header */}
      <div className="bg-card border border-line-subtle rounded-card p-4 shadow-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Step 1 */}
            <button
              type="button"
              onClick={() => setStep(1)}
              className={`flex items-center gap-2 text-xs md:text-sm font-semibold transition-colors ${
                step === 1 ? "text-brand-600 dark:text-brand-400" : "text-text-secondary"
              }`}
            >
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  step === 1 ? "bg-brand-500 text-white" : "bg-sunken text-text-primary"
                }`}
              >
                1
              </span>
              <span>1. Language / भाषा</span>
            </button>

            <ChevronRight size={16} className="text-text-tertiary" />

            {/* Step 2 */}
            <button
              type="button"
              onClick={() => setStep(2)}
              className={`flex items-center gap-2 text-xs md:text-sm font-semibold transition-colors ${
                step === 2 ? "text-brand-600 dark:text-brand-400" : "text-text-secondary"
              }`}
            >
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  step === 2 ? "bg-brand-500 text-white" : "bg-sunken text-text-primary"
                }`}
              >
                2
              </span>
              <span>2. Property / मिळकत</span>
            </button>

            <ChevronRight size={16} className="text-text-tertiary" />

            {/* Step 3 */}
            <button
              type="button"
              onClick={() => setStep(3)}
              className={`flex items-center gap-2 text-xs md:text-sm font-semibold transition-colors ${
                step === 3 ? "text-brand-600 dark:text-brand-400" : "text-text-secondary"
              }`}
            >
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  step === 3 ? "bg-brand-500 text-white" : "bg-sunken text-text-primary"
                }`}
              >
                3
              </span>
              <span>3. Document / दस्तऐवज</span>
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-2">
            {onCancel && (
              <Button variant="ghost" size="sm" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={() => onSelectTemplate(selectedTemplateId)}
              rightIcon={<ArrowRight size={14} />}
            >
              Start Drafting
            </Button>
          </div>
        </div>
      </div>

      {/* Main Two-Column Layout: Left Stepper Selection + Right Live Document Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Current Step Selectors (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* STEP 1: Language */}
          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div className="border-b border-line-subtle pb-3">
                <h2 className="text-base font-bold text-text-primary">
                  Step 1: Select Drafting Language (दस्तऐवजाची भाषा निवडा)
                </h2>
                <p className="text-xs text-text-secondary mt-1">
                  Choose the official legal execution language for the deed.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Marathi Option */}
                <div
                  onClick={() => {
                    setSelectedLanguage("mr");
                    setStep(2);
                  }}
                  className={`p-5 rounded-card border-2 cursor-pointer transition-all ${
                    selectedLanguage === "mr"
                      ? "border-brand-500 bg-brand-50/40 dark:bg-brand-900/20 shadow-md"
                      : "border-line-subtle bg-card hover:border-line-medium"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-lg text-text-primary">मराठी (Marathi)</span>
                    {selectedLanguage === "mr" && (
                      <span className="w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center">
                        <Check size={13} />
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-secondary">
                    महाराष्ट्र नोंदणी नियमांनुसार प्राधिकृत मराठी कायदेशीर मसुदा व पारिभाषिक संज्ञा.
                  </p>
                  <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-brand-600 dark:text-brand-400">
                    <span>Noto Sans Devanagari • NFC Normalised</span>
                  </div>
                </div>

                {/* English Option */}
                <div
                  onClick={() => {
                    setSelectedLanguage("en");
                    setStep(2);
                  }}
                  className={`p-5 rounded-card border-2 cursor-pointer transition-all ${
                    selectedLanguage === "en"
                      ? "border-brand-500 bg-brand-50/40 dark:bg-brand-900/20 shadow-md"
                      : "border-line-subtle bg-card hover:border-line-medium"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-lg text-text-primary">English (इंग्रजी)</span>
                    {selectedLanguage === "en" && (
                      <span className="w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center">
                        <Check size={13} />
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-secondary">
                    Standard statutory Indian legal deed formatting under Transfer of Property Act 1882.
                  </p>
                  <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-brand-600 dark:text-brand-400">
                    <span>Indian Numbering in Words • Legal Size</span>
                  </div>
                </div>

                {/* Hindi Option */}
                <div
                  onClick={() => {
                    setSelectedLanguage("hi");
                    setStep(2);
                  }}
                  className={`p-5 rounded-card border-2 cursor-pointer transition-all ${
                    selectedLanguage === "hi"
                      ? "border-brand-500 bg-brand-50/40 dark:bg-brand-900/20 shadow-md"
                      : "border-line-subtle bg-card hover:border-line-medium"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-lg text-text-primary">हिन्दी (Hindi)</span>
                    {selectedLanguage === "hi" && (
                      <span className="w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center">
                        <Check size={13} />
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-secondary">
                    संपत्ति अंतरण अधिनियम 1882 व भारतीय पंजीकरण नियमों के अंतर्गत प्राधिकृत विधिक प्रारूप।
                  </p>
                  <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-brand-600 dark:text-brand-400">
                    <span>देवनागरी अंक एवं शब्द • Legal Size</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <Button variant="primary" size="md" onClick={() => setStep(2)}>
                  Continue to Property Type →
                </Button>
              </div>
            </div>
          )}

          {/* STEP 2: Property Type */}
          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div className="border-b border-line-subtle pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-text-primary">
                    Step 2: Property Category (मिळकतीचा प्रकार)
                  </h2>
                  <p className="text-xs text-text-secondary mt-1">
                    Select the classification of the subject property.
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setStep(1)}>
                  ← Back to Language
                </Button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {propertyTypes.map((pt) => {
                  const isSelected = selectedPropertyType === pt.id;
                  return (
                    <div
                      key={pt.id}
                      onClick={() => {
                        setSelectedPropertyType(pt.id);
                        setStep(3);
                      }}
                      className={`p-4 rounded-card border-2 cursor-pointer transition-all ${
                        isSelected
                          ? "border-brand-500 bg-brand-50/40 dark:bg-brand-900/20 shadow-md"
                          : "border-line-subtle bg-card hover:border-line-medium"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400">
                          {pt.icon}
                          <span className="font-semibold text-sm text-text-primary">
                            {selectedLanguage === "mr" ? pt.titleMr : pt.titleEn}
                          </span>
                        </div>
                        {isSelected && (
                          <span className="w-4 h-4 rounded-full bg-brand-500 text-white flex items-center justify-center">
                            <Check size={11} />
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-text-secondary">
                        {selectedLanguage === "mr" ? pt.descMr : pt.descEn}
                      </p>
                    </div>
                  );
                })}
              </div>

              <div className="flex justify-between pt-2">
                <Button variant="secondary" size="md" onClick={() => setStep(1)}>
                  ← Back
                </Button>
                <Button variant="primary" size="md" onClick={() => setStep(3)}>
                  Continue to Document Type →
                </Button>
              </div>
            </div>
          )}

          {/* STEP 3: Document Type */}
          {step === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div className="border-b border-line-subtle pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-text-primary">
                    Step 3: Document Type (दस्तऐवज प्रकार निवडा)
                  </h2>
                  <p className="text-xs text-text-secondary mt-1">
                    Available approved and draft templates for {selectedLanguage.toUpperCase()} & {selectedPropertyType.toUpperCase()}.
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setStep(2)}>
                  ← Back to Property
                </Button>
              </div>

              <div className="space-y-2.5">
                {filteredTemplates.length === 0 ? (
                  <div className="p-8 text-center bg-subtle rounded-card border border-line-subtle text-text-secondary">
                    No template registered for this specific combination. Showing all {selectedLanguage.toUpperCase()} templates:
                  </div>
                ) : (
                  filteredTemplates.map((tmpl) => {
                    const isSelected = selectedTemplateId === tmpl.id;
                    return (
                      <div
                        key={tmpl.id}
                        onClick={() => setSelectedTemplateId(tmpl.id)}
                        className={`p-4 rounded-card border-2 cursor-pointer transition-all flex items-center justify-between ${
                          isSelected
                            ? "border-brand-500 bg-brand-50/50 dark:bg-brand-900/30 shadow-md"
                            : "border-line-subtle bg-card hover:border-line-medium"
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <FileText size={16} className="text-brand-600 dark:text-brand-400" />
                            <span className="font-bold text-sm text-text-primary">
                              {selectedLanguage === "mr" ? tmpl.titleMr : tmpl.titleEn}
                            </span>
                          </div>
                          <div className="text-xs text-text-secondary flex items-center gap-3">
                            <span className="font-mono text-[11px]">{tmpl.id}</span>
                            <span>•</span>
                            <span className="uppercase tracking-wider">{tmpl.propType}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Badge
                            variant={tmpl.status === "approved" ? "approved" : "draft"}
                            label={tmpl.status === "approved" ? "Approved Baseline" : "Draft (मसुदा)"}
                            size="sm"
                          />
                          {isSelected && (
                            <span className="w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center">
                              <Check size={13} />
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="flex justify-between pt-3">
                <Button variant="secondary" size="md" onClick={() => setStep(2)}>
                  ← Back
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => onSelectTemplate(selectedTemplateId)}
                  rightIcon={<ArrowRight size={14} />}
                >
                  Start Drafting This Deed
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Document Preview Pane (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2 text-text-primary font-semibold text-xs">
              <Sparkles size={14} className="text-brand-600 dark:text-brand-400" />
              <span>Live Document Preview (थेट दस्त पूर्वावलोकन)</span>
            </div>
            <span className="text-[11px] font-mono text-text-tertiary">Legal 8.5x14"</span>
          </div>

          {/* White Paper Sheet on Canvas */}
          <div className="bg-canvas border border-line-medium rounded-card p-4 shadow-sm overflow-hidden">
            <div className="bg-card border border-line-subtle rounded-input p-6 shadow-sm min-h-[480px] text-xs font-ui text-text-primary space-y-4">
              {/* Document Centered Title */}
              <div className="text-center border-b border-line-subtle pb-4 space-y-1">
                <h1 className="font-bold text-sm tracking-wide text-brand-600 dark:text-brand-400">
                  {selectedLanguage === "mr"
                    ? `॥ ${activeTemplate.titleMr} ॥`
                    : `DEED OF ${activeTemplate.titleEn.toUpperCase()}`}
                </h1>
                <p className="text-[11px] text-text-secondary">
                  दस्त नोंदणी दिनांक: २०२६-११-१७, नागपूर (नोंदणी पूर्व मसुदा)
                </p>
              </div>

              {/* Statutory Disclaimer Strip */}
              <div className="bg-sunken dark:bg-sunken/40 p-2.5 rounded text-[11px] text-text-secondary italic leading-relaxed text-center border border-line-subtle">
                {selectedLanguage === "mr"
                  ? "[सूचना: हा संगणक-व्युत्पन्न मसुदा असून केवळ सुलभ संपादन व संदर्भासाठी आहे. अंतिम नोंदणीपूर्वी संबंधित वकिलांकडून तपासणी आवश्यक आहे.]"
                  : "[NOTICE: This is a computer-generated draft provided solely for reference and editing. Verification by an advocate is required prior to final registration.]"}
              </div>

              {/* Parties Section */}
              <div className="space-y-1.5 pt-2">
                <div className="font-bold text-text-primary">
                  {selectedLanguage === "mr" ? "॥ पक्षकार परिचय ॥" : "PARTIES TO THE INSTRUMENT:"}
                </div>
                <div className="p-2 bg-subtle dark:bg-sunken/20 rounded border border-line-subtle leading-relaxed">
                  {selectedLanguage === "mr" ? (
                    <>
                      <strong>१. प्रथम पक्षकार (देणारे):</strong> आनंदराव बापूजी देशमुख, वय ५२ वर्षे, रा. वाडी, नागपूर.<br />
                      <strong>२. द्वितीय पक्षकार (घेणारे):</strong> ज्ञानेश्वर विठ्ठलराव कुलकर्णी, वय ४५ वर्षे, रा. धरमपेठ, नागपूर.
                    </>
                  ) : (
                    <>
                      <strong>1. Party of First Part:</strong> Mr. Anandrao Bapuji Deshmukh, Aged 52, Nagpur.<br />
                      <strong>2. Party of Second Part:</strong> Mr. Dnyaneshwar Vitthalrao Kulkarni, Aged 45, Nagpur.
                    </>
                  )}
                </div>
              </div>

              {/* Property Schedule */}
              <div className="space-y-1.5">
                <div className="font-bold text-text-primary">
                  {selectedLanguage === "mr" ? "॥ मिळकतीचे परिशिष्ट ॥" : "SCHEDULE OF PROPERTY:"}
                </div>
                <div className="p-2 bg-subtle dark:bg-sunken/20 rounded border border-line-subtle leading-relaxed">
                  {selectedLanguage === "mr"
                    ? `सर्व ती स्थावर मिळकत मौजे सोनेगाव, खसरा क्र. ४५/२, क्षेत्रफळ १५०.०० चौ.मी., नागपूर.`
                    : `All that piece and parcel of immoveable property situated at Mouza Sonegaon, Khasra No. 45/2, Area 150.00 Sq. Metres, Nagpur.`}
                </div>
              </div>

              {/* Covenants & Terms */}
              <div className="space-y-1.5">
                <div className="font-bold text-text-primary">
                  {selectedLanguage === "mr" ? "॥ प्रमुख नियम व कायदेशीर अटी ॥" : "TERMS & STATUTORY COVENANTS:"}
                </div>
                <ul className="list-disc pl-4 space-y-1 text-text-secondary text-[11px]">
                  <li>
                    {selectedLanguage === "mr"
                      ? "सदर मिळकत सर्व प्रकारच्या बोजा, गहाण व वादामधून पूर्णपणे मुक्त असल्याबाबत विक्रेत्यांची हमी."
                      : "The transferor warrants clear and marketable title free from all liens and encumbrances."}
                  </li>
                  <li>
                    {selectedLanguage === "mr"
                      ? "प्रत्यक्ष, रिक्त व शांततामय ताबा आज रोजी हस्तांतरित करण्यात आला आहे."
                      : "Vacant and peaceful physical possession delivered upon execution."}
                  </li>
                </ul>
              </div>

              {/* Footer Master Note */}
              <div className="pt-4 border-t border-line-subtle text-center text-[10px] text-text-tertiary">
                Preview. The downloaded DOCX is the master. Page 1 of 1.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
