import React, { useEffect, useState, useMemo } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Input, Select, Modal, Skeleton } from "../../shared/components";
import {
  Layers,
  Search,
  CheckCircle2,
  FileCode,
  FileText,
  Play,
  Eye,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

interface TemplateLibraryViewProps {
  onNavigate: (viewId: string, templateId?: string) => void;
  onSelectTemplateForDrafting?: (templateItem: any) => void;
}

export const TemplateLibraryView: React.FC<TemplateLibraryViewProps> = ({
  onNavigate,
  onSelectTemplateForDrafting,
}) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [langFilter, setLangFilter] = useState("all");
  const [propertyFilter, setPropertyFilter] = useState("all");
  const [selectedManifest, setSelectedManifest] = useState<any | null>(null);
  const [manifestModalOpen, setManifestModalOpen] = useState(false);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await api.listTemplates();
      setTemplates(data || []);
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const filteredTemplates = useMemo(() => {
    return templates.filter((t) => {
      if (langFilter !== "all" && t.language !== langFilter) return false;
      if (propertyFilter !== "all" && t.property_type !== propertyFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchName = (t.name_en || "").toLowerCase().includes(q) || (t.name_mr || "").toLowerCase().includes(q);
        const matchId = (t.template_id || "").toLowerCase().includes(q);
        if (!matchName && !matchId) return false;
      }
      return true;
    });
  }, [templates, langFilter, propertyFilter, searchQuery]);

  const handleInspectManifest = async (tId: string) => {
    try {
      const manifest = await api.getTemplateManifest(tId);
      setSelectedManifest(manifest);
      setManifestModalOpen(true);
    } catch (e: any) {
      alert("Failed to load manifest schema: " + e?.message);
    }
  };

  const handleStartDraft = (tmpl: any) => {
    if (onSelectTemplateForDrafting) {
      onSelectTemplateForDrafting(tmpl);
    }
    onNavigate("new_draft", tmpl.template_id);
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "साचे ग्रंथालय (Approved Template Library)" : "Approved Template Library"}
            </h1>
            <Badge variant="approved" size="md" label="Wave 1 Legal Suite" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "कंपनीचे अधिकृत, तपासलेले व आवृत्तीबद्ध दस्त साचे (DOCX) आणि मॅनिफेस्ट स्कीमा."
              : "Company-approved, immutable versioned deed templates with manifest schemas and lint verification."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button size="sm" variant="secondary" onClick={fetchTemplates} leftIcon={<RefreshCw size={14} />}>
            {lang === "mr" ? "रिफ्रेश" : "Refresh"}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => onNavigate("template_studio")} leftIcon={<FileCode size={14} />}>
            {lang === "mr" ? "साचा स्टुडिओ (Studio)" : "Template Studio"}
          </Button>
        </div>
      </div>

      {/* 2. Filters */}
      <Card style={{ padding: "16px", display: "flex", flexWrap: "wrap", gap: "14px", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: "10px", flex: 1, minWidth: "260px" }}>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={lang === "mr" ? "साचा शोधा (खरेदीखत, भूखंड, फ्लॅट...)" : "Search templates (sale deed, plot, flat, poa)..."}
            leftAddon={<Search size={16} />}
            style={{ width: "100%" }}
          />
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {lang === "mr" ? "भाषा:" : "Language:"}
            </span>
            <Select
              value={langFilter}
              onChange={(e) => setLangFilter(e.target.value)}
              options={[
                { label: lang === "mr" ? "सर्व भाषा (All)" : "All Languages", value: "all" },
                { label: "मराठी (mr)", value: "mr" },
                { label: "English (en)", value: "en" },
              ]}
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {lang === "mr" ? "मिळकत प्रकार:" : "Property Type:"}
            </span>
            <Select
              value={propertyFilter}
              onChange={(e) => setPropertyFilter(e.target.value)}
              options={[
                { label: lang === "mr" ? "सर्व प्रकार (All)" : "All Types", value: "all" },
                { label: lang === "mr" ? "भूखंड (Plot)" : "Plot", value: "plot" },
                { label: lang === "mr" ? "सदनिका (Flat)" : "Flat", value: "flat" },
                { label: lang === "mr" ? "दुकान (Shop)" : "Shop", value: "shop" },
                { label: lang === "mr" ? "शेतीजमीन (Agricultural)" : "Agricultural", value: "agricultural" },
              ]}
            />
          </div>
        </div>
      </Card>

      {/* 3. Template Cards Grid */}
      {loading ? (
        <Skeleton height="300px" />
      ) : filteredTemplates.length === 0 ? (
        <Card style={{ padding: "48px 24px", textAlign: "center" }}>
          <Layers size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
          <div style={{ fontWeight: 600 }}>{lang === "mr" ? "कोणताही साचा सापडला नाही." : "No templates matched."}</div>
        </Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: "20px" }}>
          {filteredTemplates.map((t) => (
            <Card
              key={t.template_id}
              style={{
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                gap: "14px",
                transition: "all var(--transition-fast)",
                border: t.status === "approved" ? "1px solid var(--brand-100)" : "1px solid var(--line-subtle)",
              }}
              className="hover:shadow-md"
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                <div>
                  <div style={{ fontSize: "1.0625rem", fontWeight: 700, color: "var(--brand-900)" }}>
                    {lang === "mr" ? t.name_mr || t.name_en : t.name_en}
                  </div>
                  <div style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-tertiary)", marginTop: "2px" }}>
                    {t.template_id} (v{t.version})
                  </div>
                </div>
                <Badge
                  variant={t.status === "approved" ? "approved" : t.status === "under_review" ? "neutral" : "neutral"}
                  size="sm"
                  label={t.status.toUpperCase()}
                />
              </div>

              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", fontSize: "0.75rem" }}>
                <span style={{ backgroundColor: "var(--surface-sunken)", padding: "3px 8px", borderRadius: "var(--radius-pill)" }}>
                  {t.language === "mr" ? "मराठी" : "English"}
                </span>
                <span style={{ backgroundColor: "var(--surface-sunken)", padding: "3px 8px", borderRadius: "var(--radius-pill)" }}>
                  {t.document_type}
                </span>
                <span style={{ backgroundColor: "var(--surface-sunken)", padding: "3px 8px", borderRadius: "var(--radius-pill)" }}>
                  {t.property_type}
                </span>
              </div>

              <div style={{ marginTop: "auto", display: "flex", gap: "8px", paddingTop: "12px", borderTop: "1px solid var(--line-subtle)" }}>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleInspectManifest(t.template_id)}
                  leftIcon={<Eye size={13} />}
                  style={{ flex: 1 }}
                >
                  {lang === "mr" ? "मॅनिफेस्ट पहा" : "Inspect Schema"}
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleStartDraft(t)}
                  leftIcon={<Play size={13} />}
                  style={{ flex: 1 }}
                >
                  {lang === "mr" ? "मसुदा सुरू करा" : "Draft Deed"}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 4. Manifest Schema Modal */}
      {selectedManifest && (
        <Modal
          isOpen={manifestModalOpen}
          onClose={() => setManifestModalOpen(false)}
          title={`Manifest Schema: ${selectedManifest.template_id}`}
          maxWidth="750px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{ fontWeight: 600 }}>{selectedManifest.name_en}</span>
                <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>{selectedManifest.name_mr}</div>
              </div>
              <Badge variant="approved" size="sm" label={`Version ${selectedManifest.version}`} />
            </div>

            {selectedManifest.sections && (
              <div>
                <h4 style={{ fontSize: "0.875rem", fontWeight: 600, margin: "0 0 6px 0" }}>Sections & Required Fields</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {selectedManifest.sections.map((s: any) => (
                    <div key={s.id} style={{ backgroundColor: "var(--surface-sunken)", padding: "8px 12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem" }}>
                      <strong>{s.title_en}</strong> ({s.title_mr})
                      <div style={{ color: "var(--text-tertiary)", fontSize: "0.75rem", marginTop: "2px" }}>
                        Fields: {s.field_names?.join(", ")}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h4 style={{ fontSize: "0.875rem", fontWeight: 600, margin: "0 0 6px 0" }}>Raw Schema JSON</h4>
              <pre
                style={{
                  backgroundColor: "var(--surface-sunken)",
                  padding: "12px",
                  borderRadius: "var(--radius-input)",
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  maxHeight: "220px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                }}
              >
                {JSON.stringify(selectedManifest, null, 2)}
              </pre>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
