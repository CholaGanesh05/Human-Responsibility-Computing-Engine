// ─── HRCE Type Definitions ─────────────────────────────────────────────────
// These mirror the backend SQLAlchemy models from Stages 2–7.

export type ResponsibilityStatus = "PENDING" | "ACTIVE" | "COMPLETED" | "BLOCKED";
export type UrgencyLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ImpactLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type ComplexityLevel = "LOW" | "MEDIUM" | "HIGH";
export type PreparationStatus = "NOT_STARTED" | "IN_PROGRESS" | "READY";
export type NotificationType =
    | "REMINDER"
    | "ESCALATION"
    | "MISSED"
    | "PREPARATION_DUE"
    | "DEPENDENCY_BLOCKED";

// ─── Event ─────────────────────────────────────────────────────────────────
export interface HRCEEvent {
    id: string;
    title: string;
    description?: string;
    start_time: string; // ISO-8601
    end_time: string;
    is_all_day: boolean;
    location?: string;
    recurrence_rule?: string;
    preparation_time_minutes: number;
    owner_id: string;
    created_at: string;
    updated_at: string;
}

/** Alias — used in Stage 10 CRUD APIs */
export type Event = HRCEEvent;

// ─── Responsibility ─────────────────────────────────────────────────────────
export interface Responsibility {
    id: string;
    title: string;
    description?: string;
    status: ResponsibilityStatus;
    priority: number;
    due_date?: string;
    effort_score: number;
    complexity_level: ComplexityLevel;
    urgency: UrgencyLevel;
    impact: ImpactLevel;
    preparation_status: PreparationStatus;
    event_id: string;
    parent_id?: string;
    assigned_to_id?: string;
    sub_responsibilities?: Responsibility[];
    created_at: string;
    updated_at: string;
}

// ─── Notification ──────────────────────────────────────────────────────────
export interface Notification {
    id: string;
    type: NotificationType;
    message: string;
    is_read: boolean;
    responsibility_id?: string;
    created_at: string;
}

export interface NotificationsResponse {
    user_id: string;
    count: number;
    notifications: Notification[];
}

// ─── Risk ──────────────────────────────────────────────────────────────────
export interface RiskScore {
    responsibility_id: string;
    risk_score: number;
    urgency: UrgencyLevel;
    impact: ImpactLevel;
    due_date?: string;
}

// ─── Document ─────────────────────────────────────────────────────────────
export interface HRCEDocument {
    id: string;
    title: string;
    score?: string;
}

// ─── WebSocket Payload ─────────────────────────────────────────────────────
export type WSEventType = "notification" | "responsibility_update" | "risk_update";

export interface WSPayload {
    event: WSEventType;
    timestamp: string;
    data: Record<string, unknown>;
}
