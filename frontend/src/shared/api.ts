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
  error?: { code: string; message: string; correlation_id?: string; [key: string]: unknown } | null;
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
  path: string;
  code: string;
  message: string;
  message_mr?: string;
  message_en?: string;
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
  operational_alerts?: Array<{ id: string; type: string; message: string; severity?: string }>;
  document_type_distribution?: Record<string, number>;
  recent_activity?: Array<{ id: string; action: string; title: string; timestamp: string; actor: string }>;
}

export interface TemplateSummaryItem {
  id?: string;
  template_id: string;
  name?: string;
  name_en?: string;
  name_mr?: string;
  version: number;
  status: string;
  language: string;
  document_type?: string;
  property_type?: string;
  has_docx?: boolean;
  sections_count?: number;
  updated_at?: string;
}

export interface TemplateSection {
  id: string;
  title: string;
  fields: Record<string, unknown>;
}

export interface TemplateManifest {
  template_id: string;
  version: number;
  title: string;
  language: string;
  sections?: TemplateSection[];
  fields?: Record<string, unknown>;
  rules?: unknown[];
}

export interface LintReport {
  valid: boolean;
  errors: Array<{ code: string; message: string; path?: string }>;
  warnings: Array<{ code: string; message: string; path?: string }>;
  unused_fields?: string[];
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
}

export interface UserItem {
  id: string;
  email: string;
  role: string;
  active: boolean;
  created_at: string;
  ui_language?: string;
}

export interface RolesPermissionsResponse {
  roles: string[];
  matrix?: Record<string, string[]>;
  separation_of_duties?: Array<{ role1: string; role2: string; reason: string }>;
}

export interface AuditRecord {
  id: number;
  actor: string;
  action: string;
  entity: string;
  entity_id?: string;
  timestamp: string;
  hash?: string;
}

export interface AuditTrailResponse {
  records: AuditRecord[];
  verified: boolean;
}

export interface SystemHealthResponse {
  status: string;
  db_connected: boolean;
  uptime_seconds: number;
  worker_active: boolean;
  worker_queue?: Record<string, unknown>;
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

  return (await res.blob()) as unknown as T;
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
};
