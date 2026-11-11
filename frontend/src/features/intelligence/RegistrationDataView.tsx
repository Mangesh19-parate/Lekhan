import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
import { Button, Badge, Card, Select, Skeleton } from "../../shared/components";
import {
  FileText,
  Copy,
  Download,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
  Landmark,
  Users,
} from "lucide-react";

interface RegistrationDataViewProps {
  onNavigate: (viewId: string) => void;
}

export const RegistrationDataView: React.FC<RegistrationDataViewProps> = ({ onNavigate }) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [portalSheet, setPortalSheet] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchDocsAndSheet = async () => {
    setLoading(true);
    try {
      const res = await api.listDocuments({ limit: 50 });
      const items = res.items || [];
      setDocuments(items);
      if (items.length > 0) {
        const firstId = items[0].id;
        setSelectedDocId(firstId);
        loadPortalSheet(firstId);
      }
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPortalSheet = async (docId: string) => {
    if (!docId) return;
    try {
      const sheet = await api.getPortalSheet(docId);
      setPortalSheet(sheet);
    } catch (err: any) {
      setPortalSheet(null);
    }
  };

  useEffect(() => {
    fetchDocsAndSheet();
  }, []);

  const handleCopyText = () => {
    if (portalSheet?.copy_paste_text) {
      navigator.clipboard.writeText(portalSheet.copy_paste_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "नोंदणी पोर्टल डेटा शीट (Registration Portal Data Prep)" : "Registration Portal Data Preparation"}
            </h1>
            <Badge variant="approved" size="md" label="Maharashtra IGR / PDE Format" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "महाराष्ट्र नोंदणी व मुद्रांक विभागाच्या (IGR Maharashtra / PDE) पोर्टलसाठी एका क्लिकवर कॉपी-पेस्ट डेटा."
              : "Structured copy-paste data sheet formatted for Maharashtra IGR public data entry portal."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          {selectedDocId && (
            <a
              href={`/api/v1/documents/${selectedDocId}/portal-sheet/text`}
              download={`Portal_Sheet_${selectedDocId}.txt`}
              style={{ textDecoration: "none" }}
            >
              <Button size="sm" variant="secondary" leftIcon={<Download size={14} />}>
                Download .TXT Sheet
              </Button>
            </a>
          )}
          <Button size="sm" variant="primary" onClick={handleCopyText} leftIcon={<Copy size={14} />}>
            {copied ? (lang === "mr" ? "कॉपी झाले!" : "Copied to Clipboard!") : (lang === "mr" ? "सर्व डेटा कॉपी करा" : "Copy Portal Text")}
          </Button>
        </div>
      </div>

      {/* 2. Select Document */}
      <Card style={{ padding: "16px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>
            {lang === "mr" ? "दस्त निवडा:" : "Select Document:"}
          </span>
          <Select
            value={selectedDocId}
            onChange={(e) => {
              setSelectedDocId(e.target.value);
              loadPortalSheet(e.target.value);
            }}
            options={documents.map((d) => ({
              label: `${d.doc_no} (${d.language === "mr" ? "मराठी" : "EN"} - ${new Date(d.created_at).toLocaleDateString()})`,
              value: d.id,
            }))}
          />
        </div>

        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          {lang === "mr" ? "पोर्टलवर पुन्हा टाइप न करता डेटा भरा." : "Prevents manual retyping errors in IGR portal."}
        </span>
      </Card>

      {/* 3. Portal Data Display */}
      {loading ? (
        <Skeleton height="350px" />
      ) : !portalSheet ? (
        <Card style={{ padding: "40px", textAlign: "center" }}>
          <FileText size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
          <div>{lang === "mr" ? "दस्त डेटा उपलब्ध नाही." : "No portal sheet available for this document."}</div>
        </Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "20px" }}>
          {/* Left: Structured Data View */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Property Schedule */}
            <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--brand-900)", fontWeight: 700 }}>
                <Landmark size={18} />
                <span>{lang === "mr" ? "मिळकतीचे वर्णन (Property Schedule)" : "Property Schedule for PDE"}</span>
              </div>
              <div style={{ backgroundColor: "var(--surface-sunken)", padding: "12px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "6px" }}>
                <div><strong>District:</strong> Nagpur (नागपूर)</div>
                <div><strong>Taluka:</strong> Nagpur Urban / Rural</div>
                <div><strong>Mouza:</strong> {portalSheet.property?.mouza || "सोनेगाव (Sonegaon)"}</div>
                <div><strong>Survey / Khasra No:</strong> {portalSheet.property?.khasra_no || "45/2"}</div>
                <div><strong>Plot No:</strong> {portalSheet.property?.plot_no || "12"}</div>
                <div><strong>Area:</strong> {portalSheet.property?.area_sqm || 150} Sq. Metres ({((portalSheet.property?.area_sqm || 150) * 10.7639104).toFixed(2)} Sq. Feet)</div>
                {portalSheet.property?.boundaries && (
                  <div style={{ marginTop: "4px" }}>
                    <strong>Boundaries:</strong> E: {portalSheet.property.boundaries.east}, W: {portalSheet.property.boundaries.west}, N: {portalSheet.property.boundaries.north}, S: {portalSheet.property.boundaries.south}
                  </div>
                )}
              </div>
            </Card>

            {/* Parties Schedule */}
            <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--brand-900)", fontWeight: 700 }}>
                <Users size={18} />
                <span>{lang === "mr" ? "पक्षकार यादी (Parties Details)" : "Parties Registration Details"}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem" }}>
                  <div style={{ fontWeight: 600, color: "var(--brand-600)" }}>विक्रेता (Seller / Transferor):</div>
                  <div>आनंद बळवंत जोशी, वय: 52, पॅन: ABCDE1234F</div>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>फ्लॅट क्र. 201, धरमपेठ, नागपूर</div>
                </div>
                <div style={{ backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem" }}>
                  <div style={{ fontWeight: 600, color: "var(--brand-600)" }}>खरेदीदार (Purchaser / Transferee):</div>
                  <div>सुरेश रामराव पाटील, वय: 41, पॅन: FGHIJ5678K</div>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>प्लॉट क्र. 45, त्रिमूर्ती नगर, नागपूर</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right: Direct Plain-Text Copy Sheet */}
          <Card style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--brand-900)" }}>
                {lang === "mr" ? "कॉपी-पेस्ट मजकूर (Plain Text Copy)" : "Portal Ready Plain Text"}
              </h3>
              <Button size="sm" variant="secondary" onClick={handleCopyText} leftIcon={<Copy size={13} />}>
                {copied ? "Copied!" : "Copy All"}
              </Button>
            </div>

            <textarea
              readOnly
              value={portalSheet.copy_paste_text}
              style={{
                width: "100%",
                height: "400px",
                fontFamily: "var(--font-mono)",
                fontSize: "0.75rem",
                padding: "12px",
                borderRadius: "var(--radius-input)",
                border: "1px solid var(--line-subtle)",
                backgroundColor: "var(--surface-sunken)",
                resize: "none",
                lineHeight: 1.5,
              }}
            />
          </Card>
        </div>
      )}
    </div>
  );
};

