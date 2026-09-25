const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("ns-token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; role: string; tenant_id: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  postureSummary: () => request("/api/v1/posture/summary"),
  listDetections: (status?: string) =>
    request(`/api/v1/detections${status ? `?status_filter=${status}` : ""}`),
  triggerSweep: () => request("/api/v1/detections/sweep", { method: "POST" }),
  reviewDetection: (id: string, verdict: string, note = "") =>
    request(`/api/v1/detections/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ verdict, note }),
    }),
  listEntities: (entityType?: string) =>
    request(`/api/v1/entities${entityType ? `?entity_type=${entityType}` : ""}`),
  createEntity: (body: { entity_type: string; name: string; criticality?: string }) =>
    request("/api/v1/entities", { method: "POST", body: JSON.stringify(body) }),
  listAgents: () => request("/api/v1/agents"),
  listBusinessHours: () => request("/api/v1/business-hours"),
  createBusinessHours: (body: unknown) =>
    request("/api/v1/business-hours", { method: "POST", body: JSON.stringify(body) }),
  businessHoursStatus: (id: string) => request(`/api/v1/business-hours/${id}/status`),
  deleteBusinessHours: (id: string) => request(`/api/v1/business-hours/${id}`, { method: "DELETE" }),
  listCases: () => request("/api/v1/cases"),
  createCase: (body: unknown) => request("/api/v1/cases", { method: "POST", body: JSON.stringify(body) }),
  relationshipGraph: () => request("/api/v1/relationships/graph"),
  query: (body: unknown) => request("/api/v1/query", { method: "POST", body: JSON.stringify(body) }),
};

export function wsUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  return `${base}${path}`;
}
