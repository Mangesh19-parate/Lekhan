import React, { useState, useEffect } from "react";
import { Modal, Button, EmptyState, Badge } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { useToast } from "../../shared/components/Toast";
import { DocumentReviewModal } from "../review/DocumentReviewModal";
import { Download, RefreshCw, FileCheck, ShieldCheck, ClipboardCopy, Check } from "lucide-react";

export interface DocumentSummaryItem {
  id: string;
  doc_no: string;
  status: string;
  language: string;
  engine_version: string;
  created_at: string;
  docx_download_url: string;
  pdf_download_url: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentHistoryDrawer: React.FC<Props> = ({ isOpen, onClose }) => {
  const { lang } = useI18n();
  const { toast } = useToast();

  const [documents, setDocuments] = useState<DocumentSummaryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Review modal state
  const [reviewDoc, setReviewDoc] = useState<DocumentSummaryItem | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchHistory = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch("/api/v1/documents?limit=25", {
        method: "GET",
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.items || []);
      } else {
        setErrorMsg("Failed to load history. Please ensure you are logged in.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Network error loading history.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen]);

  const handleCopyPortalSheet = async (docId: string, docNo: string) => {
    try {
      const res = await fetch(`/api/v1/documents/${docId}/portal-sheet/text`, {
        method: "GET",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Portal sheet endpoint unavailable");
      const text = await res.text();
      await navigator.clipboard.writeText(text);

      setCopiedId(docId);
      setTimeout(() => setCopiedId(null), 2500);

      toast({
        type: "success",
        title: "पोर्टल डेटा शीट कॉपी झाली! (PDE Copied)",
        description: `Sub-Registrar entry data for ${docNo} copied to clipboard.`,
      });
    } catch (err: any) {
      toast({
        type: "error",
        title: "कॉपी अयशस्वी",
        description: err.message,
      });
    }
  };

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={lang === "mr" ? "तयार केलेले दस्तऐवज (Document History)" : "Generated Documents History"}
        description={
          lang === "mr"
            ? "सर्व्हरवरील अधिकृत दस्त नोंदवही, तपासणी (Review) व PDE डेटा शीट"
            : "Authoritative server document records, legal review status & PDE sheet"
        }
        maxWidth="740px"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {/* Header refresh bar */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {documents.length} {lang === "mr" ? "दस्त आढळले" : "records found"}
            </span>
            <Button
              size="sm"
              variant="ghost"
              onClick={fetchHistory}
              isLoading={isLoading}
              leftIcon={<RefreshCw size={13} />}
            >
              {lang === "mr" ? "रिफ्रेश करा" : "Refresh"}
            </Button>
          </div>

          {errorMsg && (
            <div
              style={{
                padding: "10px 14px",
                backgroundColor: "var(--danger-tint)",
                color: "var(--danger-600)",
                borderRadius: "var(--radius-input)",
                fontSize: "0.8125rem",
              }}
            >
              {errorMsg}
            </div>
          )}

          {documents.length === 0 && !isLoading ? (
            <EmptyState
              icon={<FileCheck size={28} />}
              title={lang === "mr" ? "कोणतेही दस्त उपलब्ध नाहीत" : "No documents generated yet"}
              description={
                lang === "mr"
                  ? "तुम्ही दस्त तयार केल्यावर ते येथे कायमस्वरूपी दिसतील."
                  : "Documents you generate through the pipeline will appear here."
              }
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {documents.map((doc) => {
                const isFinalised = doc.status === "finalised";
                const isReviewed = doc.status === "reviewed";

                return (
                  <div
                    key={doc.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      flexWrap: "wrap",
                      gap: "10px",
                      padding: "14px 16px",
                      borderRadius: "var(--radius-card)",
                      backgroundColor: "var(--surface-sunken)",
                      border: "1px solid var(--line-subtle)",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontWeight: 700,
                            fontSize: "0.9375rem",
                            color: "var(--brand-900)",
                          }}
                        >
                          {doc.doc_no}
                        </span>
                        <Badge
                          variant={isFinalised ? "approved" : isReviewed ? "active" : "neutral"}
                          size="sm"
                          label={doc.status.toUpperCase()}
                        />
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                        <span>
                          {new Date(doc.created_at).toLocaleString([], {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })}
                        </span>
                        <span style={{ marginLeft: "8px", opacity: 0.7 }}>• v{doc.engine_version}</span>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      {/* Review Checklist Button */}
                      <Button
                        size="sm"
                        variant="secondary"
                        pill
                        onClick={() => setReviewDoc(doc)}
                        leftIcon={<ShieldCheck size={14} />}
                      >
                        {lang === "mr" ? "तपासणी (Review)" : "Review"}
                      </Button>

                      {/* PDE Portal Sheet Copy */}
                      <Button
                        size="sm"
                        variant="secondary"
                        pill
                        onClick={() => handleCopyPortalSheet(doc.id, doc.doc_no)}
                        leftIcon={copiedId === doc.id ? <Check size={14} /> : <ClipboardCopy size={14} />}
                        title="Copy Sub-Registrar Portal Entry Sheet"
                      >
                        {copiedId === doc.id ? "Copied" : "PDE Sheet"}
                      </Button>

                      {/* DOCX Download */}
                      <a href={doc.docx_download_url} download style={{ textDecoration: "none" }}>
                        <Button size="sm" variant="primary" pill leftIcon={<Download size={13} />}>
                          DOCX
                        </Button>
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Modal>

      {/* Review Modal */}
      {reviewDoc && (
        <DocumentReviewModal
          isOpen={!!reviewDoc}
          onClose={() => setReviewDoc(null)}
          documentId={reviewDoc.id}
          docNo={reviewDoc.doc_no}
          onStatusChanged={fetchHistory}
        />
      )}
    </>
  );
};
