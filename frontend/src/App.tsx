import React, { useState, useEffect, useMemo, useCallback } from "react";
import { I18nProvider, useI18n } from "./shared/i18n";
import { ToastProvider, useToast, Button, Badge } from "./shared/components";
import { AuthProvider, useAuth } from "./shared/auth/AuthContext";
import { LoginModal } from "./shared/auth/LoginModal";
import { CommandPalette } from "./features/form_engine/CommandPalette";
import { KeyboardShortcutsModal } from "./features/form_engine/KeyboardShortcutsModal";

// Views
import { DashboardView } from "./features/dashboard/DashboardView";
import { DraftingWorkspace } from "./features/drafting/DraftingWorkspace";
import { DocumentsListView } from "./features/documents/DocumentsListView";
import { DraftsPendingView } from "./features/drafts/DraftsPendingView";
import { ReviewCenterView } from "./features/review/ReviewCenterView";
import { TemplateLibraryView } from "./features/templates/TemplateLibraryView";
import { TemplateStudioView } from "./features/templates/TemplateStudioView";
import { PartyDirectoryView } from "./features/parties/PartyDirectoryView";
import { PropertyDirectoryView } from "./features/properties/PropertyDirectoryView";
import { DocumentQualityView } from "./features/intelligence/DocumentQualityView";
import { ValidationCenterView } from "./features/intelligence/ValidationCenterView";
import { AdvisoryCenterView } from "./features/intelligence/AdvisoryCenterView";
import { RegistrationDataView } from "./features/intelligence/RegistrationDataView";
import { UserManagementView } from "./features/admin/UserManagementView";
import { RolesPermissionsView } from "./features/admin/RolesPermissionsView";
import { AuditTrailView } from "./features/admin/AuditTrailView";
import { SystemSettingsView } from "./features/admin/SystemSettingsView";
import { SystemHealthView } from "./features/admin/SystemHealthView";

import {
  LayoutDashboard,
  FilePlus,
  FileText,
  Clock,
  ShieldCheck,
  Layers,
  FileCode,
  Users,
  MapPin,
  Archive,
  CheckCircle2,
  Cpu,
  HelpCircle,
  ExternalLink,
  UserCheck,
  Lock,
  History,
  Settings,
  Activity,
  ChevronLeft,
  ChevronRight,
  Search,
  Moon,
  Sun,
  Keyboard,
  LogOut,
  LogIn,
  Sparkles,
  Check,
} from "lucide-react";

type ViewId =
  | "overview"
  | "new_draft"
  | "my_documents"
  | "drafts_pending"
  | "review_center"
  | "template_library"
  | "template_studio"
  | "party_directory"
  | "property_directory"
  | "document_archive"
  | "document_quality"
  | "validation_center"
  | "advisory_center"
  | "registration_data"
  | "user_management"
  | "roles_permissions"
  | "audit_trail"
  | "system_settings"
  | "system_health";

interface NavItem {
  id: ViewId;
  labelEn: string;
  labelMr: string;
  icon: any;
  badge?: string;
}

interface NavSection {
  titleEn: string;
  titleMr: string;
  items: NavItem[];
}

