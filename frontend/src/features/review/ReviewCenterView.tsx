import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Skeleton } from "../../shared/components";
import { DocumentReviewModal } from "./DocumentReviewModal";
import {
  ShieldCheck,
  CheckCircle2,
  Clock,
  Lock,
  AlertTriangle,
  RotateCcw,
  FileText,
  UserCheck,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

interface ReviewCenterViewProps {
  onNavigate: (viewId: string) => void;
}

export const ReviewCenterView: React.FC<ReviewCenterViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const res = await api.listDocuments({ limit: 100 });
      setDocuments(res.items || []);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const pendingReviewDocs = documents.filter((d) => d.status === "draft");
  const reviewedDocs = documents.filter((d) => d.status === "reviewed");
  const finalisedDocs = documents.filter((d) => d.status === "finalised");

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "दस्त तपासणी व मंजुरी केंद्र (Review & Approval Center)" : "Review & Approval Center"}
            </h1>
            <Badge variant="approved" size="md" label="Advocate Sign-off" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "वकील तपासणी चेकलिस्ट, पक्षकार ओळख पडताळणी, चतुःसीमा व अंतिम कुलूपबंद मंजुरी प्रवाह."
              : "Advocate checklist sign-off, identity verification, boundary checks, and finalization."}
          </p>
        </div>

        <Button size="sm" variant="secondary" onClick={fetchQueue} leftIcon={<RefreshCw size={14} />}>
          {lang === "mr" ? "रिफ्रेश" : "Refresh"}
        </Button>
      </div>

      {/* 2. Permanent Legal Disclaimer */}
      <div
        style={{
          padding: "16px 20px",
          borderRadius: "var(--radius-card)",
          backgroundColor: "var(--approved-100)",
          border: "1px solid var(--approved-500)",
          display: "flex",
          gap: "14px",
          alignItems: "center",
        }}
      >
        <ShieldCheck size={24} color="var(--brand-600)" style={{ flexShrink: 0 }} />
        <div style={{ fontSize: "0.875rem", lineHeight: 1.5, color: "var(--text-primary)" }}>
          <strong>{lang === "mr" ? "वैधानिक अस्वीकृती (Statutory Disclaimer):" : "Mandatory Statutory Disclaimer:"}</strong>{" "}
          {lang === "mr"
            ? "प्रणालीद्वारे तयार केलेले दस्त केवळ मसुदे आहेत. निष्पादन अथवा नोंदणीपूर्वी पात्र कायदेतज्ज्ञाकडून (Advocate) संपूर्ण तपासणी करणे अनिवार्य आहे. हे सॉफ्टवेअर कायदेशीर सल्ला प्रदान करत नाही."
            : "Generated documents are drafts and require rigorous review by a qualified legal professional before execution or registration. This software does not provide legal advice."}
        </div>
      </div>

      {/* 3. Review Queue Metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
        <Card style={{ padding: "18px", borderLeft: "4px solid #D97706" }}>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 600 }}>
            {lang === "mr" ? "तपासणी प्रलंबित" : "Awaiting Review"}
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#D97706", marginTop: "4px" }}>
            {pendingReviewDocs.length}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "वकिलांचे स्वाक्षरी बाकी" : "Require checklist confirmation"}
          </div>
        </Card>

        <Card style={{ padding: "18px", borderLeft: "4px solid var(--brand-500)" }}>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 600 }}>
            {lang === "mr" ? "तपासणी पूर्ण" : "Reviewed (Pending Seal)"}
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--brand-500)", marginTop: "4px" }}>
            {reviewedDocs.length}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "अंतिम कुलूपबंद करण्यास सज्ज" : "Ready for finalisation lock"}
          </div>
        </Card>

        <Card style={{ padding: "18px", borderLeft: "4px solid var(--approved-500)" }}>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 600 }}>
            {lang === "mr" ? "अंतिम केलेले दस्त" : "Finalised Deeds"}
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--brand-900)", marginTop: "4px" }}>
            {finalisedDocs.length}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
            {lang === "mr" ? "अपरिवर्तनीय व कुलूपबंद" : "Immutable registration copies"}
          </div>
        </Card>
      </div>

      {/* 4. Active Review Queue Table */}
      <Card style={{ padding: "20px" }}>
        <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--brand-900)", margin: "0 0 16px 0" }}>
          {lang === "mr" ? "तपासणीसाठी प्रलंबित दस्त (Pending Review Queue)" : "Pending Review Queue"}
        </h3>

        {loading ? (
          <Skeleton height="200px" />
        ) : pendingReviewDocs.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
            <CheckCircle2 size={36} color="var(--brand-500)" style={{ margin: "0 auto 10px auto" }} />
            <div style={{ fontWeight: 600 }}>
              {lang === "mr" ? "सर्व दस्त तपासले गेले आहेत!" : "All drafts are reviewed!"}
            </div>
            <div style={{ fontSize: "0.8125rem", marginTop: "4px" }}>
              {lang === "mr" ? "सध्या तपासणीसाठी कोणताही दस्त प्रलंबित नाही." : "No documents currently pending advocate sign-off."}
            </div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--surface-sunken)", borderBottom: "1px solid var(--line-subtle)" }}>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>{lang === "mr" ? "दस्त क्र." : "Doc Number"}</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>{lang === "mr" ? "भाषा" : "Language"}</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>{lang === "mr" ? "तारीख" : "Generated At"}</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600, textAlign: "right" }}>{lang === "mr" ? "कृती" : "Action"}</th>
                </tr>
              </thead>
              <tbody>
                {pendingReviewDocs.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: "1px solid var(--line-subtle)" }}>
                    <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                      {doc.doc_no}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <Badge variant="neutral" size="sm" label={doc.language === "mr" ? "मराठी" : "English"} />
                    </td>
                    <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "right" }}>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => setSelectedDoc(doc)}
                        leftIcon={<ShieldCheck size={14} />}
                      >
                        {lang === "mr" ? "आता तपासा (Start Review)" : "Start Review"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* 5. Recently Reviewed & Ready for Finalisation */}
      {reviewedDocs.length > 0 && (
        <Card style={{ padding: "20px" }}>
          <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--brand-900)", margin: "0 0 16px 0" }}>
            {lang === "mr" ? "तपासलेले व अंतिम मंजुरीसाठी सज्ज (Ready for Finalisation)" : "Reviewed Documents Ready for Finalisation"}
          </h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--surface-sunken)", borderBottom: "1px solid var(--line-subtle)" }}>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>{lang === "mr" ? "दस्त क्र." : "Doc Number"}</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600 }}>{lang === "mr" ? "स्थिती" : "Status"}</th>
                  <th style={{ padding: "12px 16px", fontWeight: 600, textAlign: "right" }}>{lang === "mr" ? "कृती" : "Action"}</th>
                </tr>
              </thead>
              <tbody>
                {reviewedDocs.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: "1px solid var(--line-subtle)" }}>
                    <td style={{ padding: "12px 16px", fontFamily: "var(--font-mono)", fontWeight: 600 }}>
                      {doc.doc_no}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <Badge variant="active" size="sm" label="Reviewed" />
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "right" }}>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => setSelectedDoc(doc)}
                        leftIcon={<Lock size={14} />}
                      >
                        {lang === "mr" ? "अंतिम करा (Finalise)" : "Finalise & Lock"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Review Modal Dialog */}
      {selectedDoc && (
        <DocumentReviewModal
          isOpen={!!selectedDoc}
          onClose={() => {
            setSelectedDoc(null);
            fetchQueue();
          }}
          documentId={selectedDoc.id}
          docNo={selectedDoc.doc_no}
          onStatusChanged={() => {
            setSelectedDoc(null);
            fetchQueue();
          }}
        />
      )}
    </div>
  );
};
