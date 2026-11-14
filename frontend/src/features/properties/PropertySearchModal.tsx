import React, { useState, useEffect, useRef } from "react";
import { Modal, Input, Button, Badge, EmptyState } from "../../shared/components";
import { useI18n } from "../../shared/i18n";
import { apiClient } from "../../shared/api";
import { Search, Landmark, MapPin, Compass, CheckCircle2, Sparkles, Home } from "lucide-react";

export interface PropertySearchResult {
  id: string;
  category: string;
  attrs: Record<string, any>;
  area_value?: number | string;
  area_unit?: string;
  boundaries?: Record<string, string>;
  version: number;
}

export interface PropertyMatch {
  property: PropertySearchResult;
  similarity: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectProperty: (data: Record<string, any>) => void;
}

export const PropertySearchModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onSelectProperty,
}) => {
  const { lang, t } = useI18n();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PropertyMatch[]>([]);
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
      const data = await apiClient<PropertyMatch[]>(
        `/api/v1/properties/search?q=${encodeURIComponent(searchTerm.trim())}&limit=10`
      );
      setResults(data);
      setSearched(true);
    } catch (err: unknown) {
      console.error("Property search error:", err);
      setError(err instanceof Error ? err.message : "Failed to search properties");
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

  const handlePick = (match: PropertyMatch) => {
    const p = match.property;
    const attrs = p.attrs || {};
    const boundaries = p.boundaries || {};

    const extracted: Record<string, any> = {
      "property.mouza": attrs.mouza || "",
      "property.khasra_no": attrs.khasra_no || "",
      "property.plot_no": attrs.plot_no || attrs.flat_no || "",
      "property.layout_name": attrs.layout_name || attrs.building_name || "",
      "property.sheet_no": attrs.sheet_no || "",
      "property.area_sqm": p.area_value ?? "",
    };

    if (boundaries.east) extracted["boundaries.east"] = boundaries.east;
    if (boundaries.west) extracted["boundaries.west"] = boundaries.west;
    if (boundaries.north) extracted["boundaries.north"] = boundaries.north;
    if (boundaries.south) extracted["boundaries.south"] = boundaries.south;

    onSelectProperty(extracted);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={lang === "mr" ? "जतन केलेली मिळकत निवडा (Property Reuse)" : "Reuse Saved Property"}
      size="lg"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Search Input Bar */}
        <div>
          <Input
            id="property-search-input"
            label={lang === "mr" ? "मौजा, खसरा क्र., लेआउट किंवा प्लॉट क्र. शोधा" : "Search by Mouza, Khasra, Layout, or Plot No."}
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            placeholder={lang === "mr" ? "उदा. सोनेगाव, 45/2, बाबुलखेडा, शिवकृपा..." : "e.g. Sonegaon, 45/2, Babulkheda, Shivkrupa..."}
            leftAddon={<Search size={16} />}
            autoFocus
          />
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", fontSize: "0.75rem" }}>
          <span style={{ color: "var(--text-tertiary)", fontWeight: 600 }}>
            {lang === "mr" ? "जलद शोध:" : "Quick suggestions:"}
          </span>
          {["सोनेगाव", "Sonegaon", "45/2", "बाबुलखेडा", "धरमपेठ"].map((chip) => (
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
            {lang === "mr" ? "मिळकती शोधत आहे (Trigram Search)..." : "Searching registered property schedules..."}
          </div>
        )}

        {/* Results List */}
        {!isLoading && results.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "360px", overflowY: "auto" }}>
            {results.map((match) => {
              const p = match.property;
              const attrs = p.attrs || {};
              const matchPercent = Math.round(match.similarity * 100);

              const title = attrs.plot_no
                ? `${lang === "mr" ? "प्लॉट क्र." : "Plot No."} ${attrs.plot_no}, ${attrs.mouza || ""}`
                : attrs.flat_no
                ? `${lang === "mr" ? "फ्लॅट क्र." : "Flat No."} ${attrs.flat_no}, ${attrs.building_name || ""}`
                : attrs.mouza || "Property";

              const subtitle = [
                attrs.khasra_no ? `${lang === "mr" ? "खसरा क्र." : "Khasra"} ${attrs.khasra_no}` : null,
                attrs.layout_name ? attrs.layout_name : null,
                p.area_value ? `${p.area_value} ${p.area_unit || "sqm"}` : null,
              ]
                .filter(Boolean)
                .join(" • ");

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
                      {p.category === "flat" ? <Home size={18} /> : <Landmark size={18} />}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        <span style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--text-primary)" }}>
                          {title}
                        </span>
                        <Badge
                          variant="neutral"
                          size="sm"
                          label={`${matchPercent}% Match`}
                        />
                      </div>

                      <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                        {subtitle}
                      </div>

                      {p.boundaries && (
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                          <Compass size={12} />
                          <span>
                            {lang === "mr" ? "पूर्व:" : "E:"} {p.boundaries.east || "—"} | {lang === "mr" ? "पश्चिम:" : "W:"} {p.boundaries.west || "—"}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handlePick(match)}
                    leftIcon={<CheckCircle2 size={14} />}
                  >
                    {lang === "mr" ? "लागू करा" : "Select & Apply"}
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        {/* Empty Search Prompt */}
        {!isLoading && searched && results.length === 0 && (
          <EmptyState
            title={lang === "mr" ? "कोणतीही मिळकत सापडली नाही" : "No Matching Properties Found"}
            description={
              lang === "mr"
                ? "कृपया वेगळा मौजा किंवा खसरा क्रमांक शोधा. आपण मिळकतीचे तपशील फॉर्ममध्ये थेट टाईप करू शकता."
                : "Try a different Mouza or Khasra number, or enter property details manually."
            }
          />
        )}

        {!searched && !isLoading && (
          <div style={{ textAlign: "center", padding: "20px 0", color: "var(--text-tertiary)", fontSize: "0.8125rem" }}>
            {lang === "mr"
              ? "मिळकतीचा मौजा किंवा खसरा टाईप करून शोधा (किमान २ अक्षरे)"
              : "Type a Mouza name or Khasra number to search saved property schedules (min 2 chars)"}
          </div>
        )}
      </div>
    </Modal>
  );
};
