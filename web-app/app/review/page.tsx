"use client";

import { useState, useEffect } from "react";
import type { Responsibility } from "@/types/hrce";
import { StatusBadge, UrgencyChip } from "@/components/shared/Badges";
import { Check, X, Pencil, Save, ClipboardCheck } from "lucide-react";
import { toast } from "sonner";
import { getAllResponsibilities, updateResponsibility } from "@/lib/api";

interface ReviewState {
    decision: "accepted" | "rejected" | "edited" | null;
    editTitle?: string;
    editing: boolean;
}

function flattenResponsibilities(list: Responsibility[]): Responsibility[] {
    const out: Responsibility[] = [];
    for (const r of list) {
        out.push(r);
        if (r.sub_responsibilities) out.push(...flattenResponsibilities(r.sub_responsibilities));
    }
    return out;
}

export default function ReviewPage() {
    const [responsibilities, setResponsibilities] = useState<Responsibility[]>([]);
    const [pageLoading, setPageLoading] = useState(true);
    const [states, setStates] = useState<Record<string, ReviewState>>({});

    useEffect(() => {
        async function load() {
            setPageLoading(true);
            try {
                const data = await getAllResponsibilities();
                setResponsibilities(flattenResponsibilities(data));
            } catch {
                toast.error("Failed to load responsibilities — backend offline?");
            } finally {
                setPageLoading(false);
            }
        }
        load();
    }, []);

    function getState(id: string): ReviewState {
        return states[id] ?? { decision: null, editing: false };
    }

    function patch(id: string, update: Partial<ReviewState>) {
        setStates((prev) => ({ ...prev, [id]: { ...getState(id), ...update } }));
    }

    async function accept(r: Responsibility) {
        patch(r.id, { decision: "accepted" });
        try {
            await updateResponsibility(r.id, { status: "ACTIVE" });
            toast.success(`Accepted: "${r.title}"`);
        } catch {
            toast.error("Failed to save acceptance to backend");
            patch(r.id, { decision: null });
        }
    }

    async function reject(r: Responsibility) {
        patch(r.id, { decision: "rejected" });
        try {
            await updateResponsibility(r.id, { status: "BLOCKED" });
            toast.error(`Rejected: "${r.title}"`);
        } catch {
            toast.error("Failed to save rejection to backend");
            patch(r.id, { decision: null });
        }
    }

    function startEdit(r: Responsibility) {
        patch(r.id, { editing: true, editTitle: getState(r.id).editTitle ?? r.title });
    }

    async function saveEdit(r: Responsibility) {
        const title = getState(r.id).editTitle ?? r.title;
        patch(r.id, { editing: false, decision: "edited" });
        try {
            await updateResponsibility(r.id, { title, status: "ACTIVE" });
            toast.success(`Edited: "${title}"`);
        } catch {
            toast.error("Failed to save edit to backend");
            patch(r.id, { decision: null, editing: true });
        }
    }

    const accepted = Object.values(states).filter((s) => s.decision === "accepted").length;
    const rejected = Object.values(states).filter((s) => s.decision === "rejected").length;
    const edited = Object.values(states).filter((s) => s.decision === "edited").length;
    const pending = responsibilities.length - accepted - rejected - edited;

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="page-header">Human-in-the-Loop Review</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Review AI-generated responsibilities. Accept, reject, or edit before execution.
                </p>
            </div>

            {/* Summary bar */}
            <div className="flex flex-wrap gap-3">
                {[
                    { label: "Pending", value: pending, cls: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" },
                    { label: "Accepted", value: accepted, cls: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
                    { label: "Edited", value: edited, cls: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
                    { label: "Rejected", value: rejected, cls: "bg-red-500/10 text-red-400 border-red-500/20" },
                ].map(({ label, value, cls }) => (
                    <div key={label} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium ${cls}`}>
                        <span>{label}</span>
                        <span className="font-bold">{value}</span>
                    </div>
                ))}

                <button
                    onClick={() => {
                        const all = Object.values(states);
                        const done = all.filter((s) => s.decision !== null).length;
                        if (done === 0) { toast.warning("No decisions made yet."); return; }
                        toast.success(`Submitted: ${accepted} accepted, ${edited} edited, ${rejected} rejected. Agent will proceed.`);
                    }}
                    className="ml-auto flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-semibold text-black"
                    style={{ background: "hsl(var(--primary))" }}
                >
                    <ClipboardCheck size={14} />
                    Submit Decisions
                </button>
            </div>

            <div className="space-y-3">
                {responsibilities.map((r) => {
                    const state = getState(r.id);
                    const bordered =
                        state.decision === "accepted" ? "border-emerald-500/30 bg-emerald-500/5"
                            : state.decision === "rejected" ? "border-red-500/30 bg-red-500/5 opacity-50"
                                : state.decision === "edited" ? "border-blue-500/30 bg-blue-500/5"
                                    : "border-white/8";

                    return (
                        <div
                            key={r.id}
                            className={`glass rounded-xl p-4 border transition-all duration-200 ${bordered}`}
                        >
                            <div className="flex items-start gap-4">
                                <div className="flex-1 min-w-0">
                                    {state.editing ? (
                                        <input
                                            autoFocus
                                            value={state.editTitle ?? r.title}
                                            onChange={(e) => patch(r.id, { editTitle: e.target.value })}
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50"
                                        />
                                    ) : (
                                        <p className="text-sm font-medium text-foreground">
                                            {state.decision === "edited" ? state.editTitle : r.title}
                                        </p>
                                    )}
                                    {r.description && (
                                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{r.description}</p>
                                    )}
                                    <div className="flex flex-wrap items-center gap-2 mt-2">
                                        <StatusBadge status={r.status} />
                                        <UrgencyChip level={r.urgency} />
                                        <span className="text-xs text-muted-foreground">Effort {r.effort_score}/10</span>
                                    </div>
                                </div>

                                {/* Action buttons */}
                                <div className="flex items-center gap-2 shrink-0">
                                    {state.editing ? (
                                        <button
                                            onClick={() => saveEdit(r)}
                                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-400 border border-blue-500/25 hover:bg-blue-500/25 transition-colors"
                                        >
                                            <Save size={11} />
                                            Save
                                        </button>
                                    ) : (
                                        <>
                                            {state.decision !== "accepted" && state.decision !== "rejected" && (
                                                <button
                                                    onClick={() => accept(r)}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/25 transition-colors"
                                                >
                                                    <Check size={11} />
                                                    Accept
                                                </button>
                                            )}
                                            {state.decision !== "rejected" && (
                                                <button
                                                    onClick={() => startEdit(r)}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-500/15 text-blue-400 border border-blue-500/25 hover:bg-blue-500/25 transition-colors"
                                                >
                                                    <Pencil size={11} />
                                                    Edit
                                                </button>
                                            )}
                                            {state.decision !== "accepted" && state.decision !== "rejected" && (
                                                <button
                                                    onClick={() => reject(r)}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/15 text-red-400 border border-red-500/25 hover:bg-red-500/25 transition-colors"
                                                >
                                                    <X size={11} />
                                                    Reject
                                                </button>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
                {pageLoading && (
                    <div className="text-center py-12 text-sm text-muted-foreground">
                        Loading responsibilities…
                    </div>
                )}
                {!pageLoading && responsibilities.length === 0 && (
                    <div className="text-center py-16 text-sm text-muted-foreground">
                        No responsibilities found. Run the extraction agent first.
                    </div>
                )}
            </div>
        </div>
    );
}
