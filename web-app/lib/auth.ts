// ─── HRCE Auth Utilities (Stage 11) ─────────────────────────────────────────
// Login/register API calls + localStorage token management.

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "hrce_access_token";

// ─── Token helpers ──────────────────────────────────────────────────────────

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
    const token = getToken();
    if (!token) return false;
    try {
        // Decode the JWT payload (no crypto verify — just check expiry)
        const payload = JSON.parse(atob(token.split(".")[1]));
        if (!payload.exp) return true;
        return payload.exp * 1000 > Date.now();
    } catch {
        return false;
    }
}

// ─── Auth API calls ─────────────────────────────────────────────────────────

export interface AuthToken {
    access_token: string;
    token_type: string;
}

export async function login(email: string, password: string): Promise<AuthToken> {
    const res = await fetch(`${BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Login failed" }));
        throw new Error(err.detail ?? "Login failed");
    }
    return res.json();
}

export async function register(
    email: string,
    password: string,
    fullName?: string
): Promise<AuthToken> {
    const res = await fetch(`${BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Registration failed" }));
        throw new Error(err.detail ?? "Registration failed");
    }
    return res.json();
}

export interface UserProfile {
    id: string;
    email: string;
    full_name: string | null;
    is_active: boolean;
    created_at: string;
}

export async function getMe(): Promise<UserProfile> {
    const token = getToken();
    const res = await fetch(`${BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get user profile");
    return res.json();
}
