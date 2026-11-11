/**
 * Centralized API client for Lekhan (TypeScript).
 * Provides typed requests, automatic CSRF token injection, and structured error handling.
 */

export class ApiError extends Error {
  status: number;
  code?: string;
  correlationId?: string;
  details?: any;

  constructor(message: string, status: number, code?: string, correlationId?: string, details?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
    this.details = details;
  }
}

export function getCsrfTokenFromStorage(): string | null {
  return localStorage.getItem("lekhan_csrf_token");
}

export async function apiClient<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const csrf = getCsrfTokenFromStorage();
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
    let extraData: any = null;

    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
      errorCode = errJson.code || errorCode;
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

export const api = {
  // Dashboard
  getDashboardStats: () => apiClient<any>("/api/v1/dashboard/stats"),

  // Documents
  listDocuments: (params?: { status?: string; search?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.search) q.set("search", params.search);
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.offset) q.set("offset", String(params.offset));
    const qs = q.toString();
    return apiClient<any>(`/api/v1/documents${qs ? `?${qs}` : ""}`);
  },
  getDocument: (id: string) => apiClient<any>(`/api/v1/documents/${id}`),
  generateDocument: (payload: any, idempotencyKey?: string) =>
    apiClient<any>("/api/v1/documents", {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
      body: JSON.stringify(payload),
    }),
  validateDraftData: (templateId: string, data: any) =>
    apiClient<any>(`/api/v1/documents/validate/${templateId}`, {
      method: "POST",
      body: JSON.stringify({ data }),
    }),

  // Review
  getReviewStatus: (docId: string) => apiClient<any>(`/api/v1/documents/${docId}/review`),
  markReviewed: (docId: string, checklist: any) =>
    apiClient<any>(`/api/v1/documents/${docId}/review`, {
      method: "POST",
      body: JSON.stringify(checklist),
    }),
  finaliseDocument: (docId: string) =>
    apiClient<any>(`/api/v1/documents/${docId}/finalise`, { method: "POST" }),
  reopenDocument: (docId: string) =>
    apiClient<any>(`/api/v1/documents/${docId}/reopen`, { method: "POST" }),

  // Templates
  listTemplates: () => apiClient<any[]>("/api/v1/templates"),
  getTemplateManifest: (templateId: string) =>
    apiClient<any>(`/api/v1/templates/${templateId}/manifest`),
  lintTemplate: (templateId: string) =>
    apiClient<any>(`/api/v1/templates/${templateId}/lint`, { method: "POST" }),
  uploadTemplate: (formData: FormData) =>
    apiClient<any>("/api/v1/templates/upload", {
      method: "POST",
      body: formData,
    }),

  // Parties & Properties
  searchParties: (q: string) =>
    apiClient<any[]>(`/api/v1/parties/search?q=${encodeURIComponent(q)}`),
  createParty: (payload: any) =>
    apiClient<any>("/api/v1/parties", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  searchProperties: (q: string, category?: string) => {
    const qp = new URLSearchParams({ q });
    if (category) qp.set("category", category);
    return apiClient<any[]>(`/api/v1/properties/search?${qp.toString()}`);
  },
  createProperty: (payload: any) =>
    apiClient<any>("/api/v1/properties", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Advisory & Registration
  getAdvisoryRules: () => apiClient<any[]>("/api/v1/advisory/rules"),
  evaluateAdvisories: (payload: { template_id?: string; data: any }) =>
    apiClient<any[]>("/api/v1/advisory/evaluate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getPortalSheet: (docId: string) =>
    apiClient<any>(`/api/v1/documents/${docId}/portal-sheet`),

  // Administration
  getUsers: () => apiClient<any[]>("/api/v1/admin/users"),
  toggleUserStatus: (userId: string, active: boolean, role?: string) =>
    apiClient<any>(`/api/v1/admin/users/${userId}/status`, {
      method: "POST",
      body: JSON.stringify({ active, role }),
    }),
  getRolesPermissions: () => apiClient<any>("/api/v1/admin/roles"),
  getAuditTrail: () => apiClient<any>("/api/v1/admin/audit"),
  getSystemHealth: () => apiClient<any>("/api/v1/admin/system-health"),
};

