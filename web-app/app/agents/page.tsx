"use client";

import { useState } from "react";
import {
    Bot,
    Brain,
    FileText,
    Loader2,
    ChevronDown,
    ChevronUp,
    Sparkles,
    CheckCircle2,
    Clock,
    AlertTriangle,
    Zap,
} from "lucide-react";
import { toast } from "sonner";
import {
    agentDecompose,
    agentSummarize,
    getEvents,
    type DecompositionResult,
    type ContextSummaryResult,
    type ResponsibilityProposal,
} from "@/lib/api";
import type { Event } from "@/types/hrce";

// ─── Priority styling ─────────────────────────────────────────────────────────
const PRIORITY_STYLES: Record<string, string> = {
    LOW:      "bg-slate-500/15 text-slate-300 border-slate-500/30",
    MEDIUM:   "bg-amber-500/15 text-amber-300 border-amber-500/30",
    HIGH:     "bg-orange-500/15 text-orange-300 border-orange-500/30",
    CRITICAL: "bg-red-500/15 text-red-300 border-red-500/30",
};

const PRIORITY_ICON: Record<string, React.ReactNode> = {
    LOW:      <Clock size={10} />,
    MEDIUM:   <AlertTriangle size={10} />,
    HIGH:     <AlertTriangle size={10} />,
    CRITICAL: <Zap size={10} />,
};