const NAVIGATION_SECTIONS: NavSection[] = [
  {
    titleEn: "WORKSPACE",
    titleMr: "कार्यक्षेत्र",
    items: [
      { id: "overview", labelEn: "Overview", labelMr: "आढावा", icon: LayoutDashboard },
      { id: "new_draft", labelEn: "New Draft", labelMr: "नवीन मसुदा", icon: FilePlus },
      { id: "my_documents", labelEn: "My Documents", labelMr: "माझे दस्तऐवज", icon: FileText },
      { id: "drafts_pending", labelEn: "Drafts & Pending", labelMr: "प्रलंबित मसुदे", icon: Clock },
      { id: "review_center", labelEn: "Review Center", labelMr: "तपासणी केंद्र", icon: ShieldCheck },
    ],
  },
  {
    titleEn: "DOCUMENT OPERATIONS",
    titleMr: "दस्त कामकाज",
    items: [
      { id: "template_library", labelEn: "Template Library", labelMr: "साचा ग्रंथालय", icon: Layers },
      { id: "template_studio", labelEn: "Template Studio", labelMr: "साचा स्टुडिओ", icon: FileCode },
      { id: "party_directory", labelEn: "Party Directory", labelMr: "पक्षकार सूची", icon: Users },
      { id: "property_directory", labelEn: "Property Directory", labelMr: "मिळकती सूची", icon: MapPin },
      { id: "document_archive", labelEn: "Document Archive", labelMr: "अभिलेखागार", icon: Archive },
    ],
  },
  {
    titleEn: "INTELLIGENCE",
    titleMr: "दस्त बुद्धिमत्ता",
    items: [
      { id: "document_quality", labelEn: "Document Quality", labelMr: "गुणवत्ता तपासणी", icon: CheckCircle2 },
      { id: "validation_center", labelEn: "Validation Center", labelMr: "नियम पडताळणी", icon: Cpu },
      { id: "advisory_center", labelEn: "Advisory Center", labelMr: "कायदेशीर सल्ला", icon: HelpCircle },
      { id: "registration_data", labelEn: "Registration Data", labelMr: "नोंदणी डेटा (PDE)", icon: ExternalLink },
    ],
  },
  {
    titleEn: "ADMINISTRATION",
    titleMr: "प्रशासन व नियंत्रण",
    items: [
      { id: "user_management", labelEn: "User Management", labelMr: "वापरकर्ते", icon: UserCheck },
      { id: "roles_permissions", labelEn: "Roles & Permissions", labelMr: "भूमिका व अधिकार", icon: Lock },
      { id: "audit_trail", labelEn: "Audit Trail", labelMr: "ऑडिट ट्रेल", icon: History },
      { id: "system_settings", labelEn: "System Settings", labelMr: "प्रणाली संरचना", icon: Settings },
      { id: "system_health", labelEn: "System Health", labelMr: "प्रणाली आरोग्य", icon: Activity },
    ],
  },
];

