import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Hash,
  RefreshCw,
  Lock,
} from "lucide-react";

interface AuditTrailViewProps {
  onNavigate: (viewId: string) => void;
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [auditData, setAuditData] = useState<any | null>(null);

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditTrail();
      setAuditData(data);
    } catch {
      setAuditData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
  }, []);

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "वैधानिक ऑडिट ट्रेल (Statutory Audit Trail)" : "Statutory Audit Trail"}
            </h1>
            <Badge variant="approved" size="md" label="SHA-256 Hash Chained" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "सर्व दस्त निर्मिती, फेरबदल व मंजुरी घटनांची अपरिवर्तनीय आणि क्रिप्टोग्राफिक नोंद."
              : "Append-only, SHA-256 hash-chained cryptographic ledger with zero personal data logging (Hard Rule 5)."}
          </p>
        </div>

        <Button size="sm" variant="secondary" onClick={fetchAudit} leftIcon={<RefreshCw size={14} />}>
          {lang === "mr" ? "रिफ्रेश" : "Refresh"}
        </Button>
      </div>

      {/* 2. Chain Integrity Banner */}
      <div
        style={{
          padding: "16px 20px",
          borderRadius: "var(--radius-card)",
          backgroundColor: auditData?.chain_valid ? "var(--brand-100)" : "#FEE2E2",
          border: `1px solid ${auditData?.chain_valid ? "var(--brand-500)" : "#FCA5A5"}`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {auditData?.chain_valid ? (
            <ShieldCheck size={24} color="var(--brand-600)" />
          ) : (
            <AlertTriangle size={24} color="var(--danger-600)" />
          )}
          <div>
            <div style={{ fontWeight: 700, fontSize: "1rem", color: auditData?.chain_valid ? "var(--brand-900)" : "#991B1B" }}>
              {auditData?.chain_valid
                ? lang === "mr"
                  ? "क्रिप्टोग्राफिक साखळी अखंडित व सुरक्षित (Tamper-evident Chain Intact)"
                  : "Cryptographic Audit Chain Intact & Verified"
                : "Tamper Detected in Audit Chain!"}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
              Every event block is mathematically sealed by SHA-256 digest of the predecessor record.
            </div>
          </div>
        </div>

        <Badge variant={auditData?.chain_valid ? "approved" : "neutral"} size="md" label={`${auditData?.total_records || 0} Total Blocks`} />
      </div>

      {/* 3. Audit Log Entries Table */}
      <Card style={{ padding: "0", overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "20px" }}>
            <Skeleton height="300px" />
          </div>
        ) : !auditData?.records || auditData.records.length === 0 ? (
          <div style={{ padding: "40px", textAlign: "center", color: "var(--text-secondary)" }}>
            No audit records recorded yet.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.8125rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--surface-sunken)", borderBottom: "1px solid var(--line-subtle)" }}>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>Seq #</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>Action</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>Entity</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>Entity ID</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>Timestamp</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>Block SHA-256 Hash</th>
                </tr>
              </thead>
              <tbody>
                {auditData.records.map((rec: any) => (
                  <tr key={rec.id} style={{ borderBottom: "1px solid var(--line-subtle)" }}>
                    <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                      #{rec.id}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <Badge variant="neutral" size="sm" label={rec.action.toUpperCase()} />
                    </td>
                    <td style={{ padding: "12px 16px", fontWeight: 500 }}>
                      {rec.entity}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                      {rec.entity_id || "System"}
                    </td>
                    <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>
                      {new Date(rec.timestamp).toLocaleString([], {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--brand-900)" }}>
                      <span title={`Full Hash: ${rec.hash}`}>
                        {rec.hash?.slice(0, 16)}...
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

