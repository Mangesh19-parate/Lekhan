import React, { useState, useEffect, useRef } from "react";
import { Modal, Input, Button, Badge, EmptyState } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { apiClient } from "../../shared/api";
import { Search, UserCheck, Shield, MapPin, Briefcase, Sparkles, Building2, User } from "lucide-react";

export interface PartySearchResult {
  id: string;
  kind: string;
  names: Record<string, string>;
  gender?: string;
  age_or_dob?: { age?: number; dob?: string };
  occupations?: Record<string, string>;
  addresses?: Record<string, string>;
  pan_masked?: string;
  version: number;
}

export interface PartyMatch {
  party: PartySearchResult;
  similarity: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  targetRole?: string; // "seller" or "purchaser"
  onSelectParty: (data: {
    full_name: string;
    gender: string;
    age: number;
    occupation: string;
    address: string;
    pan: string;
  }) => void;
}

export const PartySearchModal: React.FC<Props> = ({
  isOpen,
  onClose,
  targetRole = "seller",
  onSelectParty,
}) => {
  const { lang, t } = useI18n();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PartyMatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setSearched(false);
      setError(null);
    }
  }, [isOpen]);

  const executeSearch = async (searchTerm: string) => {
    if (searchTerm.trim().length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient<PartyMatch[]>(
        `/api/v1/parties/search?q=${encodeURIComponent(searchTerm.trim())}&limit=10`
      );
      setResults(data);
      setSearched(true);
    } catch (err: unknown) {
      console.error("Party search error:", err);
      setError(err instanceof Error ? err.message : "Failed to search parties");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQueryChange = (val: string) => {
    setQuery(val);
    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
    }
    debounceRef.current = window.setTimeout(() => {
      executeSearch(val);
    }, 300);
  };

  const handlePick = (match: PartyMatch) => {
    const p = match.party;
    const fullName = p.names[lang] || p.names.mr || p.names.en || Object.values(p.names)[0] || "";
    const addr = p.addresses ? (p.addresses[lang] || p.addresses.mr || p.addresses.en || Object.values(p.addresses)[0] || "") : "";
    const occ = p.occupations ? (p.occupations[lang] || p.occupations.mr || p.occupations.en || Object.values(p.occupations)[0] || "") : "";
    const age = p.age_or_dob?.age ?? 45;
    const gender = p.gender || "male";
    const pan = p.pan_masked || "";

    onSelectParty({
      full_name: fullName,
      gender,
      age,
      occupation: occ,
      address: addr,
      pan,
    });
    onClose();
  };

  const roleLabel = targetRole === "purchaser"
    ? (lang === "mr" ? "खरेदीदार (Purchaser)" : "Purchaser")
    : (lang === "mr" ? "विक्रेता (Seller)" : "Seller");

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={lang === "mr" ? `जतन केलेले पक्षकार निवडा (${roleLabel})` : `Reuse Saved Party (${roleLabel})`}
      size="lg"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Search Input Bar */}
        <div style={{ position: "relative" }}>
          <Input
            id="party-search-input"
            label={lang === "mr" ? "नाव, पॅन किंवा पत्ता शोधा (देवनागरी किंवा इंग्रजी)" : "Search by Name, PAN, or Address (Marathi or English)"}
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            placeholder={lang === "mr" ? "उदा. जोशी, सुरेश पाटील, ABCDE1234F..." : "e.g. Joshi, Suresh Patil, ABCDE1234F..."}
            leftAddon={<Search size={16} />}
            autoFocus
          />
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", fontSize: "0.75rem" }}>
          <span style={{ color: "var(--text-tertiary)", fontWeight: 600 }}>
            {lang === "mr" ? "जलद शोध:" : "Quick suggestions:"}
          </span>
          {["जोशी", "पाटील", "देशपांडे", "Joshi", "Patil"].map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => {
                setQuery(chip);
                executeSearch(chip);
              }}
              style={{
                background: "var(--surface-sunken)",
                border: "1px solid var(--line-subtle)",
                borderRadius: "var(--radius-pill)",
                padding: "3px 10px",
                fontSize: "0.75rem",
                color: "var(--brand-700)",
                cursor: "pointer",
              }}
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Error Notice */}
        {error && (
          <div style={{ padding: "10px 14px", backgroundColor: "var(--color-danger-bg)", color: "var(--color-danger-fg)", borderRadius: "var(--radius-input)", fontSize: "0.8125rem" }}>
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div style={{ padding: "24px", textAlign: "center", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            <Sparkles className="animate-spin inline mr-2 text-brand-600" size={18} />
            {lang === "mr" ? "पक्षकार शोधत आहे (Trigram Search)..." : "Searching parties across registry..."}
          </div>
        )}

        {/* Results List */}
        {!isLoading && results.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "360px", overflowY: "auto" }}>
            {results.map((match) => {
              const p = match.party;
              const primaryName = p.names[lang] || p.names.mr || p.names.en || "अनामिक";
              const secondaryName = lang === "mr" ? p.names.en : p.names.mr;
              const address = p.addresses ? (p.addresses[lang] || p.addresses.mr || p.addresses.en || "") : "";
              const occupation = p.occupations ? (p.occupations[lang] || p.occupations.mr || p.occupations.en || "") : "";
              const matchPercent = Math.round(match.similarity * 100);

              return (
                <div
                  key={p.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "14px 16px",
                    borderRadius: "var(--radius-card)",
                    border: "1px solid var(--line-subtle)",
                    backgroundColor: "var(--surface-sunken)",
                    transition: "border-color 0.15s ease, background-color 0.15s ease",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "flex-start", gap: "12px", flex: 1 }}>
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "var(--radius-pill)",
                        backgroundColor: "var(--brand-50)",
                        color: "var(--brand-700)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      {p.kind === "company" ? <Building2 size={18} /> : <User size={18} />}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        <span style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--text-primary)" }}>
                          {primaryName}
                        </span>
                        {secondaryName && secondaryName !== primaryName && (
                          <span style={{ fontSize: "0.8125rem", color: "var(--text-tertiary)" }}>
                            ({secondaryName})
                          </span>
                        )}
                        <Badge
                          variant="neutral"
                          size="sm"
                          label={`${matchPercent}% Match`}
                        />
                      </div>

                      <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                        {p.pan_masked && (
                          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                            <Shield size={12} color="var(--brand-600)" />
                            PAN: <strong style={{ fontFamily: "var(--font-mono)" }}>{p.pan_masked}</strong>
                          </span>
                        )}
                        {occupation && (
                          <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                            <Briefcase size={12} />
                            {occupation}
                          </span>
                        )}
                        {p.age_or_dob?.age && (
                          <span>
                            {lang === "mr" ? `वय: ${p.age_or_dob.age} वर्षे` : `Age: ${p.age_or_dob.age} yrs`}
                          </span>
                        )}
                      </div>

                      {address && (
                        <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                          <MapPin size={12} />
                          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "340px" }}>
                            {address}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handlePick(match)}
                    leftIcon={<UserCheck size={14} />}
                  >
                    {lang === "mr" ? "लागू करा" : "Select & Fill"}
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        {/* Empty Search Prompt */}
        {!isLoading && searched && results.length === 0 && (
          <EmptyState
            title={lang === "mr" ? "कोणताही पक्षकार सापडला नाही" : "No Matching Parties Found"}
            description={
              lang === "mr"
                ? "कृपया वेगळे अक्षर किंवा पॅन क्रमांक शोधून पहा. आपण फॉर्ममध्ये थेट नवीन तपशील भरू शकता."
                : "Try a different spelling or PAN. You can also enter party details manually in the form."
            }
          />
        )}

        {!searched && !isLoading && (
          <div style={{ textAlign: "center", padding: "20px 0", color: "var(--text-tertiary)", fontSize: "0.8125rem" }}>
            {lang === "mr"
              ? "पक्षाचे नाव किंवा पॅन टाईप करून शोधा (किमान २ अक्षरे)"
              : "Type a party name or PAN above to search across saved registry matters (min 2 chars)"}
          </div>
        )}
      </div>
    </Modal>
  );
};
