"use client";

import { useState, useEffect } from "react";
import type { Responsibility } from "@/types/hrce";
import { StatusBadge, UrgencyChip, EffortDots } from "@/components/shared/Badges";
import { ChevronRight, ChevronDown, FlaskConical } from "lucide-react";
import { analyzeRisk, getAllResponsibilities } from "@/lib/api";
import { toast } from "sonner";
import { format } from "date-fns";

function ResponsibilityRow({
    r,
    depth = 0,
}: {
    r: Responsibility;
    depth?: number;
}) {
    const [expanded, setExpanded] = useState(depth === 0);
    const [analyzing, setAnalyzing] = useState(false);
    const hasSubs = r.sub_responsibilities && r.sub_responsibilities.length > 0;

    async function handleAnalyze(e: React.MouseEvent) {
        e.stopPropagation();
        setAnalyzing(true);
        try {
            await analyzeRisk(r.id);
            toast.success(`Risk analysis triggered for "${r.title}"`);
        } catch {
            toast.error("Backend unreachable — start the FastAPI server.");
        } finally {
            setAnalyzing(false);
        }
    }

    return (
        <>
            <tr
                className="border-b border-white/5 hover:bg-white/2 transition-colors cursor-pointer"
                onClick={() => hasSubs && setExpanded(!expanded)}
            >
                <td className="py-3 px-4">
                    <div className="flex items-center gap-1" style={{ paddingLeft: depth * 20 }}>
                        {hasSubs ? (
                            expanded ? (
                                <ChevronDown size={12} className="text-muted-foreground shrink-0" />
                            ) : (
                                <ChevronRight size={12} className="text-muted-foreground shrink-0" />
                            )
                        ) : (
                            <span className="w-3 shrink-0" />
                        )}
                        <span className="text-sm font-medium text-foreground">{r.title}</span>
                    </div>
                </td>
                <td className="py-3 px-3">
                    <StatusBadge status={r.status} />
                </td>
                <td className="py-3 px-3">
                    <UrgencyChip level={r.urgency} />
                </td>
                <td className="py-3 px-3">
                    <EffortDots score={r.effort_score} />
                </td>
                <td className="py-3 px-3 text-xs text-muted-foreground">
                    {r.due_date ? format(new Date(r.due_date), "MMM d, yyyy") : "—"}
                </td>
                <td className="py-3 px-3">
                    <button
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-accent/15 text-accent border border-accent/25 hover:bg-accent/25 transition-colors disabled:opacity-50"
                    >
                        <FlaskConical size={11} />
                        {analyzing ? "Analyzing…" : "Analyze Risk"}
                    </button>
                </td>
            </tr>
            {expanded &&
                hasSubs &&
                r.sub_responsibilities!.map((sub) => (
                    <ResponsibilityRow key={sub.id} r={sub} depth={depth + 1} />
                ))}
        </>
    );
}

export default function ResponsibilitiesPage() {
    const [responsibilities, setResponsibilities] = useState<Responsibility[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            setLoading(true);
            try {
                const data = await getAllResponsibilities();
                setResponsibilities(data);
            } catch {
                toast.error("Failed to load responsibilities — backend offline?");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="page-header">Responsibilities</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Full responsibility tree with status, urgency, and effort tracking
                </p>
            </div>

            <div className="glass rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/8">
                                {["Responsibility", "Status", "Urgency", "Effort", "Due Date", "Actions"].map((h) => (
                                    <th
                                        key={h}
                                        className="text-left py-3 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider first:px-4"
                                    >
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-12 text-sm text-muted-foreground">
                                        Loading responsibilities…
                                    </td>
                                </tr>
                            ) : responsibilities.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-16 text-sm text-muted-foreground">
                                        No responsibilities found. Run the extraction agent on an event first.
                                    </td>
                                </tr>
                            ) : (
                                responsibilities.map((r) => (
                                    <ResponsibilityRow key={r.id} r={r} />
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
