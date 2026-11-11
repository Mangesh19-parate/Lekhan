import React, { useState, useEffect } from "react";
import { Modal, Button, Badge } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { useToast } from "../../shared/components/Toast";
import { useAuth } from "../../shared/auth/AuthContext";
import { ShieldCheck, CheckSquare, Square, Lock, AlertTriangle, FileText } from "lucide-react";

interface ReviewMetadata {
  status: "draft" | "reviewed" | "finalised";
  disclaimer: string;
  checklist?: {
    parties_verified: boolean;
    property_schedule_verified: boolean;
    consideration_and_payment_verified: boolean;
    no_unfilled_blanks: boolean;
    reviewer_notes?: string;
  };
  reviewed_by?: string;
  reviewed_at?: string;
  finalised_by?: string;
  finalised_at?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  docNo: string;
  onStatusChanged?: () => void;
}

export const DocumentReviewModal: React.FC<Props> = ({
  isOpen,
  onClose,
  documentId,
  docNo,
  onStatusChanged,
}) => {
  const { lang } = useI18n();
  const { toast } = useToast();
  const { csrfToken } = useAuth();

  const [reviewMeta, setReviewMeta] = useState<ReviewMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Checklist state
  const [partiesVerified, setPartiesVerified] = useState(false);
  const [propertyVerified, setPropertyVerified] = useState(false);
  const [considerationVerified, setConsiderationVerified] = useState(false);
  const [noBlanksVerified, setNoBlanksVerified] = useState(false);
  const [notes, setNotes] = useState("");

  const fetchReviewStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/v1/documents/${documentId}/review`, {
        method: "GET",
        credentials: "include",
      });
      if (res.ok) {
        const data: ReviewMetadata = await res.json();
        setReviewMeta(data);
        if (data.checklist) {
          setPartiesVerified(data.checklist.parties_verified);
          setPropertyVerified(data.checklist.property_schedule_verified);
          setConsiderationVerified(data.checklist.consideration_and_payment_verified);
          setNoBlanksVerified(data.checklist.no_unfilled_blanks);
          setNotes(data.checklist.reviewer_notes || "");
        }
      }
    } catch {
      // Ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && documentId) {
      fetchReviewStatus();
    }
  }, [isOpen, documentId]);

  const allChecklistItemsChecked =
    partiesVerified && propertyVerified && considerationVerified && noBlanksVerified;

  const handleMarkReviewed = async () => {
    if (!allChecklistItemsChecked) {
      toast({
        type: "error",
        title: "तपासणी अपूर्ण (Checklist Incomplete)",
        description: "All 4 statutory checklist items must be verified.",
      });
      return;
    }

    setSubmitting(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (csrfToken) headers["X-CSRF-Token"] = csrfToken;

      const res = await fetch(`/api/v1/documents/${documentId}/review`, {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({
          parties_verified: partiesVerified,
          property_schedule_verified: propertyVerified,
          consideration_and_payment_verified: considerationVerified,
          no_unfilled_blanks: noBlanksVerified,
          reviewer_notes: notes.trim() || undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Review submission failed.");
      }

      toast({
        type: "success",
        title: "दस्त तपासणी पूर्ण (Marked as Reviewed)",
        description: `Document ${docNo} is now in Reviewed status.`,
      });

      await fetchReviewStatus();
      if (onStatusChanged) onStatusChanged();
    } catch (err: any) {
      toast({
        type: "error",
        title: "त्रुटी",
        description: err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinalise = async () => {
    if (!confirm(lang === "mr" ? "दस्त अंतिम (Finalise) करायचा आहे का? यानंतर यात कोणतेही बदल करता येणार नाहीत." : "Finalise this document? Once finalised, it becomes permanently immutable.")) {
      return;
    }

    setSubmitting(true);
    try {
      const headers: Record<string, string> = {};
      if (csrfToken) headers["X-CSRF-Token"] = csrfToken;

      const res = await fetch(`/api/v1/documents/${documentId}/finalise`, {
        method: "POST",
        headers,
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Finalisation failed.");
      }

      toast({
        type: "success",
        title: "दस्त अंतिम केला (Finalised)",
        description: `Document ${docNo} is locked as Finalised.`,
      });

      await fetchReviewStatus();
      if (onStatusChanged) onStatusChanged();
    } catch (err: any) {
      toast({
        type: "error",
        title: "त्रुटी",
        description: err.message,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const isFinalised = reviewMeta?.status === "finalised";
  const isReviewed = reviewMeta?.status === "reviewed";

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={lang === "mr" ? "कायदेशीर तपासणी व अंतिम टप्पा (Review & Finalisation)" : "Document Review Checklist & Finalisation"}
      description={`Matter Deed: ${docNo}`}
      maxWidth="580px"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Current status bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 16px",
            backgroundColor: "var(--surface-sunken)",
            borderRadius: "var(--radius-input)",
          }}
        >
          <div style={{ fontSize: "0.875rem", fontWeight: 600 }}>
            {lang === "mr" ? "सध्याची स्थिती:" : "Review Status:"}
          </div>
          <Badge
            variant={isFinalised ? "approved" : isReviewed ? "active" : "draft"}
            label={reviewMeta?.status ? reviewMeta.status.toUpperCase() : "DRAFT"}
          />
        </div>

        {/* Mandatory Statutory Disclaimer Strip */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            padding: "12px 14px",
            backgroundColor: "var(--warning-tint)",
            border: "1px solid var(--warning-border)",
            borderRadius: "var(--radius-input)",
            fontSize: "0.75rem",
            color: "var(--warning-600)",
            lineHeight: 1.5,
          }}
        >
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <span>
            {reviewMeta?.disclaimer ||
              (lang === "mr"
                ? "सूचना: लेखन हे विधी व्यावसायिकांसाठी मसुदा साहाय्यक आहे. हा मसुदा कायदेशीर सल्ला नसून वकिलांनी स्वतः तपासून अंतिम करणे आवश्यक आहे."
                : "Notice: Lekhan is a drafting assistant for legal professionals. This draft must be independently reviewed by an advocate.")}
          </span>
        </div>

        {/* Mandatory 4-Point Checklist */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--brand-900)" }}>
            {lang === "mr" ? "अनिवार्य कायदेशीर तपासणी सूची (Mandatory Checklist):" : "Advocate Verification Checklist:"}
          </div>

          <label
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "10px 12px",
              borderRadius: "var(--radius-input)",
              backgroundColor: "var(--surface-subtle)",
              cursor: isFinalised ? "default" : "pointer",
            }}
          >
            <input
              type="checkbox"
              disabled={isFinalised}
              checked={partiesVerified}
              onChange={(e) => setPartiesVerified(e.target.checked)}
              style={{ marginTop: "3px" }}
            />
            <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
              {lang === "mr"
                ? "१. पक्षकारांचे संपूर्ण नाव, वय, पत्ता व पॅन अधिकृत ओळखपत्रांनुसार पडताळले."
                : "1. Names, ages, addresses, and PAN of parties verified against official IDs."}
            </span>
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "10px 12px",
              borderRadius: "var(--radius-input)",
              backgroundColor: "var(--surface-subtle)",
              cursor: isFinalised ? "default" : "pointer",
            }}
          >
            <input
              type="checkbox"
              disabled={isFinalised}
              checked={propertyVerified}
              onChange={(e) => setPropertyVerified(e.target.checked)}
              style={{ marginTop: "3px" }}
            />
            <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
              {lang === "mr"
                ? "२. मिळकतीचे वर्णन (खसरा/भूखंड क्र., क्षेत्रफळ, चतुःसीमा) महसूल नोंदींनुसार पडताळले."
                : "2. Property Khasra/Plot number, area (sqm/sqft), and boundaries verified against revenue record."}
            </span>
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "10px 12px",
              borderRadius: "var(--radius-input)",
              backgroundColor: "var(--surface-subtle)",
              cursor: isFinalised ? "default" : "pointer",
            }}
          >
            <input
              type="checkbox"
              disabled={isFinalised}
              checked={considerationVerified}
              onChange={(e) => setConsiderationVerified(e.target.checked)}
              style={{ marginTop: "3px" }}
            />
            <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
              {lang === "mr"
                ? "३. एकूण मोबदला, बयाणा रक्कम व धनादेश/आरटीजीएस क्रमांक योग्य असल्याची खात्री केली."
                : "3. Total consideration, earnest advance, and payment instrument reference numbers confirmed."}
            </span>
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              padding: "10px 12px",
              borderRadius: "var(--radius-input)",
              backgroundColor: "var(--surface-subtle)",
              cursor: isFinalised ? "default" : "pointer",
            }}
          >
            <input
              type="checkbox"
              disabled={isFinalised}
              checked={noBlanksVerified}
              onChange={(e) => setNoBlanksVerified(e.target.checked)}
              style={{ marginTop: "3px" }}
            />
            <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)" }}>
              {lang === "mr"
                ? "४. मसुद्यामध्ये कोणतीही रिकामा कंस, प्रश्नचिन्ह अथवा भरावयाची जागा शिल्लक नाही."
                : "4. Confirmed zero unfilled bracketed blanks or unrendered template tags in document text."}
            </span>
          </label>
        </div>

        {/* Notes */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {lang === "mr" ? "वकिलांच्या नोंदी (Reviewer Notes):" : "Advocate Notes:"}
          </label>
          <textarea
            disabled={isFinalised}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Title clearance certificate verified; No litigation pending."
            rows={3}
            style={{
              width: "100%",
              padding: "8px 12px",
              fontSize: "0.8125rem",
              fontFamily: "var(--font-ui)",
              borderRadius: "var(--radius-input)",
              border: "1px solid var(--line-medium)",
              backgroundColor: isFinalised ? "var(--surface-sunken)" : "var(--surface-card)",
              color: "var(--text-primary)",
              resize: "vertical",
            }}
          />
        </div>

        {/* Action Buttons */}
        {!isFinalised && (
          <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end", marginTop: "12px" }}>
            <Button
              type="button"
              variant="secondary"
              pill
              isLoading={submitting}
              onClick={handleMarkReviewed}
              disabled={!allChecklistItemsChecked}
              leftIcon={<ShieldCheck size={16} />}
            >
              {lang === "mr" ? "तपासणी पूर्ण (Mark as Reviewed)" : "Mark as Reviewed"}
            </Button>

            {isReviewed && (
              <Button
                type="button"
                variant="primary"
                pill
                isLoading={submitting}
                onClick={handleFinalise}
                leftIcon={<Lock size={16} />}
              >
                {lang === "mr" ? "दस्त अंतिम करा (Finalise)" : "Finalise Document"}
              </Button>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};
