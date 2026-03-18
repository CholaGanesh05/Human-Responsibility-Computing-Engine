"use client";

import { useState, useEffect, useCallback } from "react";
import { getEvents, createEvent } from "@/lib/api";
import type { HRCEEvent } from "@/types/hrce";
import { CalendarDays, MapPin, Clock, Plus, X, RefreshCw, Loader2 } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";

function EventCard({ ev }: { ev: HRCEEvent }) {
    const prepHours = Math.round(ev.preparation_time_minutes / 60);
    return (
        <div className="glass rounded-xl p-5 space-y-3 hover:border-primary/20 transition-all duration-200">
            <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold text-foreground">{ev.title}</h3>
                {ev.is_all_day && (
                    <span className="badge-status bg-purple-500/15 text-purple-400 border border-purple-500/25 shrink-0">
                        All Day
                    </span>
                )}
            </div>
            {ev.description && (
                <p className="text-xs text-muted-foreground line-clamp-2">{ev.description}</p>
            )}
            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                    <CalendarDays size={11} />
                    {format(new Date(ev.start_time), "MMM d, yyyy")}
                </span>
                {ev.location && (
                    <span className="flex items-center gap-1">
                        <MapPin size={11} />
                        {ev.location}
                    </span>
                )}
                <span className="flex items-center gap-1">
                    <Clock size={11} />
                    {prepHours}h prep window
                </span>
            </div>
        </div>
    );
}

interface EventFormData {
    title: string;
    description: string;
    start_time: string;
    end_time: string;
    location: string;
    preparation_time_minutes: number;
}

function CreateEventModal({
    onClose,
    onCreated,
}: {
    onClose: () => void;
    onCreated: (ev: HRCEEvent) => void;
}) {
    const [form, setForm] = useState<EventFormData>({
        title: "",
        description: "",
        start_time: "",
        end_time: "",
        location: "",
        preparation_time_minutes: 60,
    });
    const [submitting, setSubmitting] = useState(false);

    const set = (k: keyof EventFormData, v: string | number) =>
        setForm((p) => ({ ...p, [k]: v }));

    async function handleSubmit() {
        if (!form.title || !form.start_time || !form.end_time) {
            toast.warning("Title, start time and end time are required.");
            return;
        }
        setSubmitting(true);
        try {
            const ev = await createEvent({
                title: form.title,
                description: form.description || undefined,
                start_time: new Date(form.start_time).toISOString(),
                end_time: new Date(form.end_time).toISOString(),
                location: form.location || undefined,
                preparation_time_minutes: form.preparation_time_minutes,
            });
            onCreated(ev);
            toast.success(`Event "${ev.title}" created! AI is decomposing responsibilities in the background.`);
            onClose();
        } catch {
            toast.error("Failed to create event — is the backend running?");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="glass rounded-2xl p-6 w-full max-w-lg mx-4 space-y-5 animate-fade-in">
                <div className="flex items-center justify-between">
                    <h2 className="text-base font-semibold text-foreground">Create Event</h2>
                    <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5 transition-colors">
                        <X size={16} className="text-muted-foreground" />
                    </button>
                </div>

                <div className="space-y-3">
                    {(
                        [
                            { label: "Title *", key: "title", type: "text", placeholder: "Event title" },
                            { label: "Description", key: "description", type: "text", placeholder: "Optional description" },
                            { label: "Start Time *", key: "start_time", type: "datetime-local", placeholder: "" },
                            { label: "End Time *", key: "end_time", type: "datetime-local", placeholder: "" },
                            { label: "Location", key: "location", type: "text", placeholder: "Room / URL" },
                        ] as const
                    ).map(({ label, key, type, placeholder }) => (
                        <div key={key}>
                            <label className="block text-xs font-medium text-muted-foreground mb-1">{label}</label>
                            <input
                                type={type}
                                placeholder={placeholder}
                                value={form[key] as string}
                                onChange={(e) => set(key, e.target.value)}
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-primary/50"
                            />
                        </div>
                    ))}

                    <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1">
                            Preparation Time (minutes)
                        </label>
                        <input
                            type="number"
                            min={0}
                            value={form.preparation_time_minutes}
                            onChange={(e) => set("preparation_time_minutes", Number(e.target.value))}
                            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50"
                        />
                    </div>
                </div>

                <div className="flex gap-3 pt-2">
                    <button
                        onClick={onClose}
                        disabled={submitting}
                        className="flex-1 py-2 rounded-lg border border-white/10 text-sm text-muted-foreground hover:bg-white/5 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={submitting}
                        className="flex-1 py-2 rounded-lg text-sm font-semibold text-black transition-colors flex items-center justify-center gap-2"
                        style={{ background: "hsl(var(--primary))" }}
                    >
                        {submitting ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
                        {submitting ? "Creating…" : "Create Event"}
                    </button>
                </div>
                <p className="text-xs text-center text-muted-foreground/60">
                    AI will auto-generate responsibilities for this event in the background
                </p>
            </div>
        </div>
    );
}

export default function EventsPage() {
    const [showCreate, setShowCreate] = useState(false);
    const [events, setEvents] = useState<HRCEEvent[]>([]);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getEvents();
            setEvents(data);
        } catch {
            setEvents([]);
            toast.error("Failed to load events — backend offline?");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    function handleCreated(ev: HRCEEvent) {
        setEvents((prev) => [ev, ...prev]);
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="page-header">Events</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        {events.length} event{events.length !== 1 ? "s" : ""}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={load}
                        className="p-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors"
                    >
                        <RefreshCw size={13} className={`text-muted-foreground ${loading ? "animate-spin" : ""}`} />
                    </button>
                    <button
                        onClick={() => setShowCreate(true)}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-black transition-all hover:opacity-90"
                        style={{ background: "hsl(var(--primary))" }}
                    >
                        <Plus size={15} />
                        Create Event
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="text-sm text-muted-foreground text-center py-16">Loading events…</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {events.map((ev) => (
                        <EventCard key={ev.id} ev={ev} />
                    ))}
                </div>
            )}

            {showCreate && (
                <CreateEventModal
                    onClose={() => setShowCreate(false)}
                    onCreated={handleCreated}
                />
            )}
        </div>
    );
}
