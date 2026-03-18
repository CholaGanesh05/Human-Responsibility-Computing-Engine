"use client";

import { useState, useEffect } from "react";
import type { Responsibility } from "@/types/hrce";
import { getRiskScore, analyzeRisk, getAllResponsibilities } from "@/lib/api";
import { RiskBar, StatusBadge, UrgencyChip } from "@/components/shared/Badges";
import { ShieldAlert, Brain, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

interface RiskResult {
    id: string;
    score: number | null;
    loading: boolean;
}

function flattenResponsibilities(list: Responsibility[]): Responsibility[] {
    const out: Responsibility[] = [];
    for (const r of list) {
        out.push(r);
        if (r.sub_responsibilities) out.push(...flattenResponsibilities(r.sub_responsibilities));
    }
    return out;
}

export default function RiskPage() {
    const [allResponsibilities, setAllResponsibilities] = useState<Responsibility[]>([]);
    const [riskMap, setRiskMap] = useState<Record<string, RiskResult>>({});

    useEffect(() => {
        async function load() {
            try {
                const data = await getAllResponsibilities();
                setAllResponsibilities(flattenResponsibilities(data));
            } catch {
                toast.error("Failed to load responsibilities — backend offline?");
            }
        }
        load();
    }, []);

    function setRisk(id: string, patch: Partial<RiskResult>) {
        setRiskMap((prev) => ({
            ...prev,
            [id]: { ...(prev[id] || { score: null, loading: false }), ...patch, id },
        }));
    }

    async function fetchScore(r: Responsibility) {
        setRisk(r.id, { loading: true });
        try {
            const res = await getRiskScore(r.id);
            setRisk(r.id, { score: res.risk_score, loading: false });
        } catch {
            setRisk(r.id, { loading: false });
            toast.error(`Score unavailable for "${r.title}" — backend unreachable`);
        }
    }

    async function fetchAnalysis(r: Responsibility) {
        setRisk(r.id, { loading: true });
        try {
            await analyzeRisk(r.id);
            toast.success(`AI analysis triggered for "${r.title}"`);
            await fetchScore(r);
        } catch {
            setRisk(r.id, { loading: false });
            toast.error("Analysis failed — backend unreachable.");
        }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="page-header">Risk</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    View and compute risk scores for all responsibilities
                </p>
            </div>

            <div className="glass rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/8">
                                {["Responsibility", "Status", "Urgency", "Due Date", "Risk Score", "Actions"].map((h) => (
                                    <th
                                        key={h}
                                        className="text-left py-3 px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider"
                                    >
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {allResponsibilities.map((r) => {
                                const riskState = riskMap[r.id];
                                return (
                                    <tr key={r.id} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                                        <td className="py-3 px-4">
                                            <div className="text-sm font-medium text-foreground">{r.title}</div>
                                            <div className="text-xs text-muted-foreground">Effort {r.effort_score}/10</div>
                                        </td>
                                        <td className="py-3 px-4">
                                            <StatusBadge status={r.status} />
                                        </td>
                                        <td className="py-3 px-4">
                                            <UrgencyChip level={r.urgency} />
                                        </td>
                                        <td className="py-3 px-4 text-xs text-muted-foreground">
                                            {r.due_date ? format(new Date(r.due_date), "MMM d, yyyy") : "—"}
                                        </td>
                                        <td className="py-3 px-4 w-40">
                                            {riskState?.score != null ? (
                                                <RiskBar score={riskState.score} />
                                            ) : (
                                                <span className="text-xs text-muted-foreground/50">Not fetched</span>
                                            )}
                                        </td>
                                        <td className="py-3 px-4">
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => fetchScore(r)}
                                                    disabled={riskState?.loading}
                                                    className="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-white/5 text-muted-foreground border border-white/8 hover:bg-white/10 transition-colors disabled:opacity-50"
                                                >
                                                    {riskState?.loading ? (
                                                        <Loader2 size={10} className="animate-spin" />
                                                    ) : (
                                                        <ShieldAlert size={10} />
                                                    )}
                                                    Score
                                                </button>
                                                <button
                                                    onClick={() => fetchAnalysis(r)}
                                                    disabled={riskState?.loading}
                                                    className="flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 transition-colors disabled:opacity-50"
                                                >
                                                    <Brain size={10} />
                                                    AI Analyze
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
