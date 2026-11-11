import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Lock,
  RefreshCw,
} from "lucide-react";

interface RolesPermissionsViewProps {
  onNavigate: (viewId: string) => void;
}

export const RolesPermissionsView: React.FC<RolesPermissionsViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [rbacData, setRbacData] = useState<any | null>(null);

  const fetchMatrix = async () => {
    setLoading(true);
    try {
      const data = await api.getRolesPermissions();
      setRbacData(data);
    } catch {
      setRbacData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatrix();
  }, []);

  const roles = rbacData?.roles || ["admin", "template_admin", "reviewer", "drafter"];
  const matrix = rbacData?.matrix || {};
  
  // Extract all distinct actions across roles
  const allActions = Array.from(
    new Set(Object.values(matrix).flatMap((actions: any) => actions))
  ).sort() as string[];

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "भूमिका व अधिकार मॅट्रिक्स (Roles & Permissions Matrix)" : "Roles & Authorization Matrix"}
            </h1>
            <Badge variant="approved" size="md" label="Backend Enforced" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "सर्व ऑपरेशन्ससाठी बॅकएंडवर सक्तीने लागू केलेले अधिकार नियम (Hard Rule 6)."
              : "Authoritative backend permission enforcement (authorize(actor, action, resource)). A hidden button is not security."}
          </p>
        </div>

        <Button size="sm" variant="secondary" onClick={fetchMatrix} leftIcon={<RefreshCw size={14} />}>
          {lang === "mr" ? "रिफ्रेश" : "Refresh"}
        </Button>
      </div>

      {/* 2. Separation of Duties Card */}
      {rbacData?.separation_of_duties && (
        <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--brand-900)", fontWeight: 700 }}>
            <Lock size={18} color="var(--brand-600)" />
            <span>Statutory Separation of Duties & Defense-in-Depth</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "14px" }}>
            {rbacData.separation_of_duties.map((sod: any, idx: number) => (
              <div
                key={idx}
                style={{
                  backgroundColor: "var(--surface-sunken)",
                  padding: "12px 16px",
                  borderRadius: "var(--radius-input)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                }}
              >
                <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--brand-900)" }}>
                  {sod.rule}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                  {sod.description}
                </div>
                <div style={{ fontSize: "0.6875rem", fontFamily: "var(--font-mono)", color: "var(--text-tertiary)", marginTop: "4px" }}>
                  Enforced at: {sod.enforced_at}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 3. Authoritative RBAC Matrix Table */}
      <Card style={{ padding: "0", overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "20px" }}>
            <Skeleton height="300px" />
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--surface-sunken)", borderBottom: "1px solid var(--line-subtle)" }}>
                  <th style={{ padding: "12px 18px", fontWeight: 600, minWidth: "240px" }}>Action / Operation</th>
                  {roles.map((r: string) => (
                    <th key={r} style={{ padding: "12px 18px", fontWeight: 600, textTransform: "capitalize", textAlign: "center" }}>
                      {r.replace("_", " ")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allActions.map((action: string) => (
                  <tr key={action} style={{ borderBottom: "1px solid var(--line-subtle)" }}>
                    <td style={{ padding: "12px 18px", fontFamily: "var(--font-mono)", fontSize: "0.8125rem", color: "var(--brand-900)" }}>
                      {action}
                    </td>
                    {roles.map((r: string) => {
                      const allowed = matrix[r]?.includes(action);
                      return (
                        <td key={r} style={{ padding: "12px 18px", textAlign: "center" }}>
                          {allowed ? (
                            <CheckCircle2 size={18} color="var(--brand-600)" style={{ margin: "0 auto" }} />
                          ) : (
                            <span style={{ color: "rgba(0,0,0,0.2)" }}>—</span>
                          )}
                        </td>
                      );
                    })}
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

