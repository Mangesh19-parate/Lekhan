/**
 * Centralized Typed API Client for Lekhan (TypeScript).
 *
 * Generated from OpenAPI 3.1 specification (PRD FR-11, FR-13, Features F-054 to F-067).
 * Provides strictly typed responses, automatic CSRF injection, and structured error handling.
 * Strict TypeScript: ZERO `any` types permitted (AGENTS.md Section 5).
 */

export class ApiError extends Error {
  status: number;
  code?: string;
  correlationId?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, correlationId?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
    this.details = details;
  }
}

// In-memory CSRF token storage (never localStorage per security protocol)
let memoryCsrfToken: string | null = null;

export function setMemoryCsrfToken(token: string | null): void {
  memoryCsrfToken = token;
}

export function getMemoryCsrfToken(): string | null {
  return memoryCsrfToken;
}

export function getCsrfTokenFromStorage(): string | null {
  return memoryCsrfToken;
}

// --- OpenAPI Response & Request Types ---

export interface JobEnqueueResponse {
  job_id: string;
  status: string;
  state: string;
  document_id?: string | null;
  doc_no?: string | null;
  download_url?: string | null;
  pdf_url?: string | null;
  job?: { id: string; state: string } | null;
}

export interface JobDetailResponse {
  id: string;
  status: string;
  state: string;
  document_id?: string | null;
  attempts: number;
  error?: { code: string; message: string; correlation_id?: string;[key: string]: unknown } | null;
  retryable: boolean;
  outputs: { docx: boolean; pdf: boolean };
  download_url?: string | null;
  pdf_url?: string | null;
}

export interface DocumentSummaryItem {
  id: string;
  doc_no: string;
  status: string;
  language: string;
  engine_version: string;
  created_at: string;
  docx_download_url: string;
  pdf_download_url: string;
  data_snapshot?: Record<string, unknown>;
}

