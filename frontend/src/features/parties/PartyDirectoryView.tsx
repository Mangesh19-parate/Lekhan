import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, type PartyItem, type PartyDuplicateMatch } from "../../shared/api";
import { Button, Badge, Card, Input, Modal, Skeleton } from "../../shared/components";
import {
  Users,
  Search,
  Plus,
  UserCheck,
  Building2,
  FileText,
  MapPin,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  Copy,
  CheckCircle2,
} from "lucide-react";

interface PartyDirectoryViewProps {
  onNavigate: (viewId: string) => void;
  onReuseParty?: (partyData: Record<string, unknown>) => void;
}

export const PartyDirectoryView: React.FC<PartyDirectoryViewProps> = ({
  onNavigate,
  onReuseParty,
}) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [parties, setParties] = useState<PartyItem[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  // Duplicates modal
  const [duplicatesModalOpen, setDuplicatesModalOpen] = useState(false);
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);
  const [duplicateMatches, setDuplicateMatches] = useState<PartyDuplicateMatch[]>([]);

  // Form state for creating party
  const [kind, setKind] = useState("individual");
  const [nameMr, setNameMr] = useState("");
  const [nameEn, setNameEn] = useState("");
  const [gender, setGender] = useState("male");
  const [age, setAge] = useState(45);
  const [occupation, setOccupation] = useState("व्यवसाय (Business)");
  const [address, setAddress] = useState("नागपूर (Nagpur)");
  const [pan, setPan] = useState("ABCDE1234F");

  const handleSearch = async (searchQ?: string) => {
    const q = searchQ !== undefined ? searchQ : query;
    setLoading(true);
    try {
      const res = await api.searchParties(q && q.length >= 2 ? q : "जोशी");
      setParties(res || []);
    } catch {
      setParties([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch("");
  }, []);

  const handleCheckDuplicates = async () => {
    setCheckingDuplicates(true);
    setDuplicatesModalOpen(true);
    try {
      const matches = await api.detectDuplicateParties({
        name: query.trim() || undefined,
        threshold: 0.85,
      });
      setDuplicateMatches(matches);
    } catch {
      setDuplicateMatches([]);
    } finally {
      setCheckingDuplicates(false);
    }
  };

  const handleReuse = async (partyId: string, partyObj: PartyItem) => {
    try {
      await api.reuseParty(partyId);
    } catch {
      // Offline or local fallback
    }
    if (onReuseParty) {
      const attrs = partyObj.attrs || {};
      const nameDisp = partyObj.name_mr || partyObj.name_en || (attrs.names as Record<string, string>)?.mr || "Unknown";
      onReuseParty({
        full_name: nameDisp,
        full_name_mr: partyObj.name_mr,
        full_name_en: partyObj.name_en,
        gender: attrs.gender || "male",
        age: (attrs.age_or_dob as Record<string, number>)?.age || 40,
        occupation: (attrs.occupations as Record<string, string>)?.mr || "व्यवसाय",
        address: (attrs.addresses as Record<string, string>)?.mr || "नागपूर",
        pan: partyObj.pan || "ABCDE1234F",
      });
    }
    onNavigate("new_draft");
  };

  const handleCreateParty = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createParty({
        kind,
        names: { mr: nameMr, en: nameEn },
        gender,
        age_or_dob: { age },
        occupations: { mr: occupation, en: occupation },
        addresses: { mr: address, en: address },
        pan_masked: pan,
      });
      setCreateModalOpen(false);
      handleSearch(nameMr || nameEn);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create party";
      alert("Failed to create party: " + msg);
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "पक्षकार सूची व पुनर्वापर (Party Directory)" : "Party Directory"}
            </h1>
            <Badge variant="approved" size="md" label="Trigram Search Enabled" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "मराठी व इंग्रजी त्रिग्राम शोध, पॅन माहिती, आणि भूतकाळातील दस्त न बदलता सुरक्षित पुनर्वापर."
              : "Bilingual Devanagari/Latin trigram search with immutable snapshot isolation on reuse."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleCheckDuplicates}
            isLoading={checkingDuplicates}
            leftIcon={<Copy size={15} />}
          >
            {lang === "mr" ? "डुप्लिकेट शोधा (Detect Duplicates)" : "Detect Duplicates"}
          </Button>

          <Button size="sm" variant="primary" onClick={() => setCreateModalOpen(true)} leftIcon={<Plus size={15} />}>
            {lang === "mr" ? "नवीन पक्षकार जोडा" : "Add New Party"}
          </Button>
        </div>
      </div>

      {/* 2. Search Bar */}
      <Card style={{ padding: "16px" }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          style={{ display: "flex", gap: "10px" }}
        >
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              lang === "mr"
                ? "नाव, पॅन किंवा पत्ता शोधा (मराठी किंवा English)..."
                : "Search by name, PAN, or address (Devanagari or English)..."
            }
            leftAddon={<Search size={16} />}
            style={{ flex: 1 }}
          />
          <Button type="submit" size="md" variant="secondary">
            {lang === "mr" ? "शोधा" : "Search"}
          </Button>
        </form>
      </Card>

      {/* 3. Parties List */}
      {loading ? (
        <Skeleton height="300px" />
      ) : parties.length === 0 ? (
        <Card style={{ padding: "40px", textAlign: "center" }}>
          <Users size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
          <div style={{ fontWeight: 600 }}>{lang === "mr" ? "कोणताही पक्षकार सापडला नाही." : "No matching parties found."}</div>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            {lang === "mr" ? "दुसरे नाव शोधा किंवा नवीन पक्षकार तयार करा." : "Try searching by another surname or create a party."}
          </p>
        </Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: "16px" }}>
          {parties.map((p: PartyItem, idx: number) => {
            const attrs = (p.attrs || {}) as Record<string, unknown>;
            const names = (attrs.names || {}) as Record<string, string>;
            const addresses = (attrs.addresses || {}) as Record<string, string>;
            const ageOrDob = (attrs.age_or_dob || {}) as Record<string, number>;

            const nameDisp = p.name_mr || p.name_en || names.mr || names.en || "Unknown";
            const addrDisp = addresses.mr || addresses.en || "Nagpur";
            const panDisp = p.pan || (attrs.pan_masked as string) || "Available";

            return (
              <Card
                key={p.id || idx}
                style={{
                  padding: "18px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "50%",
                        backgroundColor: "var(--brand-100)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "var(--brand-600)",
                      }}
                    >
                      {p.category === "company" ? <Building2 size={18} /> : <Users size={18} />}
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--brand-900)" }}>
                        {nameDisp}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                        {p.name_en && p.name_mr ? p.name_en : p.category || "individual"}
                      </div>
                    </div>
                  </div>
                  <Badge variant="neutral" size="sm" label="Active" />
                </div>

                <div style={{ fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px", backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)" }}>
                  <div><strong>PAN:</strong> <span style={{ fontFamily: "var(--font-mono)" }}>{panDisp}</span></div>
                  <div><strong>Age:</strong> {ageOrDob.age || 40} yrs | {(attrs.gender as string) || "male"}</div>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    <strong>Address:</strong> {addrDisp}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px", marginTop: "auto", paddingTop: "8px" }}>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => handleReuse(p.id, p)}
                    leftIcon={<UserCheck size={14} />}
                    style={{ flex: 1 }}
                  >
                    {lang === "mr" ? "मसुद्यात वापरा (Reuse)" : "Use in Draft"}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* 4. Detect Duplicates Modal */}
      {duplicatesModalOpen && (
        <Modal
          isOpen={duplicatesModalOpen}
          onClose={() => setDuplicatesModalOpen(false)}
          title="संभाव्य डुप्लिकेट पक्षकार (Potential Duplicate Parties)"
          maxWidth="640px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              Detects parties sharing identical PANs or with Devanagari trigram name similarity &gt; 85% (F-065).
            </div>

            {checkingDuplicates ? (
              <Skeleton height="150px" />
            ) : duplicateMatches.length === 0 ? (
              <div style={{ padding: "24px", textAlign: "center", backgroundColor: "var(--surface-sunken)", borderRadius: "var(--radius-card)" }}>
                <CheckCircle2 size={24} color="var(--brand-600)" style={{ margin: "0 auto 8px auto" }} />
                <div style={{ fontWeight: 600 }}>No duplicate parties found.</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                  All party identities in this tenant appear distinct.
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {duplicateMatches.map((m, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: "12px",
                      borderRadius: "var(--radius-input)",
                      backgroundColor: "#FFFBEB",
                      border: "1px solid #FDE68A",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "0.8125rem",
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, color: "#92400E" }}>
                        {m.names?.mr || m.names?.en || "Party"}
                      </div>
                      <div style={{ color: "#78350F", fontSize: "0.75rem" }}>
                        Reason: {m.reason} | Match Type: {m.match_type}
                      </div>
                      {m.pan && <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>PAN: {m.pan}</div>}
                    </div>
                    <Badge variant="under_review" size="sm" label={`${Math.round(m.similarity * 100)}% Match`} />
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "8px" }}>
              <Button size="sm" variant="secondary" onClick={() => setDuplicatesModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* 4. Create Party Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title={lang === "mr" ? "नवीन पक्षकार नोंदणी" : "Register New Party"}
        maxWidth="600px"
      >
        <form onSubmit={handleCreateParty} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>नाव (मराठी)</label>
            <Input
              required
              value={nameMr}
              onChange={(e) => setNameMr(e.target.value)}
              placeholder="उदा. आनंद बळवंत जोशी"
            />
          </div>

          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>Name (English)</label>
            <Input
              value={nameEn}
              onChange={(e) => setNameEn(e.target.value)}
              placeholder="e.g. Anand Balwant Joshi"
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>वय (Age)</label>
              <Input
                type="number"
                value={String(age)}
                onChange={(e) => setAge(parseInt(e.target.value, 10) || 18)}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>पॅन क्र. (PAN)</label>
              <Input
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                placeholder="ABCDE1234F"
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>पत्ता (Address)</label>
            <Input
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="फ्लॅट क्र. २०२, धरमपेठ, नागपूर"
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "12px" }}>
            <Button size="sm" variant="secondary" type="button" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" variant="primary" type="submit">
              Save Party
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
