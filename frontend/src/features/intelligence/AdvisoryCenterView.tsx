import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
import {
  AlertTriangle,
  Scale,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  RefreshCw,
  Info,
} from "lucide-react";

interface AdvisoryCenterViewProps {
  onNavigate: (viewId: string) => void;
}

export const AdvisoryCenterView: React.FC<AdvisoryCenterViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState<any[]>([]);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await api.getAdvisoryRules();
      setRules(data || []);
    } catch {
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "कायदेशीर सल्ला व वैधानिक नियम केंद्र (Advisory Center)" : "Advisory Center & Statutory Rules"}
            </h1>
            <Badge variant="approved" size="md" label="Advocate-Authored Rules" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "आयकर कायदा, टीडीएस, पॅन फॉर्म ६०, महारेरा व शेतजमीन हस्तांतरण वैधानिक मार्गदर्शक सूचना."
              : "Lawyer-authored compliance advisories for Section 194-IA TDS, Rule 114B PAN, MahaRERA, and Tenancy laws."}
          </p>
        </div>

        <Button size="sm" variant="secondary" onClick={fetchRules} leftIcon={<RefreshCw size={14} />}>
          {lang === "mr" ? "रिफ्रेश" : "Refresh"}
        </Button>
      </div>

      {/* 2. Advisory Notice */}
      <div
        style={{
          padding: "16px 20px",
          borderRadius: "var(--radius-card)",
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--line-subtle)",
          display: "flex",
          gap: "14px",
          alignItems: "center",
        }}
      >
        <Scale size={24} color="var(--brand-600)" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: "0.875rem", lineHeight: 1.5, color: "var(--text-secondary)" }}>
          <strong style={{ color: "var(--text-primary)" }}>
            {lang === "mr" ? "वैधानिक सल्ला मार्गदर्शक:" : "Statutory Guidance Principles:"}
          </strong>{" "}
          {lang === "mr"
            ? "सल्ला नियम हे गैर-अडथळा (Non-blocking) असून मसुदा तयार करताना वकिलांना व पक्षकारांना संभाव्य कायदेशीर दायित्वे व कर कपातीची जाणीव करून देण्यासाठी बनवले आहेत."
            : "Advisory rules provide non-blocking statutory reminders to protect drafters and parties from compliance penalties under Central and Maharashtra state enactments."}
        </div>
      </div>

      {/* 3. Advisory Rules Catalog */}
      {loading ? (
        <Skeleton height="350px" />
      ) : rules.length === 0 ? (
        <Card style={{ padding: "40px", textAlign: "center" }}>
          <AlertTriangle size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
          <div>{lang === "mr" ? "नियम लोड होऊ शकले नाहीत." : "No advisory rules found."}</div>
        </Card>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {rules.map((rule) => {
            const isWarning = rule.severity === "warning";

            return (
              <Card
                key={rule.id}
                style={{
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  borderLeft: `4px solid ${isWarning ? "#D97706" : "var(--brand-500)"}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "8px" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <h3 style={{ fontSize: "1.0625rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
                        {lang === "mr" ? rule.title_mr || rule.title_en : rule.title_en}
                      </h3>
                      <Badge
                        variant={isWarning ? "approved" : "neutral"}
                        size="sm"
                        label={rule.severity.toUpperCase()}
                      />
                    </div>
                    <div style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-tertiary)", marginTop: "2px" }}>
                      {rule.id} | {rule.rule_name}
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      backgroundColor: "var(--surface-sunken)",
                      padding: "4px 10px",
                      borderRadius: "var(--radius-pill)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {rule.statutory_ref}
                  </span>
                </div>

                <p style={{ fontSize: "0.875rem", lineHeight: 1.6, color: "var(--text-primary)", margin: 0 }}>
                  {lang === "mr" ? rule.advice_mr || rule.advice_en : rule.advice_en}
                </p>

                {rule.action_needed && (
                  <div
                    style={{
                      marginTop: "6px",
                      padding: "10px 14px",
                      borderRadius: "var(--radius-input)",
                      backgroundColor: "var(--surface-sunken)",
                      fontSize: "0.8125rem",
                      color: "var(--brand-900)",
                    }}
                  >
                    <strong>{lang === "mr" ? "शिफारस केलेली कृती (Recommended Action):" : "Recommended Action:"}</strong>{" "}
                    {rule.action_needed}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