export interface DocumentHistoryResponse {
  items: DocumentSummaryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentDetailResponse {
  id: string;
  doc_no: string;
  status: string;
  language: string;
  engine_version: string;
  template_version_id: string;
  data_snapshot: Record<string, unknown>;
  created_at: string;
  docx_download_url: string;
  pdf_download_url: string;
}

export interface ValidationViolation {
  id?: string;
  path?: string;
  code?: string;
  severity?: string;
  message?: string;
  message_en?: string;
  message_mr?: string;
  fields?: string[];
}

export interface ValidationResponse {
  valid: boolean;
  derived_fields: Record<string, unknown>;
  violations: ValidationViolation[];
  visibility: Record<string, boolean>;
}

export interface DashboardStatsResponse {
  draft_count: number;
  review_count: number;
  finalised_count: number;
  templates_count: number;
  drafts_in_progress?: number;
  pending_reviews?: number;
  finalised_documents?: number;
  approved_templates?: number;
  language_distribution?: { mr?: number; en?: number; [key: string]: number | undefined };
  operational_alerts?: Array<{
    id: string;
    type: string;
    message: string;
    severity?: string;
    title_mr?: string;
    title_en?: string;
    action_url?: string;
  }>;
  document_type_distribution?: Record<string, number>;
  recent_activity?: Array<{
    id: string;
    action: string;
    title: string;
    timestamp: string;
    actor: string;
    entity?: string;
    entity_id?: string;
    meta?: Record<string, unknown>;
  }>;
}

export interface TemplateSummaryItem {
  template_id: string;
  name_en: string;
  name_mr: string;
  version: number | string;
  status: string;
  language?: string;
  document_type?: string;
  property_type?: string;
  has_docx?: boolean;
  submitted_by?: string | null;
  approved_by?: string | null;
  id?: string;
  name?: string;
  sections_count?: number;
  updated_at?: string;
}

export interface TemplateSection {
  id: string;
  title?: string;
  title_en?: string;
  title_mr?: string;
  fields?: Record<string, unknown>;
  field_names?: string[];
}

export interface TemplateManifest {
  template_id: string;
  version: number;
  title?: string;
  name_en?: string;
  name_mr?: string;
  language: string;
  sections?: TemplateSection[];
  fields?: Record<string, unknown>;
  rules?: unknown[];
}

export interface LintReport {
  is_clean?: boolean;
  valid?: boolean;
  can_approve?: boolean;
  errors: Array<{ code: string; message: string; path?: string }>;
  warnings: Array<{ code: string; message: string; path?: string }>;
  unused_fields?: string[];
  leftover_data?: Array<{ category?: string; count?: number; masked_sample?: string;[key: string]: unknown }>;
  fonts?: string[];
  split_runs_repaired?: number;
  [key: string]: unknown;
}

export interface TemplateUploadResponse {
  version: number;
  status: string;
  lint_report: LintReport;
}

export interface PartyItem {
  id: string;
  name_en: string;
  name_mr: string;
  category?: string;
  pan?: string;
  aadhaar_hash?: string;
  address?: Record<string, unknown>;
  attrs?: Record<string, unknown>;
}

export interface PropertyItem {
  id: string;
  survey_number: string;
  village: string;
  district: string;
  category?: string;
  area_sqft?: number;
  ready_reckoner_rate?: number;
  attrs?: Record<string, unknown>;
}

export interface ReviewStatusResponse {
  status: string;
  doc_id: string;
  reviewer?: string;
  reviewed_at?: string;
  checklist?: Record<string, boolean>;
  comments?: string;
}

export interface AdvisoryRule {
  id: string;
  title: string;
  category: string;
  severity: "info" | "warning" | "critical";
  description: string;
  statutory_citation?: string;
  title_mr?: string;
  title_en?: string;
  rule_name?: string;
  statutory_ref?: string;
  advice_mr?: string;
  advice_en?: string;
  action_needed?: string;
}

export interface AdvisoryEvaluationItem {
  rule_id: string;
  severity: string;
  message: string;
  statutory_ref?: string;
}

export interface PortalSheetResponse {
  document_id: string;
  parties_text: string;
  property_text: string;
  market_value_text: string;
  copy_paste_text?: string;
  property?: Record<string, unknown>;
}

export interface UserItem {
  id: string;
  email: string;
  display_name?: string;
  role: string;
  active: boolean;
  mfa_enabled?: boolean;
  created_at: string;
  ui_language?: string;
}

export interface SeparationOfDutiesRule {
  rule?: string;
  role1?: string;
  role2?: string;
  reason?: string;
  description?: string;
  enforced_at?: string;
}

export interface RolesPermissionsResponse {
  roles: string[];
  matrix?: Record<string, string[]>;
  separation_of_duties?: SeparationOfDutiesRule[];
}

export interface AuditRecord {
  id: number;
  action: string;
  entity: string;
  entity_id?: string | null;
  timestamp: string;
  actor_id?: string | null;
  hash: string;
  prev_hash?: string;
  meta?: Record<string, unknown>;
  actor?: string;
}

export interface AuditTrailResponse {
  chain_valid: boolean;
  total_records: number;
  records: AuditRecord[];
}

export interface SystemHealthResponse {
  status: string;
  db_connected: boolean;
  uptime_seconds: number;
  worker_active: boolean;
  worker_queue?: Record<string, unknown>;
  api?: {
    status: string;
    uptime_seconds?: number;
    version?: string;
    environment?: string;
    docs_url?: string;
  };
  database?: {
    status: string;
    connected?: boolean;
    latency_ms?: number;
    pool_size?: number;
    adapter?: string;
    connection_pooling?: string;
  };
  storage?: {
    status: string;
    writeable?: boolean;
    path?: string;
    type?: string;
    free_space_gb?: number;
  };
  template_engine?: {
    status: string;
    templates_loaded?: number;
    total_templates?: number;
    approved_templates?: number;
  };
  [key: string]: unknown;
}

export interface DocumentQualityResponse {
  document_id: string;
  timestamp: string;
  overall_status: string;
  score: string;
  can_approve: boolean;
  is_clean: boolean;
  blocking_errors: Array<{ code: string; severity: string; message: string; part?: string; paragraph_idx?: number }>;
  warnings: Array<{ code: string; severity: string; message: string; part?: string; paragraph_idx?: number }>;
  leftover_data: Array<{ category: string; count: number; part: string; paragraph_idx: number; masked_sample: string }>;
  passed_checks: Array<{ name: string; description: string }>;
  split_runs_repaired: number;
  fonts: string[];
}

export interface SystemSettingsResponse {
  retention_class: string;
  digits_setting: string;
  idle_minutes: number;
  tenant_id: string;
}

export interface DraftItem {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  template_id?: string | null;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MfaSetupResponse {
  secret: string;
  otpauth_uri: string;
  recovery_codes: string[];
}

export interface MfaVerifyResponse {
  status: string;
  verified: boolean;
  message?: string;
  recovery_code_used?: boolean;
}

export interface ProvenanceVerificationResponse {
  valid: boolean;
  tampered: boolean;
  document_id?: string | null;
  tenant_id?: string | null;
  template_version_id?: string | null;
  template_sha256?: string | null;
  engine_version?: string | null;
  expected_document_hash?: string | null;
  actual_document_hash?: string | null;
  generated_at?: string | null;
  verified_at?: string | null;
  message?: string | null;
}

export interface PilotStatsResponse {
  total_logged: number;
  total_resolved: number;
  total_pending: number;
  blocking_count: number;
  resolution_rate_percent: number;
  category_breakdown: Record<string, number>;
  template_breakdown: Record<string, number>;
  avg_corrections_per_draft: number;
  weekly_trend?: Array<Record<string, unknown>>;
  top_corrections_resolved?: string[];
}

export interface PartyDuplicateMatch {
  party_id: string;
  names?: Record<string, string>;
  pan?: string;
  match_type: string;
  similarity: number;
  reason: string;
}

export interface PropertyDuplicateMatch {
  property_id: string;
  category?: string;
  survey_number: string;
  village: string;
  match_type: string;
  reason: string;
}

// --- Base Fetcher ---

export async function apiClient<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const csrf = getMemoryCsrfToken();
  if (csrf && !headers.has("X-CSRF-Token")) {
    headers.set("X-CSRF-Token", csrf);
  }

