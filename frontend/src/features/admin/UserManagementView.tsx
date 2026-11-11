import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Select, Skeleton } from "../../shared/components";
import {
  Users,
  ShieldCheck,
  UserCheck,
  UserX,
  RefreshCw,
  KeyRound,
} from "lucide-react";

interface UserManagementViewProps {
  onNavigate: (viewId: string) => void;
}

export const UserManagementView: React.FC<UserManagementViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<any[]>([]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await api.getUsers();
      setUsers(data || []);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (user: any) => {
    try {
      await api.toggleUserStatus(user.id, !user.active);
      fetchUsers();
    } catch (err: any) {
      alert("Failed to update status: " + (err?.message || "Unauthorized"));
    }
  };

  const handleRoleChange = async (user: any, newRole: string) => {
    try {
      await api.toggleUserStatus(user.id, user.active, newRole);
      fetchUsers();
    } catch (err: any) {
      alert("Failed to update role: " + (err?.message || "Unauthorized"));
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "वापरकर्ता व भूमिका व्यवस्थापन (User Management)" : "User Management & Access Control"}
            </h1>
            <Badge variant="approved" size="md" label="Tenant Scoped RBAC" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "कार्यालयातील वकील, मसुदाकार, साचा व्यवस्थापक आणि नियंत्रक खाती."
              : "Manage advocate accounts, assigned legal roles, active states, and MFA enrollment."}
          </p>
        </div>

        <Button size="sm" variant="secondary" onClick={fetchUsers} leftIcon={<RefreshCw size={14} />}>
          {lang === "mr" ? "रिफ्रेश" : "Refresh"}
        </Button>
      </div>

      {/* 2. User Table */}
      <Card style={{ padding: "0", overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "20px" }}>
            <Skeleton height="200px" />
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--surface-sunken)", borderBottom: "1px solid var(--line-subtle)" }}>
                  <th style={{ padding: "12px 18px", fontWeight: 600 }}>Name & Email</th>
                  <th style={{ padding: "12px 18px", fontWeight: 600 }}>Assigned Role</th>
                  <th style={{ padding: "12px 18px", fontWeight: 600 }}>Account Status</th>
                  <th style={{ padding: "12px 18px", fontWeight: 600 }}>MFA Protection</th>
                  <th style={{ padding: "12px 18px", fontWeight: 600, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ borderBottom: "1px solid var(--line-subtle)" }}>
                    <td style={{ padding: "14px 18px" }}>
                      <div style={{ fontWeight: 600, color: "var(--brand-900)" }}>{u.display_name}</div>
                      <div style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-tertiary)" }}>
                        {u.email}
                      </div>
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <Select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u, e.target.value)}
                        options={[
                          { label: "Admin (Partner)", value: "admin" },
                          { label: "Reviewer (Advocate)", value: "reviewer" },
                          { label: "Drafter (Legal Assistant)", value: "drafter" },
                          { label: "Template Admin", value: "template_admin" },
                        ]}
                      />
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <Badge
                        variant={u.active ? "active" : "neutral"}
                        size="sm"
                        label={u.active ? "Active Account" : "Deactivated"}
                      />
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <span style={{ fontSize: "0.8125rem", color: u.mfa_enabled ? "var(--brand-600)" : "var(--text-tertiary)", display: "flex", alignItems: "center", gap: "6px" }}>
                        <KeyRound size={14} />
                        {u.mfa_enabled ? "TOTP Enabled" : "Single Factor"}
                      </span>
                    </td>
                    <td style={{ padding: "14px 18px", textAlign: "right" }}>
                      <Button
                        size="sm"
                        variant={u.active ? "secondary" : "primary"}
                        onClick={() => handleToggleStatus(u)}
                        leftIcon={u.active ? <UserX size={13} /> : <UserCheck size={13} />}
                      >
                        {u.active ? "Deactivate" : "Activate"}
                      </Button>
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
