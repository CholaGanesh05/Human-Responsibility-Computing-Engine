"use client";

import { useEffect, useState } from "react";
import {
    format,
    addMonths,
    subMonths,
    startOfMonth,
    endOfMonth,
    startOfWeek,
    endOfWeek,
    isSameMonth,
    isSameDay,
    addDays,
} from "date-fns";
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, CheckSquare2 } from "lucide-react";
import { getEvents, getAllResponsibilities } from "@/lib/api";
import type { HRCEEvent, Responsibility } from "@/types/hrce";

export default function CalendarPage() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState<HRCEEvent[]>([]);
    const [responsibilities, setResponsibilities] = useState<Responsibility[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            setLoading(true);
            try {
                const [evs, resps] = await Promise.all([
                    getEvents().catch(() => [] as HRCEEvent[]),
                    getAllResponsibilities().catch(() => [] as Responsibility[]),
                ]);
                setEvents(evs);
                setResponsibilities(resps);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [currentDate]);

    function renderHeader() {
        return (
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                    <h1 className="text-3xl font-bold tracking-tight">Timeline</h1>
                    <div className="text-xl font-medium text-muted-foreground flex items-center space-x-2">
                        <CalendarIcon size={20} />
                        <span>{format(currentDate, "MMMM yyyy")}</span>
                    </div>
                </div>
                <div className="flex space-x-2">
                    <button
                        onClick={() => setCurrentDate(subMonths(currentDate, 1))}
                        className="p-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-md transition-all"
                    >
                        <ChevronLeft size={20} />
                    </button>
                    <button
                        onClick={() => setCurrentDate(new Date())}
                        className="px-4 py-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-md text-sm font-medium transition-all"
                    >
                        Today
                    </button>
                    <button
                        onClick={() => setCurrentDate(addMonths(currentDate, 1))}
                        className="p-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-md transition-all"
                    >
                        <ChevronRight size={20} />
                    </button>
                </div>
            </div>
        );
    }

    function renderDays() {
        const days = [];
        const startDate = startOfWeek(startOfMonth(currentDate));

        for (let i = 0; i < 7; i++) {
            days.push(
                <div key={i} className="text-center font-medium text-sm text-muted-foreground py-2 border-b border-white/10">
                    {format(addDays(startDate, i), "EEEE")}
                </div>
            );
        }
        return <div className="grid grid-cols-7">{days}</div>;
    }

    function renderCells() {
        const monthStart = startOfMonth(currentDate);
        const monthEnd = endOfMonth(monthStart);
        const startDate = startOfWeek(monthStart);
        const endDate = endOfWeek(monthEnd);

        const rows = [];
        let days = [];
        let day = startDate;
        let formattedDate = "";

        while (day <= endDate) {
            for (let i = 0; i < 7; i++) {
                formattedDate = format(day, "d");
                const currentDay = day;

                // Match Events
                const dayEvents = events.filter((e) => isSameDay(new Date(e.start_time), currentDay));

                days.push(
                    <div
                        className={`min-h-[120px] p-2 border-b border-r border-white/5 transition-all
                        ${!isSameMonth(day, monthStart) ? "opacity-30 bg-black/20" : "hover:bg-white/5"}
                        ${isSameDay(day, new Date()) ? "bg-primary/5" : ""}
                        `}
                        key={day.toISOString()}
                    >
                        <div className="flex justify-end">
                            <span className={`text-sm font-medium w-6 h-6 flex items-center justify-center rounded-full ${isSameDay(day, new Date()) ? "bg-primary text-black" : ""}`}>{formattedDate}</span>
                        </div>
                        <div className="mt-2 space-y-2">
                            {dayEvents.map((evt) => (
                                <div key={evt.id} className="text-xs p-1.5 rounded-md bg-white/10 border border-white/20 truncate font-semibold">
                                    {evt.title}
                                </div>
                            ))}
                        </div>
                    </div>
                );
                day = addDays(day, 1);
            }
            rows.push(
                <div className="grid grid-cols-7" key={day.toISOString()}>
                    {days}
                </div>
            );
            days = [];
        }

        return <div className="border border-white/5 rounded-bl-xl rounded-br-xl backdrop-blur-md glass">{rows}</div>;
    }

    return (
        <div className="animate-fade-in">
            {renderHeader()}
            <div className="glass rounded-xl overflow-hidden border border-white/10 shadow-lg">
                {renderDays()}
                {loading ? (
                    <div className="h-[600px] flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    renderCells()
                )}
            </div>
            {/* Responsibilities Backlog */}
            <div className="mt-8">
                <h2 className="text-lg font-bold mb-4 flex items-center">
                    <CheckSquare2 className="mr-2 text-primary" size={20} />
                    Unscheduled Floating Responsibilities
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {responsibilities.slice(0, 3).map((r) => (
                        <div key={r.id} className="glass p-4 rounded-xl border border-white/10">
                            <h3 className="font-semibold text-sm">{r.title}</h3>
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{r.description}</p>
                        </div>
                    ))}
                    {responsibilities.length === 0 && !loading && (
                        <p className="text-muted-foreground text-sm pl-2">None active.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
