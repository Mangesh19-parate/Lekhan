import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
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
} from "lucide-react";

interface PartyDirectoryViewProps {
  onNavigate: (viewId: string) => void;
  onReuseParty?: (partyData: any) => void;
}

export const PartyDirectoryView: React.FC<PartyDirectoryViewProps> = ({
  onNavigate,
  onReuseParty,
}) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [parties, setParties] = useState<any[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);

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
    if (!q || q.length < 2) {
      // Default common search to display existing tenant parties
      try {
        setLoading(true);
        const res = await api.searchParties("जोशी");
        setParties(res || []);
      } catch {
        setParties([]);
      } finally {
        setLoading(false);
      }
      return;
    }

    setLoading(true);
    try {
      const res = await api.searchParties(q);
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
    } catch (err: any) {
      alert("Failed to create party: " + (err?.message || "Check fields"));
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

        <Button size="sm" variant="primary" onClick={() => setCreateModalOpen(true)} leftIcon={<Plus size={15} />}>
          {lang === "mr" ? "नवीन पक्षकार जोडा" : "Add New Party"}
        </Button>
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
          {parties.map((match: any, idx: number) => {
            const p = match.party || match;
            const nameDisp = p.names?.mr || p.names?.en || "Unknown";
            const addrDisp = p.addresses?.mr || p.addresses?.en || "Nagpur";

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
                      {p.kind === "company" ? <Building2 size={18} /> : <Users size={18} />}
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--brand-900)" }}>
                        {nameDisp}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                        {p.names?.en && p.names?.mr ? p.names.en : p.kind}
                      </div>
                    </div>
                  </div>
                  <Badge variant="neutral" size="sm" label={`v${p.version || 1}`} />
                </div>

                <div style={{ fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px", backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)" }}>
                  <div><strong>PAN:</strong> <span style={{ fontFamily: "var(--font-mono)" }}>{p.pan_masked || "Available"}</span></div>
                  <div><strong>Age:</strong> {p.age_or_dob?.age || "Adult"} yrs | {p.gender || "male"}</div>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    <strong>Address:</strong> {addrDisp}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px", marginTop: "auto", paddingTop: "8px" }}>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => {
                      if (onReuseParty) {
                        onReuseParty({
                          full_name: nameDisp,
                          gender: p.gender || "male",
                          age: p.age_or_dob?.age || 40,
                          occupation: p.occupations?.mr || "व्यवसाय",
                          address: addrDisp,
                          pan: p.pan_masked || "ABCDE1234F",
                        });
                      }
                      onNavigate("new_draft");
                    }}
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
