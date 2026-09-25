export interface Entity {
  id: string;
  entity_type: string;
  name: string;
  criticality: string;
  attributes: Record<string, unknown>;
  created_at: string;
}

export interface Detection {
  id: string;
  entity_id: string;
  category: string;
  level: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  silence_started_at: string;
  detected_at: string;
  expected_summary: string;
  observed_summary: string;
  evidence: Record<string, unknown>;
  status: string;
  review_verdict: string;
}

export interface AgentStatus {
  id: string;
  host_id: string;
  agent_version: string;
  last_seen_at: string | null;
  seconds_since_last_seen: number | null;
  cpu_percent: number;
  memory_mb: number;
  queue_depth: number;
  dropped_events_total: number;
  status: "online" | "degraded" | "offline";
}

export interface PostureSummary {
  entity_count: number;
  open_detections: number;
  critical_open_detections: number;
  detections_last_24h: number;
  active_incidents: number;
  missing_relationships: number;
  agents_total: number;
  agents_online: number;
  blind_spot_ratio: number;
}

export interface BusinessHoursStatus {
  is_open: boolean;
  current_window: [string, string] | null;
  next_open_at: string | null;
  seconds_until_next_open: number | null;
  next_window_duration_seconds: number | null;
}

export interface BusinessHoursRow {
  id: string;
  entity_id: string | null;
  name: string;
  timezone: string;
  schedule: Record<string, [string, string][]>;
  is_maintenance_window: boolean;
  active: boolean;
}
