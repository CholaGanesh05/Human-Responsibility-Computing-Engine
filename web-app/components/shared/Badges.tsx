import type { UrgencyLevel, ImpactLevel, ResponsibilityStatus } from "@/types/hrce";
import { cn } from "@/lib/utils";

// ─── Status Badge ────────────────────────────────────────────────────────────

const STATUS_MAP: Record<ResponsibilityStatus, { label: string; cls: string }> = {
    PENDING: { label: "Pending", cls: "bg-yellow-500/15 text-yellow-400 border-yellow-500/25" },
    ACTIVE: { label: "Active", cls: "bg-blue-500/15 text-blue-400 border-blue-500/25" },
    COMPLETED: { label: "Completed", cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25" },
    BLOCKED: { label: "Blocked", cls: "bg-red-500/15 text-red-400 border-red-500/25" },
};

export function StatusBadge({ status }: { status: ResponsibilityStatus }) {
    const { label, cls } = STATUS_MAP[status] ?? STATUS_MAP.PENDING;
    return (
        <span className={cn("badge-status border", cls)}>{label}</span>
    );
}

// ─── Urgency Chip ────────────────────────────────────────────────────────────

const URGENCY_MAP: Record<UrgencyLevel, { cls: string }> = {
    LOW: { cls: "bg-slate-500/15 text-slate-400 border-slate-500/25" },
    MEDIUM: { cls: "bg-amber-500/15 text-amber-400 border-amber-500/25" },
    HIGH: { cls: "bg-orange-500/15 text-orange-400 border-orange-500/25" },
    CRITICAL: { cls: "bg-red-500/15 text-red-400 border-red-500/25" },
};

export function UrgencyChip({ level }: { level: UrgencyLevel }) {
    const { cls } = URGENCY_MAP[level] ?? URGENCY_MAP.LOW;
    return (
        <span className={cn("badge-status border", cls)}>{level}</span>
    );
}

// ─── Risk Bar ────────────────────────────────────────────────────────────────

export function RiskBar({ score }: { score: number }) {
    const pct = Math.min(100, Math.max(0, score));
    const color =
        pct >= 75 ? "#ef4444"
            : pct >= 50 ? "#f97316"
                : pct >= 25 ? "#eab308"
                    : "#22c55e";

    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, background: color }}
                />
            </div>
            <span className="text-xs font-mono text-muted-foreground w-8 text-right">{pct}</span>
        </div>
    );
}

// ─── Effort Score Dots ───────────────────────────────────────────────────────

export function EffortDots({ score }: { score: number }) {
    return (
        <div className="flex gap-0.5">
            {Array.from({ length: 10 }).map((_, i) => (
                <div
                    key={i}
                    className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        i < score ? "bg-primary" : "bg-white/10"
                    )}
                />
            ))}
        </div>
    );
}