const AppShell: React.FC = () => {
  const { lang, setLang } = useI18n();
  const { toast } = useToast();
  const { user, isAuthenticated, logout } = useAuth();

  // Navigation State
  const [currentView, setCurrentView] = useState<ViewId>(() => {
    const saved = localStorage.getItem("lekhan_current_view");
    return (saved as ViewId) || "overview";
  });

  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    return localStorage.getItem("lekhan_sidebar_collapsed") === "true";
  });

  // State transferred across views
  const [activeTemplateId, setActiveTemplateId] = useState<string | undefined>(undefined);
  const [resumeDraftData, setResumeDraftData] = useState<any | null>(null);

  // Modals & Palette
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  // Theme
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    return (localStorage.getItem("lekhan_theme") as "light" | "dark") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("lekhan_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("lekhan_sidebar_collapsed", String(next));
      return next;
    });
  };

  const handleNavigate = useCallback((viewId: string, templateId?: string) => {
    if (templateId) {
      setActiveTemplateId(templateId);
    }
    setCurrentView(viewId as ViewId);
    localStorage.setItem("lekhan_current_view", viewId);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleResumeDraft = useCallback((draft: any) => {
    setResumeDraftData(draft);
    if (draft.templateId) {
      setActiveTemplateId(draft.templateId);
    }
    setCurrentView("new_draft");
    localStorage.setItem("lekhan_current_view", "new_draft");
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      } else if (e.key === "?" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        setShortcutsOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Find active nav metadata for breadcrumbs
  const activeNavMetadata = useMemo(() => {
    for (const section of NAVIGATION_SECTIONS) {
      const item = section.items.find((i) => i.id === currentView);
      if (item) {
        return {
          sectionTitle: lang === "mr" ? section.titleMr : section.titleEn,
          itemTitle: lang === "mr" ? item.labelMr : item.labelEn,
          icon: item.icon,
        };
      }
    }
    return {
      sectionTitle: lang === "mr" ? "कार्यक्षेत्र" : "WORKSPACE",
      itemTitle: lang === "mr" ? "आढावा" : "Overview",
      icon: LayoutDashboard,
    };
  }, [currentView, lang]);

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        backgroundColor: "var(--surface-canvas, #F2F0EB)",
        color: "var(--text-primary, #1A1A1A)",
        fontFamily: "'Inter', 'Noto Sans Devanagari', -apple-system, sans-serif",
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* SIDEBAR NAVIGATION                                            */}
      {/* ------------------------------------------------------------- */}
      <aside
        style={{
          width: sidebarCollapsed ? "72px" : "268px",
          backgroundColor: "var(--brand-900, #1E3932)",
          color: "#FFFFFF",
          display: "flex",
          flexDirection: "column",
          transition: "width 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
          zIndex: 40,
          flexShrink: 0,
          borderRight: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "2px 0 12px rgba(0, 0, 0, 0.15)",
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            height: "64px",
            display: "flex",
            alignItems: "center",
            justifyContent: sidebarCollapsed ? "center" : "space-between",
            padding: sidebarCollapsed ? "0" : "0 18px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          {!sidebarCollapsed ? (
            <div style={{ display: "flex", alignItems: "center", gap: "10px", overflow: "hidden" }}>
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "8px",
                  backgroundColor: "var(--brand-500, #00754A)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 2px 6px rgba(0, 0, 0, 0.2)",
                  color: "#FFFFFF",
                  fontWeight: 800,
                  fontSize: "18px",
                }}
              >
                लेख
              </div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "16px", fontWeight: 700, letterSpacing: "-0.01em", color: "#FFFFFF" }}>
                  LEKHAN
                </span>
                <span style={{ fontSize: "10px", color: "var(--approved-400, #DFB96E)", fontWeight: 500 }}>
                  Enterprise Drafting v2.0
                </span>
              </div>
            </div>
          ) : (
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                backgroundColor: "var(--brand-500, #00754A)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FFFFFF",
                fontWeight: 800,
                fontSize: "18px",
              }}
            >
              लेख
            </div>
          )}

          <button
            onClick={toggleSidebar}
            aria-label="Toggle Navigation Sidebar"
            style={{
              background: "none",
              border: "none",
              color: "rgba(255, 255, 255, 0.6)",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "6px",
              display: sidebarCollapsed ? "none" : "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            <ChevronLeft size={18} />
          </button>
        </div>

        {/* Navigation Sections */}
        <nav
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "16px 8px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {NAVIGATION_SECTIONS.map((section, sIdx) => (
            <div key={sIdx}>
              {!sidebarCollapsed && (
                <div
                  style={{
                    padding: "0 10px 6px 10px",
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.06em",
                    color: "rgba(255, 255, 255, 0.45)",
                    textTransform: "uppercase",
                  }}
                >
                  {lang === "mr" ? section.titleMr : section.titleEn}
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                {section.items.map((item) => {
                  const isActive = currentView === item.id;
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavigate(item.id)}
                      title={sidebarCollapsed ? (lang === "mr" ? item.labelMr : item.labelEn) : undefined}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "12px",
                        padding: sidebarCollapsed ? "10px 0" : "9px 12px",
                        justifyContent: sidebarCollapsed ? "center" : "flex-start",
                        borderRadius: "8px",
                        border: "none",
                        backgroundColor: isActive
                          ? "var(--brand-600, #006241)"
                          : "transparent",
                        color: isActive ? "#FFFFFF" : "rgba(255, 255, 255, 0.78)",
                        fontWeight: isActive ? 600 : 500,
                        fontSize: "13.5px",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                        textAlign: "left",
                        width: "100%",
                        position: "relative",
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
                          e.currentTarget.style.color = "#FFFFFF";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.backgroundColor = "transparent";
                          e.currentTarget.style.color = "rgba(255, 255, 255, 0.78)";
                        }
                      }}
                    >
                      <Icon
                        size={18}
                        className={isActive ? "text-approved-400" : "text-white opacity-70"}
                      />
                      {!sidebarCollapsed && (
                        <span style={{ flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {lang === "mr" ? item.labelMr : item.labelEn}
                        </span>
                      )}
                      {isActive && !sidebarCollapsed && (
                        <div
                          style={{
                            width: "4px",
                            height: "18px",
                            borderRadius: "2px",
                            backgroundColor: "var(--approved-400, #DFB96E)",
                          }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar Footer / User Profile */}
        <div
          style={{
            padding: "12px 14px",
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
            backgroundColor: "rgba(0, 0, 0, 0.15)",
          }}
        >
          {isAuthenticated && user ? (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: sidebarCollapsed ? "center" : "space-between",
                gap: "8px",
              }}
            >
              {!sidebarCollapsed && (
                <div style={{ overflow: "hidden" }}>
                  <div style={{ fontSize: "12.5px", fontWeight: 600, color: "#FFFFFF", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {user.email.split("@")[0]}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--approved-400, #DFB96E)" }}>
                    {user.role} • {user.tenant_id}
                  </div>
                </div>
              )}
              <button
                onClick={logout}
                title="Sign Out"
                style={{
                  background: "none",
                  border: "none",
                  color: "rgba(255, 255, 255, 0.6)",
                  cursor: "pointer",
                  padding: "6px",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#FF6B6B")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255, 255, 255, 0.6)")}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setLoginModalOpen(true)}
              style={{
                width: "100%",
                color: "#FFFFFF",
                borderColor: "rgba(255, 255, 255, 0.2)",
                justifyContent: "center",
              }}
            >
              <LogIn size={15} style={{ marginRight: sidebarCollapsed ? 0 : "6px" }} />
              {!sidebarCollapsed && (lang === "mr" ? "लॉगिन करा" : "Sign In")}
            </Button>
          )}
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* MAIN CONTENT AREA                                             */}
      {/* ------------------------------------------------------------- */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, overflowX: "hidden" }}>
        {/* Top Navigation Bar */}
        <header
          style={{
            height: "64px",
            backgroundColor: "var(--surface-card, #FFFFFF)",
            borderBottom: "1px solid var(--border-subtle, #E6E1D8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            position: "sticky",
            top: 0,
            zIndex: 30,
            boxShadow: "0 1px 4px rgba(0, 0, 0, 0.04)",
          }}
        >
          {/* Left: Breadcrumb */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px" }}>
            <span style={{ color: "var(--text-muted, #737373)", fontWeight: 500 }}>
              {activeNavMetadata.sectionTitle}
            </span>
            <span style={{ color: "var(--text-muted, #737373)" }}>/</span>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-primary, #1A1A1A)", fontWeight: 700 }}>
              <activeNavMetadata.icon size={16} color="var(--brand-600, #006241)" />
              <span>{activeNavMetadata.itemTitle}</span>
            </div>
          </div>

          {/* Center: Command Palette Trigger */}
          <button
            onClick={() => setCommandPaletteOpen(true)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "6px 14px",
              borderRadius: "20px",
              backgroundColor: "var(--surface-canvas, #F2F0EB)",
              border: "1px solid var(--border-subtle, #E6E1D8)",
              color: "var(--text-muted, #737373)",
              fontSize: "12.5px",
              cursor: "pointer",
              transition: "all 0.15s ease",
              width: "320px",
              justifyContent: "space-between",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--brand-500, #00754A)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-subtle, #E6E1D8)";
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Search size={14} />
              <span>{lang === "mr" ? "शोध किंवा आज्ञा (Search deeds, actions)..." : "Quick action or search (Ctrl+K)..."}</span>
            </div>
            <kbd
              style={{
                backgroundColor: "var(--surface-card, #FFFFFF)",
                border: "1px solid var(--border-subtle, #E6E1D8)",
                borderRadius: "4px",
                padding: "2px 6px",
                fontSize: "10px",
                fontWeight: 600,
                color: "var(--text-muted, #737373)",
              }}
            >
              ⌘K
            </kbd>
          </button>

          {/* Right: Controls & Toggles */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {/* Sync Status Badge */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11.5px",
                color: "var(--brand-600, #006241)",
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: "12px",
                backgroundColor: "rgba(0, 98, 65, 0.08)",
              }}
            >
              <Check size={13} />
              <span>{lang === "mr" ? "सुरक्षित जोडलेले (Synced)" : "Synced"}</span>
            </div>

            {/* Language Switcher */}
            <div
              style={{
                display: "flex",
                backgroundColor: "var(--surface-canvas, #F2F0EB)",
                borderRadius: "6px",
                padding: "2px",
                border: "1px solid var(--border-subtle, #E6E1D8)",
              }}
            >
              <button
                onClick={() => setLang("mr")}
                style={{
                  border: "none",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: lang === "mr" ? 700 : 500,
                  backgroundColor: lang === "mr" ? "var(--surface-card, #FFFFFF)" : "transparent",
                  color: lang === "mr" ? "var(--brand-600, #006241)" : "var(--text-muted, #737373)",
                  boxShadow: lang === "mr" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                  cursor: "pointer",
                }}
              >
                मराठी
              </button>
              <button
                onClick={() => setLang("en")}
                style={{
                  border: "none",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "12px",
                  fontWeight: lang === "en" ? 700 : 500,
                  backgroundColor: lang === "en" ? "var(--surface-card, #FFFFFF)" : "transparent",
                  color: lang === "en" ? "var(--brand-600, #006241)" : "var(--text-muted, #737373)",
                  boxShadow: lang === "en" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                  cursor: "pointer",
                }}
              >
                EN
              </button>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              style={{
                background: "none",
                border: "1px solid var(--border-subtle, #E6E1D8)",
                padding: "6px 8px",
                borderRadius: "6px",
                color: "var(--text-primary, #1A1A1A)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
              }}
              title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
            >
              {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
            </button>

            {/* Shortcuts Guide */}
            <button
              onClick={() => setShortcutsOpen(true)}
              style={{
                background: "none",
                border: "1px solid var(--border-subtle, #E6E1D8)",
                padding: "6px 8px",
                borderRadius: "6px",
                color: "var(--text-primary, #1A1A1A)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
              }}
              title="Keyboard Shortcuts (?)"
            >
              <Keyboard size={16} />
            </button>
          </div>
        </header>

        {/* View Switcher Container */}
        <main style={{ flex: 1, padding: "20px 24px", overflowY: "auto" }}>
          {/* WORKSPACE */}
          {currentView === "overview" && (
            <DashboardView onNavigate={handleNavigate} />
          )}

          {currentView === "new_draft" && (
            <DraftingWorkspace
              onNavigate={handleNavigate}
              activeTemplateId={activeTemplateId}
              initialDraftData={resumeDraftData}
            />
          )}

          {currentView === "my_documents" && (
            <DocumentsListView onNavigate={handleNavigate} isArchiveMode={false} />
          )}

          {currentView === "drafts_pending" && (
            <DraftsPendingView onNavigate={handleNavigate} onResumeDraft={handleResumeDraft} />
          )}

          {currentView === "review_center" && (
            <ReviewCenterView onNavigate={handleNavigate} />
          )}

          {/* DOCUMENT OPERATIONS */}
          {currentView === "template_library" && (
            <TemplateLibraryView
              onNavigate={handleNavigate}
              onSelectTemplateForDrafting={(tmpl) => {
                setActiveTemplateId(tmpl.template_id);
                setCurrentView("new_draft");
              }}
            />
          )}

          {currentView === "template_studio" && (
            <TemplateStudioView onNavigate={handleNavigate} />
          )}

          {currentView === "party_directory" && (
            <PartyDirectoryView
              onNavigate={handleNavigate}
              onReuseParty={(party) => {
                toast({
                  type: "success",
                  title: lang === "mr" ? "पक्षकार निवडला" : "Party Selected",
                  description: `${party.full_name_mr || party.full_name_en} copied for next draft.`,
                });
                handleNavigate("new_draft");
              }}
            />
          )}

          {currentView === "property_directory" && (
            <PropertyDirectoryView
              onNavigate={handleNavigate}
              onReuseProperty={(prop) => {
                toast({
                  type: "success",
                  title: lang === "mr" ? "मिळकती तपशील निवडले" : "Property Schedule Selected",
                  description: `${prop.mouza_mr || prop.mouza_en} Plot ${prop.plot_no} copied for draft.`,
                });
                handleNavigate("new_draft");
              }}
            />
          )}

          {currentView === "document_archive" && (
            <DocumentsListView onNavigate={handleNavigate} isArchiveMode={true} initialStatusFilter="finalised" />
          )}

          {/* INTELLIGENCE */}
          {currentView === "document_quality" && (
            <DocumentQualityView onNavigate={handleNavigate} />
          )}

          {currentView === "validation_center" && (
            <ValidationCenterView onNavigate={handleNavigate} />
          )}

          {currentView === "advisory_center" && (
            <AdvisoryCenterView onNavigate={handleNavigate} />
          )}

          {currentView === "registration_data" && (
            <RegistrationDataView onNavigate={handleNavigate} />
          )}

          {/* ADMINISTRATION */}
          {currentView === "user_management" && (
            <UserManagementView onNavigate={handleNavigate} />
          )}

          {currentView === "roles_permissions" && (
            <RolesPermissionsView onNavigate={handleNavigate} />
          )}

          {currentView === "audit_trail" && (
            <AuditTrailView onNavigate={handleNavigate} />
          )}

          {currentView === "system_settings" && (
            <SystemSettingsView onNavigate={handleNavigate} />
          )}

          {currentView === "system_health" && (
            <SystemHealthView onNavigate={handleNavigate} />
          )}
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigateSection={(sec) => {
          handleNavigate("new_draft");
        }}
        onNavigateView={handleNavigate}
        onSaveDraft={() => {
          toast({
            type: "info",
            title: lang === "mr" ? "मसुदा जतन केला" : "Draft Saved",
            description: "Saved state synchronized.",
          });
        }}
        onExportDocx={() => {
          handleNavigate("new_draft");
        }}
        onLoadSample={() => {
          handleNavigate("new_draft");
        }}
        onClearForm={() => {}}
        onOpenShortcuts={() => setShortcutsOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Keyboard Shortcuts Modal */}
      <KeyboardShortcutsModal
        isOpen={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
      />

      {/* Authentication Login Modal */}
      <LoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <I18nProvider>
      <AuthProvider>
        <ToastProvider>
          <AppShell />
        </ToastProvider>
      </AuthProvider>
    </I18nProvider>
  );
};

export default App;
