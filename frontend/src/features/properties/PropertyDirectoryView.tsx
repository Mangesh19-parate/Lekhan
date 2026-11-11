import React, { useEffect, useState } from "react";
import { useI18n } from "../../shared/i18n";
import { api } from "../../shared/api";
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
} from "lucide-react";

interface PropertyDirectoryViewProps {
  onNavigate: (viewId: string) => void;
  onReuseProperty?: (propertyData: any) => void;
}

export const PropertyDirectoryView: React.FC<PropertyDirectoryViewProps> = ({
  onNavigate,
  onReuseProperty,
}) => {
  const { lang } = useI18n();
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [properties, setProperties] = useState<any[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);

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
      setProperties(res || []);
    } catch {
      setProperties([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch("");
  }, [category]);

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
    } catch (err: any) {
      alert("Failed to create property: " + (err?.message || "Check inputs"));
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

        <Button size="sm" variant="primary" onClick={() => setCreateModalOpen(true)} leftIcon={<Plus size={15} />}>
          {lang === "mr" ? "नवीन मिळकत जोडा" : "Register Property"}
        </Button>
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
          {properties.map((match: any, idx: number) => {
            const prop = match.property || match;
            const a = prop.attrs || {};
            const b = prop.boundaries || {};
            const areaSqmVal = prop.area_value || 150;
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
                        {a.mouza || "नागपूर"}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                        {prop.category.toUpperCase()} | Khasra: {a.khasra_no || "N/A"}, Plot: {a.plot_no || "N/A"}
                      </div>
                    </div>
                  </div>
                  <Badge variant="approved" size="sm" label={`v${prop.version || 1}`} />
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
                    onClick={() => {
                      if (onReuseProperty) {
                        onReuseProperty({
                          "property.mouza": a.mouza,
                          "property.khasra_no": a.khasra_no,
                          "property.plot_no": a.plot_no,
                          "property.layout_name": a.layout_name,
                          "property.sheet_no": a.sheet_no,
                          "property.area_sqm": areaSqmVal,
                          "boundaries.east": b.east,
                          "boundaries.west": b.west,
                          "boundaries.north": b.north,
                          "boundaries.south": b.south,
                        });
                      }
                      onNavigate("new_draft");
                    }}
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