  const res = await fetch(endpoint, {
    ...options,
    headers,
    credentials: "include",
  });

  const correlationId = res.headers.get("X-Correlation-ID") || undefined;

  if (!res.ok) {
    let errorDetail = res.statusText;
    let errorCode = "API_ERROR";
    let extraData: unknown = null;

    try {
      const errJson = (await res.json()) as Record<string, unknown>;
      errorDetail = (errJson.detail || errJson.message || errorDetail) as string;
      errorCode = (errJson.code || errorCode) as string;
      extraData = errJson;
    } catch {
      // Body wasn't JSON
    }

    throw new ApiError(errorDetail, res.status, errorCode, correlationId, extraData);
  }

  if (res.status === 204) {
    return {} as T;
  }

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }

  // Handle explicit binary downloads (DOCX, PDF)
  if (
    endpoint.includes("/download") ||
    endpoint.includes("/export") ||
    endpoint.endsWith(".docx") ||
    endpoint.endsWith(".pdf")
  ) {
    return (await res.blob()) as unknown as T;
  }

  throw new ApiError(
    `API endpoint ${endpoint} returned non-JSON response (${contentType || "empty"}). The backend service may be offline or misconfigured.`,
    res.status,
    "INVALID_CONTENT_TYPE",
    correlationId
  );
}

// --- Typed API Surface ---

