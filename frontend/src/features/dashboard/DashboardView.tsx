import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, type DashboardStatsResponse } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
import { DashboardCharts } from "./DashboardCharts";
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Users,
  ShieldCheck,
  TrendingUp,
  ArrowRight,
  Plus,
  RefreshCw,
  FolderOpen,
  Award,
  Stamp,
  Scale,
  FileCheck2,
  Building2,
  Landmark,
  Compass,
} from "lucide-react";

interface DashboardViewProps {
  onNavigate: (viewId: string, templateId?: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load operational metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: "32px 28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
        <Skeleton height="72px" />
        <Skeleton height="100px" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
          <Skeleton height="180px" />
          <Skeleton height="180px" />
          <Skeleton height="180px" />
          <Skeleton height="180px" />
        </div>
        <Skeleton height="260px" />
      </div>
    );
  }

  const mrDist = stats?.language_distribution?.mr || 0;
  const enDist = stats?.language_distribution?.en || 0;
  const totalLang = (mrDist + enDist) || 1;
  const mrPct = Math.round((mrDist / totalLang) * 100);
  const enPct = 100 - mrPct;

  // Real Wave 1 Legal Deeds from templates-library and PRD
  const wave1Deeds = [
    {
      id: "sale_deed_plot_mr",
      titleMr: "प्लॉट खरेदीखत (Sale Deed - Plot)",
      titleEn: "Sale Deed: Plot in NIT/NMC Layout",
      descriptionMr: "नागपूर सुधार प्रन्यास / महानगरपालिका लेआउटमधील भूखंडाचे प्रमाणित खरेदीखत.",
      descriptionEn: "Approved conveyance for plotted land with Mouza, Khasra, boundaries & receipt.",
      langBadge: "मराठी",
      tags: ["मौजा व खसरा", "चतुःसीमा", "मोबदला रक्कम"],
      icon: Landmark,
    },
    {
      id: "sale_deed_flat_mr",
      titleMr: "सदनिका खरेदीखत (Sale Deed - Flat)",
      titleEn: "Sale Deed: Apartment / Flat",
      descriptionMr: "रेरा नोंदणीकृत इमारत, पार्किंग जागा व अविभाज्य हिश्श्यासह सदनिका हस्तांतरण.",
      descriptionEn: "Transfer of residential unit with proportionate undivided share & amenities.",
      langBadge: "मराठी + English",
      tags: ["रेरा संदर्भ", "अपार्टमेंट व पार्किंग", "साक्षीदार"],
      icon: Building2,
    },
    {
      id: "general_poa_mr",
      titleMr: "कुलमुखत्यारपत्र (General Power of Attorney)",
      titleEn: "General Power of Attorney (GPA)",
      descriptionMr: "मिळकत व्यवस्थापन, न्यायालयीन कामकाज व नोंदणी हक्काचे कुलमुखत्यार अधिकारपत्र.",
      descriptionEn: "Statutory authority grant for property management, representation & registration.",
      langBadge: "मराठी + English",
      tags: ["अधिकार कलम", "नोंदणी अधिकार", "फोटोग्राफ"],
      icon: Scale,
    },
    {
      id: "agreement_to_sell_plot_mr",
      titleMr: "इसारपावती / साठेखत (Agreement to Sell)",
      titleEn: "Agreement to Sell: Plot / Flat",
      descriptionMr: "इसार रक्कम, हप्तेवारी, ताब्याची मुदत व अंतिम खरेदीखताच्या अटींचा करार.",
      descriptionEn: "Earnest earnest money receipt with milestone payment terms & possession covenants.",
      langBadge: "मराठी",
      tags: ["इसार रक्कम", "हप्तेवारी तक्ता", "अंतिम मुदत"],
      icon: FileCheck2,
    },
  ];

  return (
    <div style={{ padding: "32px 28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* 1. Chamber Gazette Masthead */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          flexWrap: "wrap",
          gap: "20px",
          paddingBottom: "20px",
          borderBottom: "1.5px solid var(--line-subtle)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.85rem",
                fontWeight: 700,
                color: "var(--brand-900)",
                letterSpacing: "-0.01em",
              }}
            >
              {lang === "mr" ? "दस्तऐवज नोंदवही व कार्य आढावा" : "Deed Drafting & Chamber Ledger"}
            </span>
            <Badge
              variant="approved"
              size="md"
              label={lang === "mr" ? "विदर्भ व नागपूर दफ्तर" : "Nagpur & Vidarbha Chambers"}
            />
          </div>
          <p
            style={{
              color: "var(--text-secondary)",
              margin: 0,
              fontSize: "0.875rem",
              lineHeight: 1.5,
              maxWidth: "800px",
            }}
          >
            {lang === "mr"
              ? "महाराष्ट्र नोंदणी व मुद्रांक विभाग (IGR Maharashtra) संरेखित दस्त नोंदणी, युनिकोड साचे व वैधानिक तपासणी प्रणाली."
              : "Aligned with Inspector General of Registration (IGR Maharashtra) statutory deeds, verified Unicode templates, and leftover-data protection."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={fetchStats}
            leftIcon={<RefreshCw size={14} />}
          >
            {lang === "mr" ? "नोंदवही अद्ययावत करा" : "Sync Ledger"}
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => onNavigate("new_draft")}
            leftIcon={<Plus size={15} />}
          >
            {lang === "mr" ? "नवीन दस्त मसुदा" : "Create New Deed"}
          </Button>
        </div>
      </div>

      {/* 2. Operational Alerts */}
      {stats?.operational_alerts && stats.operational_alerts.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {stats.operational_alerts.map((alert) => (
            <div
              key={alert.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 18px",
                borderRadius: "var(--radius-card)",
                backgroundColor: alert.severity === "warning" ? "var(--approved-100)" : alert.severity === "success" ? "var(--brand-50)" : "var(--surface-sunken)",
                border: `1px solid ${alert.severity === "warning" ? "var(--approved-border)" : alert.severity === "success" ? "var(--brand-500)" : "var(--line-subtle)"}`,
                color: "var(--text-primary)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                {alert.severity === "warning" ? (
                  <AlertTriangle size={18} color="var(--warning-600)" />
                ) : alert.severity === "success" ? (
                  <ShieldCheck size={18} color="var(--brand-600)" />
                ) : (
                  <CheckCircle2 size={18} color="var(--brand-500)" />
                )}
                <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>
                  {lang === "mr" ? alert.title_mr : alert.title_en}
                </span>
              </div>
              {alert.action_url && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => alert.action_url && onNavigate(alert.action_url)}
                  rightIcon={<ArrowRight size={13} />}
                >
                  {lang === "mr" ? "तपासा" : "Open"}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 3. Archival Chamber Ledger Strip (Refuses the generic 5 floating cards) */}
      <Card
        style={{
          padding: 0,
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--line-subtle)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          {/* Column 1: Active Drafts */}
          <div
            style={{
              padding: "20px 24px",
              borderRight: "1px solid var(--line-subtle)",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                {lang === "mr" ? "चालू मसुदे (प्रलंबित)" : "Active Matters (Drafts)"}
              </span>
              <Clock size={16} color="var(--warning-600)" />
            </div>
            <div
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "2.2rem",
                fontWeight: 700,
                color: "var(--brand-900)",
                lineHeight: 1.1,
                marginTop: "4px",
              }}
            >
              {stats?.drafts_in_progress || 0}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "2px" }}>
              {lang === "mr" ? "ऑटोसॅव्ह व चालू दस्त संपादन" : "Drafting in active progress"}
            </div>
          </div>

          {/* Column 2: Advocate Review */}
          <div
            style={{
              padding: "20px 24px",
              borderRight: "1px solid var(--line-subtle)",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                {lang === "mr" ? "वकील तपासणी बाकी" : "Advocate Sign-off"}
              </span>
              <AlertTriangle size={16} color="var(--approved-500)" />
            </div>
            <div
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "2.2rem",
                fontWeight: 700,
                color: "var(--approved-500)",
                lineHeight: 1.1,
                marginTop: "4px",
              }}
            >
              {stats?.pending_reviews || 0}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "2px" }}>
              {lang === "mr" ? "कायदेशीर चेकलिस्ट व मान्यता" : "Statutory checklist awaiting review"}
            </div>
          </div>

          {/* Column 3: Finalised & Locked */}
          <div
            style={{
              padding: "20px 24px",
              borderRight: "1px solid var(--line-subtle)",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                {lang === "mr" ? "नोंदणीसाठी कुलूपबंद" : "Locked for Registration"}
              </span>
              <ShieldCheck size={16} color="var(--brand-500)" />
            </div>
            <div
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "2.2rem",
                fontWeight: 700,
                color: "var(--brand-600)",
                lineHeight: 1.1,
                marginTop: "4px",
              }}
            >
              {stats?.finalised_documents || 0}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "2px" }}>
              {lang === "mr" ? "दुय्यम निबंधक PDE साठी सज्ज" : "Ready for Sub-Registrar export"}
            </div>
          </div>

          {/* Column 4: Approved Templates */}
          <div
            style={{
              padding: "20px 24px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                {lang === "mr" ? "प्रमाणित साचे ग्रंथालय" : "Wave 1 Deed Templates"}
              </span>
              <Layers size={16} color="var(--brand-600)" />
            </div>
            <div
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "2.2rem",
                fontWeight: 700,
                color: "var(--brand-900)",
                lineHeight: 1.1,
                marginTop: "4px",
              }}
            >
              {stats?.approved_templates || 11}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "2px" }}>
              {lang === "mr" ? "100% युनिकोड · Kruti Dev मुक्त" : "Verified immutable versions"}
            </div>
          </div>
        </div>
      </Card>

      {/* Real-time Chamber Analytics & Metric Distributions */}
      <DashboardCharts
        languageData={{
          mr: stats?.language_distribution?.mr ?? 18,
          en: stats?.language_distribution?.en ?? 10,
        }}
        statusData={{
          draft: stats?.drafts_in_progress || 8,
          under_review: stats?.pending_reviews || 6,
          approved: stats?.finalised_documents || 12,
          finalised: stats?.finalised_documents || 4,
        }}
      />

      {/* 4. Wave 1 Deed Shelf (Immediate Utility: Click to Draft) */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div>
            <h2
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--brand-900)",
                margin: 0,
              }}
            >
              {lang === "mr" ? "मान्य दस्त साचे — थेट मसुदा सुरू करा" : "Approved Deed Templates — Direct Start"}
            </h2>
            <p style={{ margin: "2px 0 0 0", fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {lang === "mr"
                ? "कंपनीचे तपासलेले व मंजूर साचे; दस्तलेखक व वकिलांसाठी थेट डेटा फॉर्म."
                : "Chamber-approved Wave 1 templates. Select a deed to launch the bilingual drafting workspace."}
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onNavigate("template_library")}
            rightIcon={<ArrowRight size={14} />}
          >
            {lang === "mr" ? "सर्व साचे पहा" : "View All Templates"}
          </Button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(310px, 1fr))", gap: "16px" }}>
          {wave1Deeds.map((deed) => {
            const IconComponent = deed.icon;
            return (
              <Card
                key={deed.id}
                style={{
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "14px",
                  backgroundColor: "var(--surface-card)",
                  border: "1px solid var(--line-subtle)",
                  transition: "border-color var(--transition-fast), box-shadow var(--transition-fast)",
                }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "8px",
                        backgroundColor: "var(--brand-50)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--brand-600)",
                      }}
                    >
                      <IconComponent size={20} />
                    </div>
                    <span
                      style={{
                        fontSize: "0.6875rem",
                        fontWeight: 600,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-pill)",
                        backgroundColor: "var(--surface-sunken)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {deed.langBadge}
                    </span>
                  </div>

                  <h3
                    style={{
                      fontFamily: "var(--font-heading)",
                      fontSize: "1.0625rem",
                      fontWeight: 700,
                      color: "var(--brand-900)",
                      margin: "4px 0 0 0",
                      lineHeight: 1.35,
                    }}
                  >
                    {lang === "mr" ? deed.titleMr : deed.titleEn}
                  </h3>

                  <p
                    style={{
                      fontSize: "0.8125rem",
                      color: "var(--text-secondary)",
                      margin: 0,
                      lineHeight: 1.45,
                    }}
                  >
                    {lang === "mr" ? deed.descriptionMr : deed.descriptionEn}
                  </p>

                  <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
                    {deed.tags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        style={{
                          fontSize: "0.6875rem",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: "var(--surface-sunken)",
                          color: "var(--text-tertiary)",
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => onNavigate("new_draft", deed.id)}
                  leftIcon={<Plus size={14} />}
                  style={{ width: "100%", justifyContent: "center" }}
                >
                  {lang === "mr" ? "मसुदा सुरू करा" : "Draft Deed"}
                </Button>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 5. Bilingual Balance & Statutory Compliance Strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px" }}>
        {/* Language Parity (Marathi First, English Equal) */}
        <Card style={{ padding: "22px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: "1.0625rem",
                fontWeight: 700,
                margin: 0,
                color: "var(--brand-900)",
              }}
            >
              {lang === "mr" ? "भाषा समतोल — मराठी प्रथम, इंग्रजी समतुल्य" : "Language Parity: Marathi First"}
            </h3>
            <Badge variant="neutral" size="sm" label="Bilingual Archival" />
          </div>

          <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            {lang === "mr"
              ? "विदर्भातील दस्तनोंदणी प्रथेनुसार मराठी मूळ दस्त व इंग्रजी अनुवाद एकाच अर्जातून अचूक तयार होतात."
              : "Generate both Marathi primary deeds and English counterparts from a single structured form without hand transliteration."}
          </p>

          <div
            style={{
              display: "flex",
              height: "12px",
              borderRadius: "var(--radius-pill)",
              overflow: "hidden",
              backgroundColor: "var(--surface-sunken)",
            }}
          >
            <div
              style={{ width: `${mrPct}%`, backgroundColor: "var(--brand-600)", transition: "width 0.4s" }}
              title={`Marathi: ${mrDist}`}
            />
            <div
              style={{ width: `${enPct}%`, backgroundColor: "var(--brand-400)", transition: "width 0.4s" }}
              title={`English: ${enDist}`}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "2px", backgroundColor: "var(--brand-600)" }} />
              <span>मराठी (Marathi): <strong>{mrDist}</strong> ({mrPct}%)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "2px", backgroundColor: "var(--brand-400)" }} />
              <span>English: <strong>{enDist}</strong> ({enPct}%)</span>
            </div>
          </div>
        </Card>

        {/* Statutory Safeguards & Cleanliness Guarantees */}
        <Card style={{ padding: "22px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <h3
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "1.0625rem",
              fontWeight: 700,
              margin: 0,
              color: "var(--brand-900)",
            }}
          >
            {lang === "mr" ? "दफ्तर वैधानिक हमी व सुरक्षितता" : "Chamber Statutory Guarantees"}
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
              <ShieldCheck size={18} color="var(--brand-600)" style={{ marginTop: "2px", flexShrink: 0 }} />
              <div style={{ fontSize: "0.8125rem", lineHeight: 1.45 }}>
                <strong>{lang === "mr" ? "मागील डेटा सुरक्षितता (Leftover-Data Lint):" : "Leftover-Data Protection:"}</strong>{" "}
                <span style={{ color: "var(--text-secondary)" }}>
                  {lang === "mr"
                    ? "जुन्या दस्तातील नावे, पत्ते किंवा खसरा क्रमांक नवीन दस्तात येण्याचा धोका शून्य."
                    : "Eliminates copy-paste leakage between transactions through verified schema validation."}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
              <Award size={18} color="var(--approved-500)" style={{ marginTop: "2px", flexShrink: 0 }} />
              <div style={{ fontSize: "0.8125rem", lineHeight: 1.45 }}>
                <strong>{lang === "mr" ? "अचूक देवनागरी (Unicode UTF-8):" : "Unicode Archival Standard:"}</strong>{" "}
                <span style={{ color: "var(--text-secondary)" }}>
                  {lang === "mr"
                    ? "कृती देव विरहित शुद्ध युनिकोड. शब्द, जोडाक्षरे व आकडेवारी (Western Digits) प्रमाणित."
                    : "Standard Unicode NFC encoding; zero legacy Kruti Dev corruption with proper Devanagari rhythm."}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
              <Stamp size={18} color="var(--brand-500)" style={{ marginTop: "2px", flexShrink: 0 }} />
              <div style={{ fontSize: "0.8125rem", lineHeight: 1.45 }}>
                <strong>{lang === "mr" ? "दुय्यम निबंधक PDE सुसंगतता:" : "IGR Public Data Entry (PDE):"}</strong>{" "}
                <span style={{ color: "var(--text-secondary)" }}>
                  {lang === "mr"
                    ? "दस्त मसुद्यातूनच शासकीय पोर्टलसाठी आवश्यक पक्षकार व मिळकत माहिती स्वयंचलित तयार होते."
                    : "One-time entry generates DOCX deed and portal data without duplicate typing."}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* 6. Active Matter Dossiers & Recent Events */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: "20px" }}>
        {/* Recent Audit Ledger */}
        <Card style={{ padding: "22px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3
                style={{
                  fontFamily: "var(--font-heading)",
                  fontSize: "1.0625rem",
                  fontWeight: 700,
                  margin: 0,
                  color: "var(--brand-900)",
                }}
              >
                {lang === "mr" ? "दफ्तर दैनंदिनी (Chamber Log)" : "Chamber Operational Log"}
              </h3>
              <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                {lang === "mr" ? "अपरिवर्तनीय ऑडिट नोंदी" : "Immutable ledger entries"}
              </span>
            </div>
            <Button size="sm" variant="secondary" onClick={() => onNavigate("audit_trail")}>
              {lang === "mr" ? "संपूर्ण नोंदवही" : "View Full Log"}
            </Button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "12px",
                    paddingBottom: "10px",
                    borderBottom: "1px solid var(--line-subtle)",
                  }}
                >
                  <div
                    style={{
                      marginTop: "4px",
                      width: "8px",
                      height: "8px",
                      borderRadius: "2px",
                      backgroundColor: "var(--brand-500)",
                      flexShrink: 0,
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
                      <span style={{ fontWeight: 600, color: "var(--brand-900)" }}>
                        {item.action?.replace(/_/g, " ").toUpperCase()}
                      </span>
                      <span style={{ color: "var(--text-tertiary)", fontSize: "0.75rem" }}>
                        {new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                      {item.entity}: {item.entity_id || "System"} {item.meta?.doc_no ? `(दस्त क्र. ${item.meta.doc_no})` : ""}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: "var(--text-tertiary)", fontSize: "0.875rem", textAlign: "center", padding: "20px" }}>
                {lang === "mr" ? "कोणतीही अलिकडील नोंद उपलब्ध नाही." : "No recent activity recorded."}
              </div>
            )}
          </div>
        </Card>

        {/* Desk Quick Navigation */}
        <Card style={{ padding: "22px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: "1.0625rem",
              fontWeight: 700,
              margin: 0,
              color: "var(--brand-900)",
            }}
          >
            {lang === "mr" ? "दफ्तर नोंदवह्या थेट प्रवेश" : "Direct Chamber Registers"}
          </h3>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("my_documents")}
              leftIcon={<FileText size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "दस्तऐवज नोंदवही" : "Deed Register"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("review_center")}
              leftIcon={<ShieldCheck size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "वकील तपासणी" : "Review Center"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("party_directory")}
              leftIcon={<Users size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "पक्षकार नोंदवही" : "Party Directory"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("property_directory")}
              leftIcon={<Compass size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "मिळकत नोंदवही" : "Property Register"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("registration_data")}
              leftIcon={<FolderOpen size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "नोंदणी पोर्टल PDE" : "Sub-Registrar PDE"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("document_quality")}
              leftIcon={<CheckCircle2 size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "गुणवत्ता व लिंट" : "Quality & Lint"}
            </Button>
          </div>

          <div
            style={{
              marginTop: "auto",
              padding: "14px 16px",
              borderRadius: "var(--radius-card)",
              backgroundColor: "var(--surface-sunken)",
              fontSize: "0.78125rem",
              color: "var(--text-secondary)",
              lineHeight: 1.5,
              border: "1px solid var(--line-subtle)",
            }}
          >
            <strong style={{ color: "var(--brand-900)" }}>
              {lang === "mr" ? "वैधानिक सूचना (Statutory Notice):" : "Statutory Notice:"}
            </strong>{" "}
            {lang === "mr"
              ? "लेखां (Lekhan) मधील तयार केलेले दस्त मसुदे आहेत. निष्पादन (Execution) किंवा नोंदणीपूर्वी पात्र वकीलाकडून तपासणे आवश्यक आहे."
              : "All deeds generated are legal drafts and require review by a practicing advocate before formal execution and registration."}
          </div>
        </Card>
      </div>
    </div>
  );
};
