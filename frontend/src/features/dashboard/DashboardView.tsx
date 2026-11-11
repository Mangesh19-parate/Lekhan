import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
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
} from "lucide-react";

interface DashboardViewProps {
  onNavigate: (viewId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const { lang, t } = useI18n();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load operational metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: "28px", maxWidth: "1400px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
        <Skeleton height="80px" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
          <Skeleton height="110px" />
          <Skeleton height="110px" />
          <Skeleton height="110px" />
          <Skeleton height="110px" />
        </div>
        <Skeleton height="320px" />
      </div>
    );
  }

  const mrDist = stats?.language_distribution?.mr || 0;
  const enDist = stats?.language_distribution?.en || 0;
  const totalLang = (mrDist + enDist) || 1;
  const mrPct = Math.round((mrDist / totalLang) * 100);
  const enPct = 100 - mrPct;

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header with Refresh & Quick Actions */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "कार्यकारी डॅशबोर्ड (Operations Overview)" : "Operational Overview"}
            </h1>
            <Badge variant="approved" size="md" label="Live System" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "दस्त नोंदणी, मसुदा स्थिती, मंजुरी प्रवाह आणि ऑडिट नोंदींचा थेट आढावा."
              : "Real-time legal drafting telemetry, lifecycle distribution, and audit verification."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={fetchStats}
            leftIcon={<RefreshCw size={14} />}
          >
            {lang === "mr" ? "रिफ्रेश" : "Refresh"}
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => onNavigate("new_draft")}
            leftIcon={<Plus size={15} />}
          >
            {lang === "mr" ? "नवीन दस्त तयार करा" : "Create New Draft"}
          </Button>
        </div>
      </div>

      {/* 2. Operational Alerts */}
      {stats?.operational_alerts && stats.operational_alerts.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {stats.operational_alerts.map((alert: any) => (
            <div
              key={alert.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 18px",
                borderRadius: "var(--radius-card)",
                backgroundColor: alert.severity === "warning" ? "var(--approved-100)" : alert.severity === "success" ? "var(--brand-100)" : "#EBF3FF",
                border: `1px solid ${alert.severity === "warning" ? "var(--approved-500)" : alert.severity === "success" ? "var(--brand-500)" : "#3B82F6"}`,
                color: "var(--text-primary)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                {alert.severity === "warning" ? (
                  <AlertTriangle size={18} color="#B45309" />
                ) : alert.severity === "success" ? (
                  <ShieldCheck size={18} color="var(--brand-600)" />
                ) : (
                  <CheckCircle2 size={18} color="#2563EB" />
                )}
                <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>
                  {lang === "mr" ? alert.title_mr : alert.title_en}
                </span>
              </div>
              {alert.action_url && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => onNavigate(alert.action_url)}
                  rightIcon={<ArrowRight size={13} />}
                >
                  {lang === "mr" ? "तपासा" : "Open"}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 3. Primary KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "16px" }}>
        <Card style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8125rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {lang === "mr" ? "एकूण निर्माण केलेले दस्त" : "Total Documents"}
            </span>
            <FileText size={18} color="var(--brand-600)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--brand-900)" }}>
            {stats?.total_documents || 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {stats?.documents_today || 0} {lang === "mr" ? "आज तयार केले" : "generated today"}
          </div>
        </Card>

        <Card style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8125rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {lang === "mr" ? "प्रलंबित मसुदे (Drafts)" : "Drafts in Progress"}
            </span>
            <Clock size={18} color="#D97706" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#D97706" }}>
            {stats?.drafts_in_progress || 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "ऑटोसॅव्ह व संपादन सुरू" : "Active matters being drafted"}
          </div>
        </Card>

        <Card style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8125rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {lang === "mr" ? "वकिलांची तपासणी प्रलंबित" : "Pending Reviews"}
            </span>
            <AlertTriangle size={18} color="#B45309" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--approved-500)" }}>
            {stats?.pending_reviews || 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "चेकलिस्ट व मान्यता बाकी" : "Awaiting statutory checklist sign-off"}
          </div>
        </Card>

        <Card style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8125rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {lang === "mr" ? "अंतिम केलेले दस्त" : "Finalised Deeds"}
            </span>
            <CheckCircle2 size={18} color="var(--brand-500)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--brand-600)" }}>
            {stats?.finalised_documents || 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "नोंदणीसाठी कुलूपबंद (Locked)" : "Immutable locked for registration"}
          </div>
        </Card>

        <Card style={{ padding: "18px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8125rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {lang === "mr" ? "मान्य केलेले साचे" : "Approved Templates"}
            </span>
            <Layers size={18} color="var(--brand-600)" />
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--brand-900)" }}>
            {stats?.approved_templates || 0}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "Wave 1 कायदेशीर साचे" : "DocxLinter verified library"}
          </div>
        </Card>
      </div>

      {/* 4. Analytics & Lifecycle Distribution */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "20px" }}>
        {/* Language Breakdown */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
              {lang === "mr" ? "भाषा वितरण (Language Distribution)" : "Language Distribution"}
            </h3>
            <Badge variant="neutral" size="sm" label="Marathi First" />
          </div>

          <div style={{ display: "flex", height: "16px", borderRadius: "var(--radius-pill)", overflow: "hidden", backgroundColor: "var(--surface-sunken)" }}>
            <div style={{ width: `${mrPct}%`, backgroundColor: "var(--brand-600)", transition: "width 0.4s" }} title={`Marathi: ${mrDist}`} />
            <div style={{ width: `${enPct}%`, backgroundColor: "var(--brand-400)", transition: "width 0.4s" }} title={`English: ${enDist}`} />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "var(--brand-600)" }} />
              <span>मराठी (Marathi): <strong>{mrDist}</strong> ({mrPct}%)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "var(--brand-400)" }} />
              <span>English: <strong>{enDist}</strong> ({enPct}%)</span>
            </div>
          </div>
        </Card>

        {/* Deed Type Breakdown */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
              {lang === "mr" ? "दस्त प्रकार विभागणी (Deed Types)" : "Document Classification"}
            </h3>
            <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
              {lang === "mr" ? "प्रमाणित साचे" : "Active deed categories"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {Object.entries(stats?.document_type_distribution || {}).map(([dtype, count]: [string, any]) => (
              <div key={dtype} style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "0.8125rem" }}>
                <span style={{ minWidth: "150px", fontWeight: 500 }}>{dtype}</span>
                <div style={{ flex: 1, height: "8px", borderRadius: "var(--radius-pill)", backgroundColor: "var(--surface-sunken)", overflow: "hidden" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${Math.min(100, Math.max(12, (count / (stats?.total_documents || 1)) * 100))}%`,
                      backgroundColor: "var(--brand-500)",
                    }}
                  />
                </div>
                <span style={{ fontWeight: 600, minWidth: "30px", textAlign: "right" }}>{count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 5. Real Activity Timeline & Quick Links */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
        {/* Timeline */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
              {lang === "mr" ? "अलिकडील कार्यप्रवाह (Recent Activity)" : "Recent Operational Events"}
            </h3>
            <Button size="sm" variant="secondary" onClick={() => onNavigate("audit_trail")}>
              {lang === "mr" ? "संपूर्ण ऑडिट ट्रेल" : "View Audit Trail"}
            </Button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.slice(0, 6).map((item: any) => (
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
                      marginTop: "2px",
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
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
                      {item.entity}: {item.entity_id || "System"} {item.meta?.doc_no ? `(${item.meta.doc_no})` : ""}
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

        {/* Quick Launchpad */}
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
            {lang === "mr" ? "जलद पर्याय (Quick Actions)" : "Operations Launchpad"}
          </h3>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("new_draft")}
              leftIcon={<Plus size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "नवीन मसुदा" : "New Draft"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("review_center")}
              leftIcon={<ShieldCheck size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "दस्त तपासणी" : "Review Center"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("template_library")}
              leftIcon={<Layers size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "साचे लायब्ररी" : "Template Library"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("party_directory")}
              leftIcon={<Users size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "पक्षकार सूची" : "Party Directory"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("registration_data")}
              leftIcon={<FolderOpen size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "नोंदणी पोर्टल डेटा" : "Registration Data"}
            </Button>
            <Button
              size="md"
              variant="secondary"
              onClick={() => onNavigate("system_health")}
              leftIcon={<TrendingUp size={16} />}
              style={{ justifyContent: "flex-start" }}
            >
              {lang === "mr" ? "सिस्टम स्थिती" : "System Health"}
            </Button>
          </div>

          <div
            style={{
              marginTop: "auto",
              padding: "12px",
              borderRadius: "var(--radius-input)",
              backgroundColor: "var(--surface-sunken)",
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              lineHeight: 1.5,
            }}
          >
            <strong>{lang === "mr" ? "कायदेशीर सूचना:" : "Statutory Notice:"}</strong>{" "}
            {lang === "mr"
              ? "तयार केलेले दस्त केवळ मसुदे आहेत. निष्पादन किंवा नोंदणीपूर्वी पात्र वकीलाकडून तपासणे आवश्यक आहे."
              : "Generated deeds are drafts and require verification by a qualified advocate before execution or registration."}
          </div>
        </Card>
      </div>
    </div>
  );
};
