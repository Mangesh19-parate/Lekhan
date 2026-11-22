import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, type PilotStatsResponse } from "../../shared/api";
import { Card, Button, Badge, Skeleton } from "../../shared/components";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  BarChart3,
  Layers,
  FileCheck,
  RefreshCw,
  HelpCircle,
  MessageSquare,
} from "lucide-react";

interface PilotStatsViewProps {
  onNavigate: (viewId: string) => void;
}

export const PilotStatsView: React.FC<PilotStatsViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<PilotStatsResponse | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await api.getPilotStats();
      setStats(data);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "पायलट प्रकल्प विश्लेषण (Pilot Statistics)" : "Pilot Performance & Drafter Feedback"}
            </h1>
            <Badge variant="approved" size="md" label="Active Pilot Phase" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "पायलट मसुदाकार व वकिलांचे अभिप्राय, दुरुस्त्यांचा कल आणि निवारण दर (PRD Section 10)."
              : "Advocate & drafter correction log, triage metrics, and resolution rate per PRD Section 10."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <Button size="sm" variant="secondary" onClick={fetchStats} isLoading={loading} leftIcon={<RefreshCw size={14} />}>
            {lang === "mr" ? "रिफ्रेश" : "Refresh"}
          </Button>
        </div>
      </div>

      {loading ? (
        <Skeleton height="350px" />
      ) : !stats ? (
        <Card style={{ padding: "40px", textAlign: "center" }}>
          <Activity size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
          <div style={{ fontWeight: 600 }}>No pilot statistics available.</div>
        </Card>
      ) : (
        <>
          {/* Key Metric Highlights */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
            <Card style={{ padding: "20px" }}>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                {lang === "mr" ? "एकूण नोंदवलेल्या दुरुस्त्या" : "Total Corrections Logged"}
              </div>
              <div style={{ fontSize: "1.875rem", fontWeight: 700, color: "var(--brand-900)", marginTop: "4px" }}>
                {stats.total_logged}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "4px" }}>
                Across all pilot legal drafts
              </div>
            </Card>

            <Card style={{ padding: "20px" }}>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                {lang === "mr" ? "यशस्वीरित्या सोडवलेल्या" : "Resolved Corrections"}
              </div>
              <div style={{ fontSize: "1.875rem", fontWeight: 700, color: "var(--brand-600)", marginTop: "4px" }}>
                {stats.total_resolved}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)", marginTop: "4px" }}>
                {stats.total_pending} issues pending triage
              </div>
            </Card>

            <Card style={{ padding: "20px" }}>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                {lang === "mr" ? "निवारण दर (Resolution Rate)" : "Resolution Rate"}
              </div>
              <div style={{ fontSize: "1.875rem", fontWeight: 700, color: "var(--brand-900)", marginTop: "4px" }}>
                {stats.resolution_rate_percent.toFixed(1)}%
              </div>
              <div style={{ fontSize: "0.75rem", color: stats.resolution_rate_percent >= 80 ? "var(--brand-600)" : "var(--warning-600)", marginTop: "4px" }}>
                {stats.resolution_rate_percent >= 80 ? "On target (> 80%)" : "Attention needed"}
              </div>
            </Card>

            <Card style={{ padding: "20px" }}>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                {lang === "mr" ? "प्रति दस्त सरासरी दुरुस्त्या" : "Avg Corrections / Draft"}
              </div>
              <div style={{ fontSize: "1.875rem", fontWeight: 700, color: stats.blocking_count > 0 ? "var(--danger-600)" : "var(--brand-900)", marginTop: "4px" }}>
                {stats.avg_corrections_per_draft.toFixed(2)}
              </div>
              <div style={{ fontSize: "0.75rem", color: stats.blocking_count > 0 ? "var(--danger-600)" : "var(--text-tertiary)", marginTop: "4px" }}>
                {stats.blocking_count} blocking flaw{stats.blocking_count !== 1 ? "s" : ""}
              </div>
            </Card>
          </div>

          {/* Breakdown Grids */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            {/* Category Breakdown */}
            <Card style={{ padding: "20px" }}>
              <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 14px 0", color: "var(--brand-900)" }}>
                {lang === "mr" ? "दुरुस्ती प्रकार विभागणी" : "Corrections by Category"}
              </h2>
              {Object.keys(stats.category_breakdown || {}).length === 0 ? (
                <div style={{ color: "var(--text-secondary)", fontSize: "0.8125rem" }}>No category data logged yet.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {Object.entries(stats.category_breakdown).map(([cat, count]) => (
                    <div
                      key={cat}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "8px 12px",
                        backgroundColor: "var(--surface-sunken)",
                        borderRadius: "var(--radius-input)",
                        fontSize: "0.8125rem",
                      }}
                    >
                      <span style={{ fontWeight: 500 }}>{cat.replace(/_/g, " ").toUpperCase()}</span>
                      <Badge variant="neutral" size="sm" label={`${count} incidents`} />
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Template Breakdown */}
            <Card style={{ padding: "20px" }}>
              <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 14px 0", color: "var(--brand-900)" }}>
                {lang === "mr" ? "साच्यानुसार दुरुस्त्या" : "Corrections by Template"}
              </h2>
              {Object.keys(stats.template_breakdown || {}).length === 0 ? (
                <div style={{ color: "var(--text-secondary)", fontSize: "0.8125rem" }}>No template breakdown data logged yet.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {Object.entries(stats.template_breakdown).map(([tmpl, count]) => (
                    <div
                      key={tmpl}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "8px 12px",
                        backgroundColor: "var(--surface-sunken)",
                        borderRadius: "var(--radius-input)",
                        fontSize: "0.8125rem",
                      }}
                    >
                      <span style={{ fontWeight: 500, fontFamily: "var(--font-mono)" }}>{tmpl}</span>
                      <Badge variant={count > 5 ? "under_review" : "neutral"} size="sm" label={`${count} items`} />
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
};