function PriorityChip({ level }: { level: string }) {
    const style = PRIORITY_STYLES[level] ?? PRIORITY_STYLES.MEDIUM;
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${style}`}>
            {PRIORITY_ICON[level]}
            {level}
        </span>
    );
}

// ─── Decomposition result card ────────────────────────────────────────────────
function DecompositionCard({ result }: { result: DecompositionResult }) {
    const [open, setOpen] = useState(true);
    return (
        <div className="glass rounded-xl overflow-hidden animate-fade-in">
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/8">
                <div className="flex items-center gap-2">
                    <Brain size={16} className="text-primary" />
                    <span className="text-sm font-semibold text-foreground">
                        Decomposition — {result.event_title}
                    </span>
                    <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/15 text-primary border border-primary/25">
                        {result.responsibilities.length} proposals
                    </span>
                </div>
                <button
                    onClick={() => setOpen((v) => !v)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                >
                    {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
            </div>

            {open && (
                <>
                    <div className="px-5 py-3 bg-white/2 border-b border-white/5">
                        <p className="text-xs text-muted-foreground italic">
                            <span className="text-foreground font-medium">AI reasoning: </span>
                            {result.reasoning}
                        </p>
                    </div>
                    <div className="divide-y divide-white/5">
                        {result.responsibilities.map((r, i) => (
                            <ResponsibilityRow key={i} proposal={r} index={i} />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

function ResponsibilityRow({ proposal, index }: { proposal: ResponsibilityProposal; index: number }) {
    return (
        <div className="px-5 py-3.5 flex items-start gap-4 hover:bg-white/2 transition-colors">
            <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-muted-foreground bg-white/5 flex-shrink-0 mt-0.5">
                {index + 1}
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-sm font-medium text-foreground">{proposal.title}</span>
                    <PriorityChip level={proposal.priority} />
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{proposal.description}</p>
            </div>
            <div className="flex-shrink-0 text-right">
                <div className="text-xs font-semibold text-muted-foreground">{proposal.estimated_effort_hours}h</div>
                <div className="text-[10px] text-muted-foreground/60">effort</div>
            </div>
        </div>
    );
}

// ─── Context summary result card ──────────────────────────────────────────────
function SummaryCard({ result }: { result: ContextSummaryResult }) {
    return (
        <div className="glass rounded-xl overflow-hidden animate-fade-in">
            <div className="flex items-center gap-2 px-5 py-4 border-b border-white/8">
                <FileText size={16} className="text-accent" />
                <span className="text-sm font-semibold text-foreground">
                    Context Summary
                </span>
                <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-accent/15 text-accent border border-accent/25">
                    {result.document_count} {result.document_count === 1 ? "doc" : "docs"}
                </span>
            </div>
            <div className="px-5 py-4 space-y-4">
                <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Summary</div>
                    <p className="text-sm text-foreground/90 leading-relaxed">{result.summary}</p>
                </div>
                {result.key_points.length > 0 && (
                    <div>
                        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Key Points</div>
                        <ul className="space-y-1.5">
                            {result.key_points.map((pt, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-foreground/85">
                                    <CheckCircle2 size={13} className="text-accent mt-0.5 flex-shrink-0" />
                                    <span>{pt}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function AgentsPage() {
    const [events, setEvents] = useState<Event[]>([]);
    const [eventsLoaded, setEventsLoaded] = useState(false);
    const [loadingEvents, setLoadingEvents] = useState(false);
    const [selectedEventId, setSelectedEventId] = useState("");

    const [decomposing, setDecomposing] = useState(false);
    const [summarising, setSummarising] = useState(false);
    const [decompositionResult, setDecompositionResult] = useState<DecompositionResult | null>(null);
    const [summaryResult, setSummaryResult] = useState<ContextSummaryResult | null>(null);

    async function loadEvents() {
        if (eventsLoaded) return;
        setLoadingEvents(true);
        try {
            const data = await getEvents(0, 50);
            setEvents(data);
            setEventsLoaded(true);
            if (data.length > 0) setSelectedEventId(data[0].id);
        } catch {
            toast.error("Could not load events — backend unreachable.");
        } finally {
            setLoadingEvents(false);
        }
    }

    async function handleDecompose() {
        if (!selectedEventId) return toast.error("Select an event first.");
        setDecomposing(true);
        setDecompositionResult(null);
        try {
            const result = await agentDecompose(selectedEventId);
            setDecompositionResult(result);
            toast.success(`Decomposed into ${result.responsibilities.length} responsibilities.`);
        } catch (err) {
            toast.error("Decomposition failed — agent service unreachable or GROQ_API_KEY not set.");
            console.error(err);
        } finally {
            setDecomposing(false);
        }
    }

    async function handleSummarise() {
        if (!selectedEventId) return toast.error("Select an event first.");
        setSummarising(true);
        setSummaryResult(null);
        try {
            const result = await agentSummarize(selectedEventId);
            setSummaryResult(result);
            toast.success("Context summary ready.");
        } catch (err) {
            toast.error("Summarisation failed — agent service unreachable or GROQ_API_KEY not set.");
            console.error(err);
        } finally {
            setSummarising(false);
        }
    }

    const busy = decomposing || summarising;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="page-header flex items-center gap-2">
                    <Bot size={24} className="text-accent" />
                    AI Agents
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Run LangGraph agents on your events to decompose responsibilities or summarise documents.
                </p>
            </div>

            {/* Control Panel */}
            <div className="glass rounded-xl p-5 space-y-4">
                <div className="flex items-center gap-2 mb-1">
                    <Sparkles size={14} className="text-primary" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Select Event
                    </span>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                    {/* Event picker */}
                    <select
                        id="agent-event-select"
                        className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-colors"
                        value={selectedEventId}
                        onChange={(e) => setSelectedEventId(e.target.value)}
                        onFocus={loadEvents}
                    >
                        {!eventsLoaded && (
                            <option value="" disabled>
                                {loadingEvents ? "Loading events…" : "Click to load events"}
                            </option>
                        )}
                        {eventsLoaded && events.length === 0 && (
                            <option value="" disabled>No events found</option>
                        )}
                        {events.map((ev) => (
                            <option key={ev.id} value={ev.id}>
                                {ev.title}
                            </option>
                        ))}
                    </select>

                    {/* Agent buttons */}
                    <div className="flex gap-2 flex-shrink-0">
                        <button
                            id="btn-decompose"
                            onClick={handleDecompose}
                            disabled={busy || !selectedEventId}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-primary/15 text-primary border border-primary/25 hover:bg-primary/25 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            {decomposing ? (
                                <Loader2 size={14} className="animate-spin" />
                            ) : (
                                <Brain size={14} />
                            )}
                            {decomposing ? "Decomposing…" : "Decompose"}
                        </button>

                        <button
                            id="btn-summarise"
                            onClick={handleSummarise}
                            disabled={busy || !selectedEventId}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-accent/15 text-accent border border-accent/25 hover:bg-accent/25 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            {summarising ? (
                                <Loader2 size={14} className="animate-spin" />
                            ) : (
                                <FileText size={14} />
                            )}
                            {summarising ? "Summarising…" : "Summarise Docs"}
                        </button>
                    </div>
                </div>

                {/* How-it-works pills */}
                <div className="flex flex-wrap gap-2 pt-1">
                    {[
                        { icon: <Brain size={10} />, color: "text-primary", label: "Decompose — LangGraph fetches the event then uses Groq LLM to propose responsibilities" },
                        { icon: <FileText size={10} />, color: "text-accent",  label: "Summarise — LangGraph fetches attached documents then summarises them with key points" },
                    ].map(({ icon, color, label }) => (
                        <div key={label} className={`flex items-center gap-1.5 text-[11px] text-muted-foreground`}>
                            <span className={color}>{icon}</span>
                            {label}
                        </div>
                    ))}
                </div>
            </div>

            {/* Results */}
            {(decompositionResult || summaryResult) && (
                <div className="space-y-4">
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-0.5">
                        Results
                    </div>
                    {decompositionResult && <DecompositionCard result={decompositionResult} />}
                    {summaryResult && <SummaryCard result={summaryResult} />}
                </div>
            )}

            {/* Empty state */}
            {!decompositionResult && !summaryResult && !busy && (
                <div className="glass rounded-xl p-16 flex flex-col items-center justify-center gap-4 text-center">
                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center glow-accent"
                        style={{ background: "oklch(0.55 0.2 295 / 0.12)", border: "1px solid oklch(0.55 0.2 295 / 0.2)" }}>
                        <Bot size={28} className="text-accent" />
                    </div>
                    <div>
                        <div className="text-sm font-semibold text-foreground">No results yet</div>
                        <div className="text-xs text-muted-foreground mt-1 max-w-xs">
                            Select an event and click Decompose or Summarise Docs to run an AI agent.
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
