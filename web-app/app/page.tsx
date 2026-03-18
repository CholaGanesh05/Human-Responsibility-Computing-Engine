"use client";

import { useEffect, useState } from "react";
import {
  CalendarDays, CheckSquare2, ShieldAlert, Bell,
  TrendingUp, Clock, AlertTriangle, Activity
} from "lucide-react";
import { getEvents, getAllResponsibilities, getNotifications } from "@/lib/api";
import type { Notification, HRCEEvent, Responsibility } from "@/types/hrce";
import { StatusBadge, UrgencyChip } from "@/components/shared/Badges";
import { format } from "date-fns";

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

function StatCard({ icon, label, value, sub, color = "var(--primary)" }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
        <div className="p-2 rounded-lg" style={{ background: `${color}18` }}>
          <div style={{ color }}>{icon}</div>
        </div>
      </div>
      <div className="text-3xl font-bold text-foreground">{value}</div>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [events, setEvents] = useState<HRCEEvent[]>([]);
  const [responsibilities, setResponsibilities] = useState<Responsibility[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [notifsRes, eventsData, respData] = await Promise.all([
          getNotifications().catch(() => ({ notifications: [] as Notification[], total: 0 })),
          getEvents().catch(() => [] as HRCEEvent[]),
          getAllResponsibilities().catch(() => [] as Responsibility[]),
        ]);
        setNotifications(notifsRes.notifications);
        setEvents(eventsData);
        setResponsibilities(respData);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const activeEvents = events.length;
  const openResponsibilities = responsibilities.filter((r) => r.status !== "COMPLETED").length;
  const criticalCount = responsibilities.filter((r) => r.urgency === "CRITICAL").length;
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="page-header">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Overview of your responsibilities and obligations
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          icon={<CalendarDays size={16} />}
          label="Active Events"
          value={loading ? "—" : activeEvents}
          sub="Upcoming obligations"
          color="hsl(199 89% 48%)"
        />
        <StatCard
          icon={<CheckSquare2 size={16} />}
          label="Open Responsibilities"
          value={loading ? "—" : openResponsibilities}
          sub={`${responsibilities.length} total`}
          color="hsl(268 75% 57%)"
        />
        <StatCard
          icon={<ShieldAlert size={16} />}
          label="Critical Items"
          value={loading ? "—" : criticalCount}
          sub="Require immediate action"
          color="hsl(0 84% 60%)"
        />
        <StatCard
          icon={<Bell size={16} />}
          label="Unread Notifications"
          value={loading ? "—" : unreadCount}
          sub="Live from backend"
          color="hsl(38 92% 50%)"
        />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Upcoming Events */}
        <section className="glass rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Clock size={15} className="text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Upcoming Events</h2>
          </div>
          <div className="space-y-3">
            {loading ? (
              <div className="text-sm text-muted-foreground py-4">Loading events...</div>
            ) : events.length === 0 ? (
              <div className="text-sm text-muted-foreground py-4">No events found.</div>
            ) : (
              events.slice(0, 5).map((ev) => (
              <div
                key={ev.id}
                className="flex items-start justify-between p-3 rounded-lg bg-white/3 border border-white/5 hover:border-white/10 transition-colors"
              >
                <div>
                  <div className="text-sm font-medium text-foreground">{ev.title}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {format(new Date(ev.start_time), "MMM d, yyyy · h:mm a")}
                  </div>
                </div>
                <div className="text-xs text-muted-foreground shrink-0 ml-3">
                  {Math.round((ev.preparation_time_minutes || 0) / 60)}h prep
                </div>
              </div>
            )))}
          </div>
        </section>

        {/* Recent Responsibilities */}
        <section className="glass rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Activity size={15} className="text-accent" />
            <h2 className="text-sm font-semibold text-foreground">Recent Responsibilities</h2>
          </div>
          <div className="space-y-3">
            {loading ? (
              <div className="text-sm text-muted-foreground py-4">Loading responsibilities...</div>
            ) : responsibilities.length === 0 ? (
              <div className="text-sm text-muted-foreground py-4">No responsibilities found.</div>
            ) : (
              responsibilities.slice(0, 5).map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between p-3 rounded-lg bg-white/3 border border-white/5 hover:border-white/10 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-foreground truncate">{r.title}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={r.status} />
                    <UrgencyChip level={r.urgency} />
                  </div>
                </div>
                <div className="text-xs text-muted-foreground ml-3 shrink-0">
                  E:{r.effort_score}/10
                </div>
              </div>
            )))}
          </div>
        </section>

        {/* Recent Notifications */}
        <section className="glass rounded-xl p-5 space-y-4 lg:col-span-2">
          <div className="flex items-center gap-2">
            <AlertTriangle size={15} className="text-yellow-400" />
            <h2 className="text-sm font-semibold text-foreground">Recent Notifications</h2>
            <span className="ml-auto text-xs text-muted-foreground">
              {loading ? "Loading..." : `${notifications.length} total`}
            </span>
          </div>
          {loading ? (
            <div className="text-sm text-muted-foreground text-center py-6">Fetching from backend…</div>
          ) : notifications.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-6">
              No notifications yet. Backend is running and WebSocket is connected.
            </div>
          ) : (
            <div className="space-y-2">
              {notifications.slice(0, 5).map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${n.is_read
                      ? "bg-white/2 border-white/5 opacity-60"
                      : "bg-primary/5 border-primary/15"
                    }`}
                >
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${n.is_read ? "bg-muted-foreground/40" : "bg-primary"}`} />
                  <div>
                    <div className="text-xs font-medium text-foreground">{n.type}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{n.message}</div>
                  </div>
                  <div className="ml-auto text-xs text-muted-foreground shrink-0">
                    {format(new Date(n.created_at), "MMM d")}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
