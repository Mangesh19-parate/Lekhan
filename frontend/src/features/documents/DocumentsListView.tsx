import React, { useEffect, useState, useMemo } from "react";
import { useI18n } from "../../shared/i18n";
import {
  api,
  type DocumentSummaryItem,
  type DocumentDetailResponse,
  type ProvenanceVerificationResponse,
} from "../../shared/api";
import { Button, Badge, Card, Input, Select, Modal, Skeleton, Table, type Column } from "../../shared/components";
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
  CheckCircle2,
  AlertTriangle,
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
  const [documents, setDocuments] = useState<DocumentSummaryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>(
    isArchiveMode ? "finalised" : initialStatusFilter || "all"
  );
  const [langFilter, setLangFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"created_at" | "doc_no">("created_at");
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetailResponse | DocumentSummaryItem | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [reviewModalDoc, setReviewModalDoc] = useState<DocumentSummaryItem | null>(null);
  const [verificationResult, setVerificationResult] = useState<ProvenanceVerificationResponse | null>(null);
  const [verifyingDocId, setVerifyingDocId] = useState<string | null>(null);

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

  const handleViewDetail = async (docSummary: DocumentSummaryItem) => {
    try {
      const fullDoc = await api.getDocument(docSummary.id);
      setSelectedDoc(fullDoc);
      setDetailModalOpen(true);
    } catch {
      setSelectedDoc(docSummary);
      setDetailModalOpen(true);
    }
  };

  const handleVerifyDoc = async (docId: string) => {
    setVerifyingDocId(docId);
    try {
      const res = await api.verifyDocument(docId);
      setVerificationResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification failed";
      alert("Cryptographic verification failed: " + msg);
    } finally {
      setVerifyingDocId(null);
    }
  };

  const columns: Column<DocumentSummaryItem>[] = [
    {
      key: "doc_no",
      header: lang === "mr" ? "दस्त क्रमांक" : "Document Number",
      sortable: true,
      render: (doc) => {
        const isFinal = doc.status === "finalised";
        return (
          <div className="flex items-center gap-2 font-mono font-semibold text-brand-900">
            {isFinal && <span title="Finalised Deed"><Lock size={14} className="text-approved-500" /></span>}
            <span>{doc.doc_no}</span>
          </div>
        );
      },
    },
    {
      key: "status",
      header: lang === "mr" ? "स्थिती" : "Status",
      sortable: true,
      render: (doc) => {
        const isFinal = doc.status === "finalised";
        const isReviewed = doc.status === "reviewed";
        return (
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
        );
      },
    },
    {
      key: "language",
      header: lang === "mr" ? "भाषा" : "Language",
      sortable: true,
      render: (doc) => (
        <Badge variant="neutral" size="sm" label={doc.language === "mr" ? "मराठी" : "English"} />
      ),
    },
    {
      key: "created_at",
      header: lang === "mr" ? "तयार केल्याची तारीख" : "Generated Date",
      sortable: true,
      render: (doc) => (
        <span className="text-xs text-text-secondary">
          {new Date(doc.created_at).toLocaleString([], {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      ),
    },
    {
      key: "actions",
      header: lang === "mr" ? "कृती" : "Actions",
      align: "right",
      render: (doc) => {
        const isFinal = doc.status === "finalised";
        return (
          <div className="flex items-center justify-end gap-1.5 flex-wrap">
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

            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleVerifyDoc(doc.id)}
              isLoading={verifyingDocId === doc.id}
              leftIcon={<ShieldCheck size={13} />}
              title="Cryptographically verify provenance and SHA-256 seal"
            >
              {lang === "mr" ? "पडताळा" : "Verify"}
            </Button>

            <a
              href={doc.docx_download_url}
              download
              className="no-underline inline-flex"
              title="Download editable DOCX master deed"
            >
              <Button size="sm" variant="secondary" leftIcon={<Download size={13} />}>
                DOCX
              </Button>
            </a>

            <a
              href={doc.pdf_download_url || api.getDocumentPdfUrl(doc.id)}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="no-underline inline-flex"
              title="Download PDF convenience copy (ADR 010)"
            >
              <Button size="sm" variant="secondary" leftIcon={<Download size={13} />}>
                PDF
              </Button>
            </a>
          </div>
        );
      },
    },
  ];

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0, fontFamily: "var(--font-heading)" }}>
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
      <Table<DocumentSummaryItem>
        columns={columns}
        data={filteredDocs}
        keyExtractor={(doc) => doc.id}
        isLoading={loading}
        enablePagination={true}
        pageSize={10}
        enableSearch={true}
        searchPlaceholder={
          lang === "mr" ? "दस्त किंवा तपशील शोधा..." : "Filter deeds in register..."
        }
        emptyMessage={
          lang === "mr"
            ? "कोणतेही दस्त उपलब्ध नाहीत. नवीन मसुदा तयार करा."
            : "No documents match criteria. Create a new draft."
        }
        emptyAction={
          <Button size="sm" variant="primary" onClick={() => onNavigate("new_draft")}>
            {lang === "mr" ? "नवीन दस्त तयार करा" : "Create New Draft"}
          </Button>
        }
      />

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
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleVerifyDoc(selectedDoc.id)}
                  leftIcon={<ShieldCheck size={14} />}
                >
                  Verify Integrity
                </Button>
                <a href={selectedDoc.docx_download_url} download style={{ textDecoration: "none" }}>
                  <Button size="sm" variant="primary" leftIcon={<Download size={14} />}>
                    DOCX Master
                  </Button>
                </a>
                <a
                  href={selectedDoc.pdf_download_url || api.getDocumentPdfUrl(selectedDoc.id)}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ textDecoration: "none" }}
                >
                  <Button size="sm" variant="secondary" leftIcon={<Download size={14} />}>
                    PDF Copy
                  </Button>
                </a>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* 5. Provenance Verification Modal */}
      {verificationResult && (
        <Modal
          isOpen={!!verificationResult}
          onClose={() => setVerificationResult(null)}
          title="दस्तऐवज क्रिप्टोग्राफिक पडताळणी निकाल (Cryptographic Provenance)"
          maxWidth="640px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div
              style={{
                padding: "14px 16px",
                borderRadius: "var(--radius-card)",
                backgroundColor: verificationResult.valid && !verificationResult.tampered ? "var(--brand-100)" : "#FEE2E2",
                border: `1px solid ${verificationResult.valid && !verificationResult.tampered ? "var(--brand-500)" : "#FCA5A5"}`,
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              {verificationResult.valid && !verificationResult.tampered ? (
                <CheckCircle2 size={24} color="var(--brand-600)" />
              ) : (
                <AlertTriangle size={24} color="var(--danger-600)" />
              )}
              <div>
                <div style={{ fontWeight: 700, fontSize: "0.9375rem", color: verificationResult.valid && !verificationResult.tampered ? "var(--brand-900)" : "#991B1B" }}>
                  {verificationResult.valid && !verificationResult.tampered
                    ? "Cryptographic Provenance Verified: Document is authentic & untampered."
                    : "Provenance Verification Failed: Document seal invalid or tampered!"}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                  {verificationResult.message || "Custom XML part checked against SHA-256 manifest hash."}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.8125rem", backgroundColor: "var(--surface-sunken)", padding: "14px", borderRadius: "var(--radius-card)" }}>
              <div><strong>Document ID:</strong> {verificationResult.document_id || "N/A"}</div>
              <div><strong>Template Version ID:</strong> {verificationResult.template_version_id || "N/A"}</div>
              <div><strong>Template SHA-256:</strong> <span style={{ fontFamily: "var(--font-mono)" }}>{verificationResult.template_sha256?.slice(0, 24)}...</span></div>
              <div><strong>Actual Document Hash:</strong> <span style={{ fontFamily: "var(--font-mono)" }}>{verificationResult.actual_document_hash?.slice(0, 24)}...</span></div>
              <div><strong>Generated At:</strong> {verificationResult.generated_at ? new Date(verificationResult.generated_at).toLocaleString() : "N/A"}</div>
              <div><strong>Verified At:</strong> {verificationResult.verified_at ? new Date(verificationResult.verified_at).toLocaleString() : "N/A"}</div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <Button size="sm" variant="secondary" onClick={() => setVerificationResult(null)}>
                Close
              </Button>
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
