import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
import {
  Activity,
  Server,
  Database,
  HardDrive,
  Cpu,
  Layers,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";

interface SystemHealthViewProps {
  onNavigate: (viewId: string) => void;
}

export const SystemHealthView: React.FC<SystemHealthViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [healthData, setHealthData] = useState<any | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const data = await api.getSystemHealth();
      setHealthData(data);
    } catch {
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "सिस्टम कार्यक्षमता व आरोग्य (System Health & Infrastructure)" : "System Health & Infrastructure"}
            </h1>
            <Badge variant="approved" size="md" label="Telemetry Live" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "एपीआय सर्व्हर, डेटाबेस, डॉक्युमेंट स्टोरेज व बॅकग्राउंड जॉब क्यू स्थिती."
              : "Live operational telemetry across FastAPI process, PostgreSQL pooling, storage, and worker pipeline."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button size="sm" variant="secondary" onClick={fetchHealth} leftIcon={<RefreshCw size={14} />}>
            {lang === "mr" ? "रिफ्रेश" : "Refresh"}
          </Button>
          <a href="/metrics" target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
            <Button size="sm" variant="secondary" rightIcon={<ExternalLink size={13} />}>
              Prometheus Metrics
            </Button>
          </a>
        </div>
      </div>

      {/* 2. System Status Overview */}
      {loading ? (
        <Skeleton height="350px" />
      ) : !healthData ? (
        <Card style={{ padding: "40px", textAlign: "center" }}>
          <AlertTriangle size={36} color="var(--danger-600)" style={{ margin: "0 auto 10px auto" }} />
          <div>Failed to connect to health probe.</div>
        </Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
          {/* API Server */}
          <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
                <Server size={18} color="var(--brand-600)" />
                <span>FastAPI Core Server</span>
              </div>
              <Badge variant="active" size="sm" label="Online" />
            </div>
            <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div><strong>Version:</strong> {healthData.api?.version}</div>
              <div><strong>Environment:</strong> {healthData.api?.environment}</div>
              <div><strong>OpenAPI Docs:</strong> {healthData.api?.docs_url}</div>
              <div><strong>Middleware:</strong> Observability + Correlation ID</div>
            </div>
          </Card>

          {/* Database */}
          <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
                <Database size={18} color="var(--brand-600)" />
                <span>PostgreSQL Database</span>
              </div>
              <Badge variant={healthData.database?.status === "connected" ? "active" : "neutral"} size="sm" label={healthData.database?.status?.toUpperCase()} />
            </div>
            <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div><strong>Adapter:</strong> {healthData.database?.adapter}</div>
              <div><strong>Pooling:</strong> {healthData.database?.connection_pooling}</div>
              <div><strong>Status:</strong> {healthData.database?.status}</div>
            </div>
          </Card>

          {/* Storage */}
          <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
                <HardDrive size={18} color="var(--brand-600)" />
                <span>Encrypted Document Store</span>
              </div>
              <Badge variant="active" size="sm" label="Available" />
            </div>
            <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div><strong>Type:</strong> {healthData.storage?.type}</div>
              <div><strong>Path:</strong> <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{healthData.storage?.path}</span></div>
              <div><strong>Free Disk:</strong> {healthData.storage?.free_space_gb} GB free</div>
            </div>
          </Card>

          {/* Template Engine */}
          <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
                <Layers size={18} color="var(--brand-600)" />
                <span>Template Registry & Linter</span>
              </div>
              <Badge variant="approved" size="sm" label="Ready" />
            </div>
            <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div><strong>Total Templates:</strong> {healthData.template_engine?.total_templates}</div>
              <div><strong>Approved Templates:</strong> {healthData.template_engine?.approved_templates}</div>
              <div><strong>Quality Gates:</strong> DocxLinter Active</div>
            </div>
          </Card>

          {/* Worker Queue */}
          <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, color: "var(--brand-900)" }}>
                <Cpu size={18} color="var(--brand-600)" />
                <span>Document Generation Worker</span>
              </div>
              <Badge variant="active" size="sm" label="Active" />
            </div>
            <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div><strong>Pipeline:</strong> {healthData.worker_queue?.engine}</div>
              <div><strong>Queued Jobs:</strong> {healthData.worker_queue?.queued_jobs}</div>
              <div><strong>Execution Mode:</strong> Idempotent with Verification Gate</div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
