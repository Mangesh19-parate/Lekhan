import React, { useEffect, useState, useMemo } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Input, Select, Modal, Skeleton } from "../../shared/components";
import { DocumentReviewModal } from "../review/DocumentReviewModal";
import {
  FileText,
  Search,
  Download,
  Eye,
  ShieldCheck,
  Filter,
  FileCode,
  Calendar,
  Lock,
  ArrowUpDown,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

interface DocumentsListViewProps {
  onNavigate: (viewId: string) => void;
  initialStatusFilter?: string;
  isArchiveMode?: boolean;
}

export const DocumentsListView: React.FC<DocumentsListViewProps> = ({
  onNavigate,
  initialStatusFilter,
  isArchiveMode = false,
}) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>(
    isArchiveMode ? "finalised" : initialStatusFilter || "all"
  );
  const [langFilter, setLangFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"created_at" | "doc_no">("created_at");
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [reviewModalDoc, setReviewModalDoc] = useState<any | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await api.listDocuments({
        status: statusFilter === "all" ? undefined : statusFilter,
        search: searchQuery || undefined,
        limit: 100,
      });
      setDocuments(res.items || []);
      setTotal(res.total || 0);
    } catch {
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDocuments();
  };

  const filteredDocs = useMemo(() => {
    return documents.filter((d) => {
      if (langFilter !== "all" && d.language !== langFilter) return false;
      return true;
    });
  }, [documents, langFilter]);

  const handleViewDetail = async (docSummary: any) => {
    try {
      const fullDoc = await api.getDocument(docSummary.id);
      setSelectedDoc(fullDoc);
      setDetailModalOpen(true);
    } catch {
      setSelectedDoc(docSummary);
      setDetailModalOpen(true);
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {isArchiveMode
                ? lang === "mr"
                  ? "दस्त अभिलेखागार (Document Archive)"
                  : "Document Archive"
                : lang === "mr"
                ? "माझे दस्त नोंदवही (My Documents)"
                : "Document Registry"}
            </h1>
            <Badge
              variant={isArchiveMode ? "approved" : "neutral"}
              size="md"
              label={isArchiveMode ? "Immutable Archive" : `${total} Records`}
            />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {isArchiveMode
              ? lang === "mr"
                ? "अंतिम झालेले, स्वाक्षरी केलेले व नोंदणीकृत कायदेशीर दस्तऐवज."
                : "Tamper-evident, finalized legal deeds sealed for permanent statutory retention."
              : lang === "mr"
              ? "सर्व तयार केलेले, प्रलंबित आणि तपासणी झालेले खरेदीखत व करारनामे."
              : "Searchable registry of deeds generated across drafting, review, and completion stages."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <Button size="sm" variant="secondary" onClick={fetchDocuments} leftIcon={<RefreshCw size={14} />}>
            {lang === "mr" ? "रिफ्रेश" : "Refresh"}
          </Button>
          <Button size="sm" variant="primary" onClick={() => onNavigate("new_draft")} leftIcon={<FileText size={15} />}>
            {lang === "mr" ? "नवीन मसुदा" : "New Draft"}
          </Button>
        </div>
      </div>

      {/* 2. Filters & Search Bar */}
      <Card style={{ padding: "16px", display: "flex", flexWrap: "wrap", gap: "14px", alignItems: "center", justifyContent: "space-between" }}>
        <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "10px", flex: 1, minWidth: "280px" }}>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={
              lang === "mr"
                ? "दस्त क्र., पक्षकाराचे नाव, सर्व्हे क्र., मौजे शोधा..."
                : "Search by Doc No, party name, khasra, mouza..."
            }
            leftAddon={<Search size={16} />}
            style={{ width: "100%" }}
          />
          <Button type="submit" size="md" variant="secondary">
            {lang === "mr" ? "शोधा" : "Search"}
          </Button>
        </form>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {!isArchiveMode && (
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
                {lang === "mr" ? "स्थिती:" : "Status:"}
              </span>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                options={[
                  { label: lang === "mr" ? "सर्व स्थिती (All)" : "All Statuses", value: "all" },
                  { label: lang === "mr" ? "मसुदा (Draft)" : "Draft", value: "draft" },
                  { label: lang === "mr" ? "तपासलेला (Reviewed)" : "Reviewed", value: "reviewed" },
                  { label: lang === "mr" ? "अंतिम (Finalised)" : "Finalised", value: "finalised" },
                ]}
              />
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500 }}>
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
        </div>
      </Card>

      {/* 3. Document Data Table */}
      {loading ? (
        <Skeleton height="350px" />
      ) : filteredDocs.length === 0 ? (
        <Card style={{ padding: "48px 24px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
          <FileText size={40} color="var(--text-tertiary)" />
          <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--brand-900)", margin: 0 }}>
            {lang === "mr" ? "कोणतेही दस्त सापडले नाहीत" : "No documents match criteria"}
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", margin: 0 }}>
            {lang === "mr" ? "कृपया फिल्टर बदला किंवा नवीन दस्त तयार करा." : "Try adjusting your filters or search term."}
          </p>
          <Button size="sm" variant="primary" onClick={() => onNavigate("new_draft")}>
            {lang === "mr" ? "नवीन दस्त तयार करा" : "Create New Draft"}
          </Button>
        </Card>
      ) : (
        <Card style={{ padding: "0", overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--surface-sunken)", borderBottom: "1px solid var(--line-subtle)" }}>
                  <th style={{ padding: "12px 18px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "mr" ? "दस्त क्रमांक" : "Document Number"}
                  </th>
                  <th style={{ padding: "12px 18px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "mr" ? "स्थिती" : "Status"}
                  </th>
                  <th style={{ padding: "12px 18px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "mr" ? "भाषा" : "Language"}
                  </th>
                  <th style={{ padding: "12px 18px", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {lang === "mr" ? "तयार केल्याची तारीख" : "Generated Date"}
                  </th>
                  <th style={{ padding: "12px 18px", fontWeight: 600, color: "var(--text-secondary)", textAlign: "right" }}>
                    {lang === "mr" ? "कृती" : "Actions"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map((doc) => {
                  const isFinal = doc.status === "finalised";
                  const isReviewed = doc.status === "reviewed";

                  return (
                    <tr
                      key={doc.id}
                      style={{
                        borderBottom: "1px solid var(--line-subtle)",
                        transition: "background var(--transition-fast)",
                      }}
                      className="hover:bg-[var(--surface-sunken)]"
                    >
                      <td style={{ padding: "14px 18px", fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--brand-900)" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          {isFinal && <span title="Finalised Deed"><Lock size={14} color="var(--approved-500)" /></span>}
                          <span>{doc.doc_no}</span>
                        </div>
                      </td>
                      <td style={{ padding: "14px 18px" }}>
                        <Badge
                          variant={isFinal ? "approved" : isReviewed ? "active" : "neutral"}
                          size="sm"
                          label={
                            doc.status === "draft"
                              ? lang === "mr" ? "मसुदा (Draft)" : "Draft"
                              : doc.status === "reviewed"
                              ? lang === "mr" ? "तपासलेला (Reviewed)" : "Reviewed"
                              : lang === "mr" ? "अंतिम (Finalised)" : "Finalised"
                          }
                        />
                      </td>
                      <td style={{ padding: "14px 18px" }}>
                        <Badge variant="neutral" size="sm" label={doc.language === "mr" ? "मराठी" : "English"} />
                      </td>
                      <td style={{ padding: "14px 18px", color: "var(--text-secondary)", fontSize: "0.8125rem" }}>
                        {new Date(doc.created_at).toLocaleString([], {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td style={{ padding: "14px 18px", textAlign: "right" }}>
                        <div style={{ display: "flex", gap: "6px", justifyContent: "flex-end", alignItems: "center" }}>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleViewDetail(doc)}
                            leftIcon={<Eye size={13} />}
                            title="View Metadata & Snapshot"
                          >
                            {lang === "mr" ? "तपशील" : "View"}
                          </Button>

                          {!isFinal && (
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => setReviewModalDoc(doc)}
                              leftIcon={<ShieldCheck size={13} />}
                              title="Review / Finalise"
                            >
                              {lang === "mr" ? "तपासा" : "Review"}
                            </Button>
                          )}

                          <a
                            href={doc.docx_download_url}
                            download
                            style={{ textDecoration: "none" }}
                          >
                            <Button size="sm" variant="secondary" leftIcon={<Download size={13} />}>
                              DOCX
                            </Button>
                          </a>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 4. Document Detail Modal */}
      {selectedDoc && (
        <Modal
          isOpen={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          title={`${lang === "mr" ? "दस्त तपशील" : "Document Details"}: ${selectedDoc.doc_no}`}
          maxWidth="700px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", backgroundColor: "var(--surface-sunken)", padding: "14px", borderRadius: "var(--radius-card)" }}>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Document Number:</span>
                <div style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>{selectedDoc.doc_no}</div>
              </div>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Status:</span>
                <div>
                  <Badge variant={selectedDoc.status === "finalised" ? "approved" : "neutral"} size="sm" label={selectedDoc.status} />
                </div>
              </div>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Engine Version:</span>
                <div style={{ fontFamily: "var(--font-mono)" }}>{selectedDoc.engine_version || "1.0.0"}</div>
              </div>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Language:</span>
                <div>{selectedDoc.language === "mr" ? "मराठी (Devanagari)" : "English (Western)"}</div>
              </div>
            </div>

            {selectedDoc.data_snapshot && (
              <div>
                <h4 style={{ fontSize: "0.875rem", fontWeight: 600, margin: "0 0 6px 0" }}>
                  {lang === "mr" ? "अपरिवर्तनीय डेटा स्नॅपशॉट (Immutable Snapshot)" : "Immutable Data Snapshot"}
                </h4>
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
                  {JSON.stringify(selectedDoc.data_snapshot, null, 2)}
                </pre>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "12px", borderTop: "1px solid var(--line-subtle)" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                ID: {selectedDoc.id}
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <a href={selectedDoc.docx_download_url} download style={{ textDecoration: "none" }}>
                  <Button size="sm" variant="primary" leftIcon={<Download size={14} />}>
                    Download DOCX Master
                  </Button>
                </a>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* 5. Review Center Modal */}
      {reviewModalDoc && (
        <DocumentReviewModal
          isOpen={!!reviewModalDoc}
          onClose={() => {
            setReviewModalDoc(null);
            fetchDocuments();
          }}
          documentId={reviewModalDoc.id}
          docNo={reviewModalDoc.doc_no}
          onStatusChanged={() => {
            setReviewModalDoc(null);
            fetchDocuments();
          }}
        />
      )}
    </div>
  );
};
