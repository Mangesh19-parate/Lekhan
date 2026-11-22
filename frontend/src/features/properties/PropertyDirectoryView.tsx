import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api, type PropertyItem, type PropertyDuplicateMatch } from "../../shared/api";
import { Button, Badge, Card, Input, Select, Modal, Skeleton } from "../../shared/components";
import {
  MapPin,
  Search,
  Plus,
  Landmark,
  Building,
  TreePine,
  Layers,
  ArrowRight,
  RefreshCw,
  Copy,
  CheckCircle2,
} from "lucide-react";

interface PropertyDirectoryViewProps {
  onNavigate: (viewId: string) => void;
  onReuseProperty?: (propertyData: Record<string, unknown>) => void;
}

export const PropertyDirectoryView: React.FC<PropertyDirectoryViewProps> = ({
  onNavigate,
  onReuseProperty,
}) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [properties, setProperties] = useState<PropertyItem[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  // Duplicates modal
  const [duplicatesModalOpen, setDuplicatesModalOpen] = useState(false);
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);
  const [duplicateMatches, setDuplicateMatches] = useState<PropertyDuplicateMatch[]>([]);

  // Form state
  const [propCategory, setPropCategory] = useState("plot");
  const [mouza, setMouza] = useState("सोनेगाव (Sonegaon)");
  const [khasraNo, setKhasraNo] = useState("45/2");
  const [plotNo, setPlotNo] = useState("12");
  const [layoutName, setLayoutName] = useState("शिवकृपा लेआउट");
  const [sheetNo, setSheetNo] = useState("14");
  const [areaSqm, setAreaSqm] = useState("150");
  const [east, setEast] = useState("९.०० मी. रुंद रस्ता");
  const [west, setWest] = useState("भूखंड क्र. १३");
  const [north, setNorth] = useState("भूखंड क्र. ११");
  const [south, setSouth] = useState("लेआउट सीमा");

  const handleSearch = async (searchQ?: string) => {
    const q = searchQ !== undefined ? searchQ : query;
    setLoading(true);
    try {
      const res = await api.searchProperties(
        q && q.length >= 2 ? q : "सोनेगाव",
        category === "all" ? undefined : category
      );
      setProperties(Array.isArray(res) ? res : []);
    } catch {
      setProperties([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch("");
  }, [category]);

  const handleCheckDuplicates = async () => {
    setCheckingDuplicates(true);
    setDuplicatesModalOpen(true);
    try {
      const matches = await api.detectDuplicateProperties({
        survey_number: query.trim() || undefined,
        village: mouza || undefined,
      });
      setDuplicateMatches(matches);
    } catch {
      setDuplicateMatches([]);
    } finally {
      setCheckingDuplicates(false);
    }
  };

  const handleReuse = async (propId: string, propObj: PropertyItem) => {
    try {
      await api.reuseProperty(propId);
    } catch {
      // Offline fallback
    }
    if (onReuseProperty) {
      const a = (propObj.attrs || {}) as Record<string, string>;
      const b = (propObj.attrs?.boundaries || {}) as Record<string, string>;
      onReuseProperty({
        "property.mouza": a.mouza || propObj.village,
        "property.khasra_no": a.khasra_no || propObj.survey_number,
        "property.plot_no": a.plot_no || "12",
        "property.layout_name": a.layout_name || "",
        "property.sheet_no": a.sheet_no || "",
        "property.area_sqm": propObj.area_sqft ? Math.round(propObj.area_sqft * 0.0929) : 150,
        "boundaries.east": b.east || "Road",
        "boundaries.west": b.west || "Plot",
        "boundaries.north": b.north || "Plot",
        "boundaries.south": b.south || "Boundary",
      });
    }
    onNavigate("new_draft");
  };

  const handleCreateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createProperty({
        category: propCategory,
        attrs: {
          mouza,
          khasra_no: khasraNo,
          plot_no: plotNo,
          layout_name: layoutName,
          sheet_no: sheetNo,
        },
        area_value: parseFloat(areaSqm) || 100,
        area_unit: "sqm",
        boundaries: {
          east,
          west,
          north,
          south,
        },
      });
      setCreateModalOpen(false);
      handleSearch(mouza);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create property";
      alert("Failed to create property: " + msg);
    }
  };

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--brand-900)", margin: 0 }}>
              {lang === "mr" ? "मिळकत नोंदवही (Property Directory)" : "Property Directory"}
            </h1>
            <Badge variant="approved" size="md" label="Cadastral Index" />
          </div>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0 0 0", fontSize: "0.875rem" }}>
            {lang === "mr"
              ? "मौजे, खसरा, लेआउट व चतुःसीमा व्यवस्थापन आणि दस्त मसुद्यात अचूक पुनर्वापर."
              : "Cadastral land parcels, boundary schedules, and immutable property snapshots for drafting."}
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
            {lang === "mr" ? "नवीन मिळकत जोडा" : "Register Property"}
          </Button>
        </div>
      </div>

      {/* 2. Search & Category Filters */}
      <Card style={{ padding: "16px", display: "flex", flexWrap: "wrap", gap: "14px", alignItems: "center", justifyContent: "space-between" }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          style={{ display: "flex", gap: "10px", flex: 1, minWidth: "260px" }}
        >
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={lang === "mr" ? "मौजे, खसरा, प्लॉट क्र. किंवा लेआउट शोधा..." : "Search by mouza, khasra no, plot, or CTS..."}
            leftAddon={<Search size={16} />}
            style={{ width: "100%" }}
          />
          <Button type="submit" size="md" variant="secondary">
            {lang === "mr" ? "शोधा" : "Search"}
          </Button>
        </form>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
            {lang === "mr" ? "प्रकार:" : "Category:"}
          </span>
          <Select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            options={[
              { label: lang === "mr" ? "सर्व मिळकती (All)" : "All Categories", value: "all" },
              { label: lang === "mr" ? "भूखंड (Plot)" : "Plot", value: "plot" },
              { label: lang === "mr" ? "सदनिका (Flat)" : "Flat", value: "flat" },
              { label: lang === "mr" ? "दुकान (Shop)" : "Shop", value: "shop" },
              { label: lang === "mr" ? "शेतीजमीन (Agricultural)" : "Agricultural", value: "agricultural" },
            ]}
          />
        </div>
      </Card>

      {/* 3. Property Cards Grid */}
      {loading ? (
        <Skeleton height="300px" />
      ) : properties.length === 0 ? (
        <Card style={{ padding: "40px", textAlign: "center" }}>
          <MapPin size={36} color="var(--text-tertiary)" style={{ margin: "0 auto 10px auto" }} />
          <div style={{ fontWeight: 600 }}>{lang === "mr" ? "कोणतीही मिळकत सापडली नाही." : "No properties matched."}</div>
        </Card>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: "16px" }}>
          {properties.map((prop: PropertyItem, idx: number) => {
            const a = (prop.attrs || {}) as Record<string, string>;
            const b = ((prop.attrs?.boundaries || prop.attrs || {}) as Record<string, string>);
            const areaSqmVal = (prop.attrs?.area_value as number) || (prop.area_sqft ? Math.round(prop.area_sqft * 0.0929) : 150);
            const areaSqftVal = (areaSqmVal * 10.7639104).toFixed(2);

            return (
              <Card
                key={prop.id || idx}
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
                      {prop.category === "flat" ? (
                        <Building size={18} />
                      ) : prop.category === "agricultural" ? (
                        <TreePine size={18} />
                      ) : (
                        <Landmark size={18} />
                      )}
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--brand-900)" }}>
                        {a.mouza || prop.village || "नागपूर"}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                        {(prop.category || "plot").toUpperCase()} | Khasra: {a.khasra_no || prop.survey_number || "N/A"}, Plot: {a.plot_no || "N/A"}
                      </div>
                    </div>
                  </div>
                  <Badge variant="approved" size="sm" label="Active" />
                </div>

                <div style={{ backgroundColor: "var(--surface-sunken)", padding: "10px", borderRadius: "var(--radius-input)", fontSize: "0.8125rem", display: "flex", flexDirection: "column", gap: "4px" }}>
                  <div><strong>Area:</strong> {areaSqmVal} Sq.M ({areaSqftVal} Sq.Ft)</div>
                  {a.layout_name && <div><strong>Layout:</strong> {a.layout_name}</div>}
                  <div style={{ marginTop: "4px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    <strong>Boundaries:</strong> E: {b.east || "Road"}, W: {b.west || "Plot"}, N: {b.north || "Plot"}, S: {b.south || "Boundary"}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px", marginTop: "auto", paddingTop: "8px" }}>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => handleReuse(prop.id, prop)}
                    leftIcon={<MapPin size={14} />}
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
          title="संभाव्य डुप्लिकेट मिळकती (Potential Duplicate Properties)"
          maxWidth="640px"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              Detects properties sharing identical cadastral survey numbers, khasra numbers, or plot numbers within village scope.
            </div>

            {checkingDuplicates ? (
              <Skeleton height="150px" />
            ) : duplicateMatches.length === 0 ? (
              <div style={{ padding: "24px", textAlign: "center", backgroundColor: "var(--surface-sunken)", borderRadius: "var(--radius-card)" }}>
                <CheckCircle2 size={24} color="var(--brand-600)" style={{ margin: "0 auto 8px auto" }} />
                <div style={{ fontWeight: 600 }}>No duplicate properties detected.</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                  Survey parcel references appear distinct across tenant cadastral entries.
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
                        Survey/Plot: {m.survey_number} | Village: {m.village || "Chamber Area"}
                      </div>
                      <div style={{ color: "#78350F", fontSize: "0.75rem" }}>
                        Reason: {m.reason} | Match Type: {m.match_type}
                      </div>
                    </div>
                    <Badge variant="under_review" size="sm" label="Duplicate Match" />
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

      {/* 4. Create Property Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title={lang === "mr" ? "नवीन मिळकत नोंदणी" : "Register Property Parcel"}
        maxWidth="650px"
      >
        <form onSubmit={handleCreateProperty} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>मिळकत प्रकार (Category)</label>
              <Select
                value={propCategory}
                onChange={(e) => setPropCategory(e.target.value)}
                options={[
                  { label: "भूखंड (Plot)", value: "plot" },
                  { label: "सदनिका (Flat)", value: "flat" },
                  { label: "दुकान (Shop)", value: "shop" },
                  { label: "शेतीजमीन (Agricultural)", value: "agricultural" },
                ]}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>मौजे (Mouza)</label>
              <Input value={mouza} onChange={(e) => setMouza(e.target.value)} required />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>खसरा क्र. (Khasra No.)</label>
              <Input value={khasraNo} onChange={(e) => setKhasraNo(e.target.value)} required />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>भूखंड क्र. (Plot No.)</label>
              <Input value={plotNo} onChange={(e) => setPlotNo(e.target.value)} required />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>क्षेत्रफळ (चौ.मी.)</label>
              <Input type="number" value={areaSqm} onChange={(e) => setAreaSqm(e.target.value)} required />
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>लेआउट / कॉलनीचे नाव</label>
            <Input value={layoutName} onChange={(e) => setLayoutName(e.target.value)} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>पूर्व (East Boundary)</label>
              <Input value={east} onChange={(e) => setEast(e.target.value)} />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>पश्चिम (West Boundary)</label>
              <Input value={west} onChange={(e) => setWest(e.target.value)} />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>उत्तर (North Boundary)</label>
              <Input value={north} onChange={(e) => setNorth(e.target.value)} />
            </div>
            <div>
              <label style={{ fontSize: "0.8125rem", fontWeight: 600 }}>दक्षिण (South Boundary)</label>
              <Input value={south} onChange={(e) => setSouth(e.target.value)} />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "12px" }}>
            <Button size="sm" variant="secondary" type="button" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" variant="primary" type="submit">
              Save Property Parcel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
