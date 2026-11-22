import React, { useState, useEffect, useMemo, useCallback } from "react";
import { I18nProvider, useI18n } from "./shared/i18n";
import { ToastProvider, useToast, Button, Badge, ErrorBoundary } from "./shared/components";
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
import { SecuritySettingsView } from "./features/admin/SecuritySettingsView";
import { PilotStatsView } from "./features/admin/PilotStatsView";
import { StepperWizard } from "./features/drafting/StepperWizard";

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
  Menu,
  X,
} from "lucide-react";

type ViewId =
  | "overview"
  | "wizard"
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
  | "system_health"
  | "security_settings"
  | "pilot_stats"
  | "not_found";

interface NavItem {
  id: ViewId;
  labelEn: string;
  labelMr: string;
  icon: React.ComponentType<{ size?: number | string; className?: string; color?: string }>;
  badge?: string;
}

interface NavSection {
  titleEn: string;
  titleMr: string;
  items: NavItem[];
}

const NAVIGATION_SECTIONS: NavSection[] = [
  {
    titleEn: "DRAFTING & MATTERS",
    titleMr: "मसुदा व प्रकरणे",
    items: [
      { id: "overview", labelEn: "Chamber Overview", labelMr: "दफ्तर आढावा", icon: LayoutDashboard },
      { id: "wizard", labelEn: "Drafting Wizard", labelMr: "मसुदा सहाय्यक", icon: Sparkles },
      { id: "new_draft", labelEn: "New Deed Draft", labelMr: "नवीन दस्त मसुदा", icon: FilePlus },
      { id: "my_documents", labelEn: "Deed Register", labelMr: "दस्तऐवज नोंदवही", icon: FileText },
      { id: "drafts_pending", labelEn: "Active Drafts", labelMr: "चालू मसुदे", icon: Clock },
      { id: "review_center", labelEn: "Advocate Review", labelMr: "वकील तपासणी", icon: ShieldCheck },
    ],
  },
  {
    titleEn: "CHAMBER REGISTERS",
    titleMr: "दफ्तर नोंदवह्या",
    items: [
      { id: "template_library", labelEn: "Approved Templates", labelMr: "मान्य साचे", icon: Layers },
      { id: "template_studio", labelEn: "Template Studio", labelMr: "साचा स्टुडिओ", icon: FileCode },
      { id: "party_directory", labelEn: "Party Directory", labelMr: "पक्षकार नोंदवही", icon: Users },
      { id: "property_directory", labelEn: "Property Register", labelMr: "मिळकत नोंदवही", icon: MapPin },
      { id: "document_archive", labelEn: "Deed Archive", labelMr: "अभिलेखागार", icon: Archive },
    ],
  },
  {
    titleEn: "STATUTORY VERIFICATION",
    titleMr: "वैधानिक पडताळणी",
    items: [
      { id: "document_quality", labelEn: "Quality & Lint Check", labelMr: "गुणवत्ता व लिंट", icon: CheckCircle2 },
      { id: "validation_center", labelEn: "Statutory Rules", labelMr: "कायदेशीर नियम", icon: Cpu },
      { id: "advisory_center", labelEn: "Legal Advisory", labelMr: "कायदेशीर सल्ला", icon: HelpCircle },
      { id: "registration_data", labelEn: "Sub-Registrar PDE", labelMr: "नोंदणी डेटा (PDE)", icon: ExternalLink },
    ],
  },
  {
    titleEn: "CHAMBER ADMIN",
    titleMr: "प्रशासन व नियंत्रण",
    items: [
      { id: "user_management", labelEn: "Users & Staff", labelMr: "वापरकर्ते", icon: UserCheck },
      { id: "roles_permissions", labelEn: "Roles & Sign-off", labelMr: "अधिकार व स्वाक्षरी", icon: Lock },
      { id: "system_settings", labelEn: "Chamber Settings", labelMr: "दफ्तर संरचना", icon: Settings },
      { id: "security_settings", labelEn: "Security & MFA", labelMr: "सुरक्षा व MFA", icon: Lock },
      { id: "audit_trail", labelEn: "Immutable Audit Trail", labelMr: "ऑडिट ट्रेल", icon: History },
      { id: "pilot_stats", labelEn: "Pilot Statistics", labelMr: "पायलट आकडेवारी", icon: Activity },
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
    const path = window.location.pathname;
    if (path !== "/" && path !== "/index.html") {
      return "not_found";
    }
    const saved = localStorage.getItem("lekhan_current_view");
    return (saved as ViewId) || "overview";
  });

  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    return localStorage.getItem("lekhan_sidebar_collapsed") === "true";
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // State transferred across views
  const [activeTemplateId, setActiveTemplateId] = useState<string | undefined>(undefined);
  const [resumeDraftData, setResumeDraftData] = useState<Record<string, unknown> | null>(null);

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
    if (window.location.pathname !== "/") {
      window.history.replaceState(null, "", "/");
    }
    setCurrentView(viewId as ViewId);
    setMobileMenuOpen(false);
    localStorage.setItem("lekhan_current_view", viewId);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleResumeDraft = useCallback((draft: Record<string, unknown>) => {
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
    if (currentView === "not_found") {
      return {
        sectionTitle: "Lekhan",
        itemTitle: lang === "mr" ? "पृष्ठ सापडले नाही (404)" : "Page Not Found (404)",
        icon: HelpCircle,
      };
    }
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

  useEffect(() => {
    document.title = `${activeNavMetadata.itemTitle} — Lekhan | लेखन`;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute(
        "content",
        `${activeNavMetadata.itemTitle} — Lekhan (लेखन) multilingual property legal drafting workspace.`
      );
    }
  }, [activeNavMetadata]);

  return (
    <div className="flex min-h-screen bg-canvas text-text-primary font-ui antialiased">
      {/* Accessible Skip Link for Keyboard Navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand-500 focus:text-white focus:rounded-pill focus:shadow-dialog focus:font-semibold focus:text-xs"
      >
        Skip to main content
      </a>
      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          className="lekhan-sidebar-backdrop open"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ------------------------------------------------------------- */}
      {/* SIDEBAR NAVIGATION                                            */}
      {/* ------------------------------------------------------------- */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 flex flex-col bg-brand-900 text-white border-r border-brand-800 transition-all duration-200 shadow-xl lg:shadow-none select-none ${
          mobileMenuOpen ? "translate-x-0 w-64" : "-translate-x-full lg:translate-x-0"
        } ${sidebarCollapsed ? "lg:w-16" : "lg:w-64"}`}
        aria-label="Primary Navigation"
      >
        {/* Brand Header (Logo links back to home) */}
        <div
          className={`h-16 flex items-center border-b border-white/10 px-4 ${
            sidebarCollapsed ? "justify-center" : "justify-between"
          }`}
        >
          <button
            type="button"
            onClick={() => handleNavigate("overview")}
            aria-label="Lekhan Home"
            className="flex items-center gap-2.5 overflow-hidden text-left focus:outline-none"
          >
            <div className="w-9 h-9 rounded-input bg-brand-500 text-white font-extrabold text-base flex items-center justify-center shrink-0 border border-approved-500/40 shadow-sm">
              लेख
            </div>
            {!sidebarCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-bold tracking-tight text-white leading-tight">
                  LEKHAN · लेखन
                </span>
                <span className="text-[10px] text-approved-400 font-medium truncate">
                  नागपूर व विदर्भ Chambers
                </span>
              </div>
            )}
          </button>

          <button
            onClick={toggleSidebar}
            aria-label="Toggle Navigation Sidebar"
            className={`p-1.5 rounded text-white/60 hover:text-white hover:bg-white/10 transition-colors hidden lg:flex ${
              sidebarCollapsed ? "hidden" : ""
            }`}
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            <ChevronLeft size={18} />
          </button>
        </div>

        {/* Navigation Sections */}
        <nav className="flex-1 overflow-y-auto p-2.5 space-y-5 focus:outline-none">
          {NAVIGATION_SECTIONS.map((section, sIdx) => (
            <div key={sIdx} className="space-y-1">
              {!sidebarCollapsed && (
                <div className="px-2.5 pb-1 text-[10px] font-bold tracking-wider text-white/40 uppercase">
                  {lang === "mr" ? section.titleMr : section.titleEn}
                </div>
              )}

              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive = currentView === item.id;
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavigate(item.id)}
                      title={sidebarCollapsed ? (lang === "mr" ? item.labelMr : item.labelEn) : undefined}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-input text-xs font-medium transition-colors ${
                        sidebarCollapsed ? "justify-center px-2" : "justify-start"
                      } ${
                        isActive
                          ? "bg-brand-800 text-white font-semibold border-l-4 border-brand-500 shadow-sm"
                          : "text-white/75 hover:bg-white/10 hover:text-white"
                      }`}
                    >
                      <Icon size={16} className={`shrink-0 ${isActive ? "text-brand-400" : "text-white/70"}`} />
                      {!sidebarCollapsed && (
                        <span className="truncate">{lang === "mr" ? item.labelMr : item.labelEn}</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User Profile Footer */}
        <div className="p-3 border-t border-white/10 bg-brand-900/60">
          {isAuthenticated && user ? (
            <div
              className={`flex items-center gap-2 ${
                sidebarCollapsed ? "justify-center" : "justify-between"
              }`}
            >
              {!sidebarCollapsed && (
                <div className="overflow-hidden">
                  <div className="text-xs font-semibold text-white truncate">
                    {user.email.split("@")[0]}
                  </div>
                  <div className="text-[11px] text-approved-400 font-medium">
                    {user.role} • {user.tenant_id}
                  </div>
                </div>
              )}
              <button
                onClick={logout}
                title="Sign Out"
                className="p-1.5 rounded text-white/60 hover:text-danger-500 hover:bg-white/10 transition-colors"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setLoginModalOpen(true)}
              className="w-full justify-center text-xs text-white border-white/20 bg-white/10 hover:bg-white/20"
            >
              <LogIn size={14} className={sidebarCollapsed ? "" : "mr-1.5"} />
              {!sidebarCollapsed && (lang === "mr" ? "लॉगिन करा" : "Sign In")}
            </Button>
          )}
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* MAIN CONTENT AREA                                             */}
      {/* ------------------------------------------------------------- */}
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        {/* Top Navigation Bar */}
        <header className="h-16 bg-card border-b border-line-subtle flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30 shadow-xs">
          {/* Left: Mobile Menu + Breadcrumb */}
          <div className="flex items-center gap-2 text-xs sm:text-sm min-w-0">
            <button
              type="button"
              className="lg:hidden p-1.5 rounded-input border border-line-subtle text-text-primary hover:bg-canvas transition-colors cursor-pointer"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
            <span className="hidden md:inline text-text-secondary font-medium">
              {activeNavMetadata.sectionTitle}
            </span>
            <span className="hidden md:inline text-text-muted">/</span>
            <div className="flex items-center gap-1.5 text-text-primary font-bold min-w-0">
              <activeNavMetadata.icon size={16} className="text-brand-600" />
              <span className="truncate">{activeNavMetadata.itemTitle}</span>
            </div>
          </div>

          {/* Center: Command Palette Trigger */}
          <button
            type="button"
            className="hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-input bg-canvas border border-line-subtle text-text-secondary hover:border-brand-500 text-xs transition-colors justify-between w-64 md:w-80 cursor-pointer"
            aria-label="Open quick action or search"
            onClick={() => setCommandPaletteOpen(true)}
          >
            <div className="flex items-center gap-2 truncate">
              <Search size={14} className="shrink-0 text-text-muted" />
              <span className="truncate">{lang === "mr" ? "शोध किंवा आज्ञा (Search deeds)..." : "Quick action or search (Ctrl+K)..."}</span>
            </div>
            <kbd className="bg-card border border-line-medium rounded px-1.5 py-0.5 text-[10px] font-semibold text-text-secondary font-mono shrink-0">
              ⌘K
            </kbd>
          </button>

          {/* Right: Controls & Toggles */}
          <div className="flex items-center gap-2 sm:gap-2.5">
            {/* Sync Status Badge */}
            <div className="hidden lg:flex items-center gap-1.5 text-xs text-brand-600 font-semibold px-2.5 py-1 rounded-pill bg-brand-500/10">
              <Check size={13} />
              <span>{lang === "mr" ? "सुरक्षित जोडलेले" : "Synced"}</span>
            </div>

            {/* Language Switcher (Trilingual: Marathi, English, Hindi) */}
            <div className="flex bg-canvas rounded-input p-0.5 border border-line-subtle">
              <button
                type="button"
                onClick={() => setLang("mr")}
                className={`px-2 py-1 rounded text-xs transition-all cursor-pointer ${
                  lang === "mr"
                    ? "bg-card text-brand-600 font-bold shadow-xs"
                    : "text-text-secondary hover:text-text-primary font-medium"
                }`}
              >
                मराठी
              </button>
              <button
                type="button"
                onClick={() => setLang("en")}
                className={`px-2 py-1 rounded text-xs transition-all cursor-pointer ${
                  lang === "en"
                    ? "bg-card text-brand-600 font-bold shadow-xs"
                    : "text-text-secondary hover:text-text-primary font-medium"
                }`}
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => setLang("hi")}
                className={`px-2 py-1 rounded text-xs transition-all cursor-pointer ${
                  lang === "hi"
                    ? "bg-card text-brand-600 font-bold shadow-xs"
                    : "text-text-secondary hover:text-text-primary font-medium"
                }`}
              >
                हिन्दी
              </button>
            </div>

            {/* Theme Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-1.5 sm:px-2 rounded-input border border-line-subtle text-text-primary hover:bg-canvas transition-colors cursor-pointer"
              title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
              aria-label="Toggle theme"
            >
              {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
            </button>

            {/* Shortcuts Guide */}
            <button
              type="button"
              onClick={() => setShortcutsOpen(true)}
              className="p-1.5 sm:px-2 rounded-input border border-line-subtle text-text-primary hover:bg-canvas transition-colors cursor-pointer"
              title="Keyboard Shortcuts (?)"
              aria-label="Keyboard Shortcuts"
            >
              <Keyboard size={16} />
            </button>
          </div>
        </header>

        {/* View Switcher Container */}
        <main id="main-content" className="flex-1 p-4 sm:p-6 overflow-y-auto bg-canvas">
          {/* WORKSPACE */}
          {currentView === "overview" && (
            <DashboardView onNavigate={handleNavigate} />
          )}

          {currentView === "wizard" && (
            <StepperWizard
              onSelectTemplate={(tmplId) => {
                setActiveTemplateId(tmplId);
                setCurrentView("new_draft");
              }}
              onNavigate={handleNavigate}
            />
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

          {currentView === "security_settings" && (
            <SecuritySettingsView onNavigate={handleNavigate} />
          )}

          {currentView === "pilot_stats" && (
            <PilotStatsView onNavigate={handleNavigate} />
          )}

          {currentView === "system_health" && (
            <SystemHealthView onNavigate={handleNavigate} />
          )}

          {currentView === "not_found" && (
            <div className="max-w-md mx-auto my-16 p-8 text-center bg-card rounded-card border border-line-subtle shadow-card">
              <div className="text-5xl font-extrabold text-brand-600 mb-2">404</div>
              <h1 className="text-xl font-bold text-text-primary mb-2">
                {lang === "mr" ? "पृष्ठ सापडले नाही" : "Page Not Found"}
              </h1>
              <p className="text-sm text-text-secondary mb-6">
                {lang === "mr"
                  ? "आपण शोधत असलेले पृष्ठ उपलब्ध नाही किंवा हलवले गेले आहे."
                  : "The page you requested does not exist or has been moved."}
              </p>
              <Button variant="primary" onClick={() => handleNavigate("overview")}>
                {lang === "mr" ? "मुख्यपृष्ठावर जा" : "Back to Overview"}
              </Button>
            </div>
          )}
        </main>

        {/* Compact App Footer */}
        <footer className="px-6 py-3 border-t border-line-subtle bg-card flex flex-wrap items-center justify-between gap-3 text-xs text-text-secondary">
          <span>© {new Date().getFullYear()} Lekhan (लेखन) — Property Legal Drafting</span>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => handleNavigate("system_health")}
              className="text-brand-600 hover:text-brand-700 cursor-pointer font-medium"
            >
              {lang === "mr" ? "प्रणाली स्थिती" : "System Health"}
            </button>
            <button
              type="button"
              onClick={() => setShortcutsOpen(true)}
              className="text-brand-600 hover:text-brand-700 cursor-pointer font-medium"
            >
              {lang === "mr" ? "शॉर्टकट्स (?)" : "Shortcuts (?)"}
            </button>
          </div>
        </footer>
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
        onClearForm={() => {
          localStorage.removeItem("lekhan_current_form");
          localStorage.removeItem("lekhan_current_repeaters");
          setResumeDraftData(null);
          toast({
            type: "info",
            title: lang === "mr" ? "मसुदा रिकामा केला" : "Draft Cleared",
            description: lang === "mr" ? "जतन केलेला फॉर्म डेटा काढून टाकला." : "Saved form data removed.",
          });
        }}
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
    <ErrorBoundary>
      <I18nProvider>
        <AuthProvider>
          <ToastProvider>
            <AppShell />
          </ToastProvider>
        </AuthProvider>
      </I18nProvider>
    </ErrorBoundary>
  );
};

export default App;