export const api = {
  // Dashboard
  getDashboardStats: (): Promise<DashboardStatsResponse> =>
    apiClient<DashboardStatsResponse>("/api/v1/dashboard/stats"),

  // Documents
  listDocuments: (params?: {
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<DocumentHistoryResponse> => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.search) q.set("search", params.search);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return apiClient<DocumentHistoryResponse>(`/api/v1/documents${qs ? `?${qs}` : ""}`);
  },

  getDocument: (id: string): Promise<DocumentDetailResponse> =>
    apiClient<DocumentDetailResponse>(`/api/v1/documents/${id}`),

  generateDocument: (
    payload: Record<string, unknown>,
    idempotencyKey?: string
  ): Promise<JobEnqueueResponse> =>
    apiClient<JobEnqueueResponse>("/api/v1/documents", {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
      body: JSON.stringify(payload),
    }),

  getJob: (jobId: string): Promise<JobDetailResponse> =>
    apiClient<JobDetailResponse>(`/api/v1/jobs/${jobId}`),

  validateDraftData: (
    templateId: string,
    data: Record<string, unknown>
  ): Promise<ValidationResponse> =>
    apiClient<ValidationResponse>(`/api/v1/documents/validate/${templateId}`, {
      method: "POST",
      body: JSON.stringify({ data }),
    }),

  // Review
  getReviewStatus: (docId: string): Promise<ReviewStatusResponse> =>
    apiClient<ReviewStatusResponse>(`/api/v1/documents/${docId}/review`),

  markReviewed: (
    docId: string,
    checklist: Record<string, boolean>
  ): Promise<ReviewStatusResponse> =>
    apiClient<ReviewStatusResponse>(`/api/v1/documents/${docId}/review`, {
      method: "POST",
      body: JSON.stringify(checklist),
    }),

  finaliseDocument: (docId: string): Promise<{ status: string; doc_id: string }> =>
    apiClient<{ status: string; doc_id: string }>(`/api/v1/documents/${docId}/finalise`, {
      method: "POST",
    }),

  reopenDocument: (docId: string): Promise<{ status: string; doc_id: string }> =>
    apiClient<{ status: string; doc_id: string }>(`/api/v1/documents/${docId}/reopen`, {
      method: "POST",
    }),

  // Templates
  listTemplates: (): Promise<TemplateSummaryItem[]> =>
    apiClient<TemplateSummaryItem[]>("/api/v1/templates"),

  getTemplateManifest: (templateId: string): Promise<TemplateManifest> =>
    apiClient<TemplateManifest>(`/api/v1/templates/${templateId}/manifest`),

  lintTemplate: (templateId: string): Promise<LintReport> =>
    apiClient<LintReport>(`/api/v1/templates/${templateId}/lint`, { method: "POST" }),

  uploadTemplate: (formData: FormData): Promise<TemplateUploadResponse> =>
    apiClient<TemplateUploadResponse>("/api/v1/templates/upload", {
      method: "POST",
      body: formData,
    }),

  // Parties & Properties
  searchParties: (q: string): Promise<PartyItem[]> =>
    apiClient<PartyItem[]>(`/api/v1/parties/search?q=${encodeURIComponent(q)}`),

  createParty: (payload: Record<string, unknown>): Promise<PartyItem> =>
    apiClient<PartyItem>("/api/v1/parties", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  searchProperties: (q: string, category?: string): Promise<PropertyItem[]> => {
    const qp = new URLSearchParams({ q });
    if (category) qp.set("category", category);
    return apiClient<PropertyItem[]>(`/api/v1/properties/search?${qp.toString()}`);
  },

  createProperty: (payload: Record<string, unknown>): Promise<PropertyItem> =>
    apiClient<PropertyItem>("/api/v1/properties", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Advisory & Registration
  getAdvisoryRules: (): Promise<AdvisoryRule[]> =>
    apiClient<AdvisoryRule[]>("/api/v1/advisory/rules"),

  evaluateAdvisories: (payload: {
    template_id?: string;
    data: Record<string, unknown>;
  }): Promise<AdvisoryEvaluationItem[]> =>
    apiClient<AdvisoryEvaluationItem[]>("/api/v1/advisory/evaluate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getPortalSheet: (docId: string): Promise<PortalSheetResponse> =>
    apiClient<PortalSheetResponse>(`/api/v1/documents/${docId}/portal-sheet`),

  // Administration
  getUsers: (): Promise<UserItem[]> => apiClient<UserItem[]>("/api/v1/admin/users"),

  toggleUserStatus: (
    userId: string,
    active: boolean,
    role?: string
  ): Promise<UserItem> =>
    apiClient<UserItem>(`/api/v1/admin/users/${userId}/status`, {
      method: "POST",
      body: JSON.stringify({ active, role }),
    }),

  getRolesPermissions: (): Promise<RolesPermissionsResponse> =>
    apiClient<RolesPermissionsResponse>("/api/v1/admin/roles"),

  getAuditTrail: (): Promise<AuditTrailResponse> =>
    apiClient<AuditTrailResponse>("/api/v1/admin/audit"),

  getSystemHealth: (): Promise<SystemHealthResponse> =>
    apiClient<SystemHealthResponse>("/api/v1/admin/system-health"),

  getSystemSettings: (): Promise<SystemSettingsResponse> =>
    apiClient<SystemSettingsResponse>("/api/v1/admin/settings"),

  updateSystemSettings: (
    payload: Partial<SystemSettingsResponse>
  ): Promise<SystemSettingsResponse> =>
    apiClient<SystemSettingsResponse>("/api/v1/admin/settings", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  // Quality Inspection
  checkDocumentQuality: (id: string): Promise<DocumentQualityResponse> =>
    apiClient<DocumentQualityResponse>(`/api/v1/documents/${id}/quality`, {
      method: "POST",
    }),

  // Drafts
  listDrafts: (): Promise<DraftItem[]> =>
    apiClient<DraftItem[]>("/api/v1/drafts"),

  createDraft: (payload: {
    title?: string;
    template_id?: string;
    data?: Record<string, unknown>;
  }): Promise<DraftItem> =>
    apiClient<DraftItem>("/api/v1/drafts", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getDraft: (id: string): Promise<DraftItem> =>
    apiClient<DraftItem>(`/api/v1/drafts/${id}`),

  updateDraft: (
    id: string,
    payload: {
      title?: string;
      template_id?: string;
      data?: Record<string, unknown>;
    }
  ): Promise<DraftItem> =>
    apiClient<DraftItem>(`/api/v1/drafts/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deleteDraft: (id: string): Promise<void> =>
    apiClient<void>(`/api/v1/drafts/${id}`, {
      method: "DELETE",
    }),

  // Template Lifecycle & Separation of Duties
  submitTemplate: (
    templateId: string
  ): Promise<{ template_id: string; version: number; status: string }> =>
    apiClient<{ template_id: string; version: number; status: string }>(
      `/api/v1/templates/${templateId}/submit`,
      { method: "POST" }
    ),

  approveTemplate: (
    templateId: string
  ): Promise<{ template_id: string; version: number; status: string }> =>
    apiClient<{ template_id: string; version: number; status: string }>(
      `/api/v1/templates/${templateId}/approve`,
      { method: "POST" }
    ),

  retireTemplate: (
    templateId: string
  ): Promise<{ template_id: string; version: number; status: string }> =>
    apiClient<{ template_id: string; version: number; status: string }>(
      `/api/v1/templates/${templateId}/retire`,
      { method: "POST" }
    ),

  // Auth & Security (MFA & Password)
  setupMfa: (): Promise<MfaSetupResponse> =>
    apiClient<MfaSetupResponse>("/api/v1/auth/mfa/setup", { method: "POST" }),

  enableMfa: (payload: {
    code: string;
    password: string;
  }): Promise<{ status: string; message: string }> =>
    apiClient<{ status: string; message: string }>("/api/v1/auth/mfa/enable", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  verifyMfa: (payload: {
    code?: string;
    recovery_code?: string;
  }): Promise<MfaVerifyResponse> =>
    apiClient<MfaVerifyResponse>("/api/v1/auth/mfa/verify", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  disableMfa: (payload: {
    code: string;
    password: string;
  }): Promise<{ status: string; message: string }> =>
    apiClient<{ status: string; message: string }>("/api/v1/auth/mfa/disable", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  changePassword: (payload: {
    current_password: string;
    new_password: string;
  }): Promise<{ status: string; message: string }> =>
    apiClient<{ status: string; message: string }>("/api/v1/auth/password", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Audit Verification & Export
  verifyAuditTrail: (): Promise<{
    tenant_id: string;
    chain_valid: boolean;
    tamper_detected: boolean;
  }> =>
    apiClient<{
      tenant_id: string;
      chain_valid: boolean;
      tamper_detected: boolean;
    }>("/api/v1/admin/audit/verify"),

  exportAuditTrail: (): Promise<Record<string, unknown>> =>
    apiClient<Record<string, unknown>>("/api/v1/admin/audit/export"),

  // Document Verification & PDF
  verifyDocument: (
    docId: string
  ): Promise<ProvenanceVerificationResponse> =>
    apiClient<ProvenanceVerificationResponse>(`/api/v1/documents/${docId}/verify`),

  getDocumentPdfUrl: (docId: string): string => `/api/v1/documents/${docId}/pdf`,

  // Parties & Properties Reuse and Duplicates
  reuseParty: (
    partyId: string,
    overrides?: Record<string, unknown>
  ): Promise<PartyItem> =>
    apiClient<PartyItem>(`/api/v1/parties/${partyId}/reuse`, {
      method: "POST",
      body: JSON.stringify({ overrides: overrides || {} }),
    }),

  detectDuplicateParties: (payload: {
    name?: string;
    pan?: string;
    threshold?: number;
  }): Promise<PartyDuplicateMatch[]> =>
    apiClient<PartyDuplicateMatch[]>("/api/v1/parties/detect-duplicates", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  reuseProperty: (
    propertyId: string,
    overrides?: Record<string, unknown>
  ): Promise<PropertyItem> =>
    apiClient<PropertyItem>(`/api/v1/properties/${propertyId}/reuse`, {
      method: "POST",
      body: JSON.stringify({ overrides: overrides || {} }),
    }),

  detectDuplicateProperties: (payload: {
    survey_number?: string;
    village?: string;
  }): Promise<PropertyDuplicateMatch[]> =>
    apiClient<PropertyDuplicateMatch[]>("/api/v1/properties/detect-duplicates", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Pilot Stats
  getPilotStats: (): Promise<PilotStatsResponse> =>
    apiClient<PilotStatsResponse>("/api/v1/pilot/stats"),
};
