// ─── HRCE API Client (Stage 11 update) ──────────────────────────────────────
// All fetch wrappers for HRCE backend endpoints.
// Now attaches Authorization: Bearer token to all requests.

import type {
    NotificationsResponse,
    Notification,
    RiskScore,
    HRCEDocument,
} from "@/types/hrce";
import { getToken, clearToken } from "@/lib/auth";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(): Record<string, string> {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
        headers: {
            "Content-Type": "application/json",
            ...authHeaders(),
            ...init?.headers,
        },
        ...init,
    });
    if (!res.ok) {
        if (res.status === 401 && typeof window !== "undefined") {
            clearToken();
            window.location.href = "/login";
        }
        const text = await res.text();
        throw new Error(`API ${path} → ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
}

// ─── Notifications ─────────────────────────────────────────────────────────

export async function getNotifications(
    unreadOnly = false
): Promise<NotificationsResponse> {
    return apiFetch<NotificationsResponse>(
        `/api/v1/notifications?unread_only=${unreadOnly}`
    );
}

export async function markNotificationRead(
    notificationId: string
): Promise<Notification> {
    return apiFetch<Notification>(`/api/v1/notifications/${notificationId}/read`, {
        method: "PATCH",
    });
}

export async function triggerNotificationScan(): Promise<{
    status: string;
    task_id: string;
    message: string;
}> {
    return apiFetch(`/api/v1/notifications/trigger-scan`, { method: "POST" });
}

// ─── Risk ──────────────────────────────────────────────────────────────────

export async function getRiskScore(responsibilityId: string): Promise<RiskScore> {
    return apiFetch<RiskScore>(`/api/v1/risk/score/${responsibilityId}`);
}

export async function analyzeRisk(responsibilityId: string): Promise<unknown> {
    return apiFetch(`/api/v1/risk/analyze/${responsibilityId}`, { method: "POST" });
}

// ─── Documents ─────────────────────────────────────────────────────────────

export async function uploadDocument(
    file: File
): Promise<{ id: string; title: string; message: string }> {
    const form = new FormData();
    form.append("file", file);
    const token = getToken();
    const res = await fetch(`${BASE}/api/v1/documents/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Upload failed: ${res.status}: ${text}`);
    }
    return res.json();
}

export async function searchDocuments(
    q: string,
    limit = 5
): Promise<HRCEDocument[]> {
    return apiFetch<HRCEDocument[]>(
        `/api/v1/documents/search?q=${encodeURIComponent(q)}&limit=${limit}`
    );
}

// ─── Health ────────────────────────────────────────────────────────────────

export async function getHealthAll(): Promise<Record<string, string>> {
    return apiFetch<Record<string, string>>(`/api/v1/health/all`);
}

// ─── Events (Stage 10, Stage 11 auth update) ──────────────────────────────

import type { Event } from "@/types/hrce";

export async function getEvents(
    skip = 0,
    limit = 50
): Promise<Event[]> {
    return apiFetch<Event[]>(`/api/v1/events?skip=${skip}&limit=${limit}`);
}

export async function createEvent(data: {
    title: string;
    description?: string;
    start_time: string;
    end_time: string;
    is_all_day?: boolean;
    location?: string;
    preparation_time_minutes?: number;
}): Promise<Event> {
    return apiFetch<Event>(`/api/v1/events`, {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function getEventResponsibilities(
    eventId: string
): Promise<import("@/types/hrce").Responsibility[]> {
    return apiFetch(`/api/v1/events/${eventId}/responsibilities`);
}

// ─── Responsibilities (Stage 10) ────────────────────────────────────────────

export async function getAllResponsibilities(
    skip = 0,
    limit = 200
): Promise<import("@/types/hrce").Responsibility[]> {
    return apiFetch(`/api/v1/responsibilities?skip=${skip}&limit=${limit}`);
}

export async function updateResponsibility(
    id: string,
    data: Partial<import("@/types/hrce").Responsibility>
): Promise<import("@/types/hrce").Responsibility> {
    return apiFetch(`/api/v1/responsibilities/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
    });
}

// ─── Agent Service (Stage 5) ────────────────────────────────────────────────

const AGENT_BASE =
    process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:8001";

async function agentFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${AGENT_BASE}${path}`, {
        headers: {
            "Content-Type": "application/json",
            ...authHeaders(),
            ...init?.headers,
        },
        ...init,
    });
    if (!res.ok) {
        if (res.status === 401 && typeof window !== "undefined") {
            clearToken();
            window.location.href = "/login";
        }
        const text = await res.text();
        throw new Error(`Agent ${path} → ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
}

export interface ResponsibilityProposal {
    title: string;
    description: string;
    priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    estimated_effort_hours: number;
}

export interface DecompositionResult {
    event_id: string;
    event_title: string;
    responsibilities: ResponsibilityProposal[];
    reasoning: string;
}

export interface ContextSummaryResult {
    event_id: string;
    document_count: number;
    summary: string;
    key_points: string[];
}

/** Decompose an event into responsibility proposals via the AI agent. */
export async function agentDecompose(eventId: string): Promise<DecompositionResult> {
    return agentFetch<DecompositionResult>("/agents/decompose", {
        method: "POST",
        body: JSON.stringify({ event_id: eventId }),
    });
}

/** Summarise documents attached to an event via the AI agent. */
export async function agentSummarize(eventId: string): Promise<ContextSummaryResult> {
    return agentFetch<ContextSummaryResult>("/agents/summarize", {
        method: "POST",
        body: JSON.stringify({ event_id: eventId }),
    });
}
