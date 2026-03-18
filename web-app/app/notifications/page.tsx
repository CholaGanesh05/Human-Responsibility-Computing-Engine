"use client";

import { useEffect, useState, useCallback } from "react";
import { getNotifications, markNotificationRead } from "@/lib/api";
import type { Notification } from "@/types/hrce";
import { Bell, CheckCheck, RefreshCw } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const TYPE_COLORS: Record<string, string> = {
    REMINDER: "text-blue-400",
    ESCALATION: "text-orange-400",
    MISSED: "text-red-400",
    PREPARATION_DUE: "text-yellow-400",
    DEPENDENCY_BLOCKED: "text-purple-400",
};

export default function NotificationsPage() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const [unreadOnly, setUnreadOnly] = useState(false);

    const load = useCallback(async (unread = unreadOnly) => {
        setLoading(true);
        try {
            const r = await getNotifications(unread);
            setNotifications(r.notifications);
        } catch {
            toast.error("Could not fetch notifications — is the backend running?");
        } finally {
            setLoading(false);
        }
    }, [unreadOnly]);

    useEffect(() => { load(); }, [load]);

    async function handleMarkRead(id: string) {
        try {
            await markNotificationRead(id);
            setNotifications((prev) =>
                prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
            );
        } catch {
            toast.error("Failed to mark as read.");
        }
    }

    const unreadCount = notifications.filter((n) => !n.is_read).length;

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="page-header">Notifications</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        {unreadCount} unread · {notifications.length} total
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => { setUnreadOnly(!unreadOnly); load(!unreadOnly); }}
                        className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                            unreadOnly
                                ? "bg-primary/15 border-primary/30 text-primary"
                                : "border-white/10 text-muted-foreground hover:bg-white/5"
                        )}
                    >
                        Unread only
                    </button>
                    <button
                        onClick={() => load()}
                        className="p-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors"
                    >
                        <RefreshCw size={13} className={cn("text-muted-foreground", loading && "animate-spin")} />
                    </button>
                </div>
            </div>

            <div className="glass rounded-xl overflow-hidden">
                {loading ? (
                    <div className="text-sm text-muted-foreground text-center py-12">Loading notifications…</div>
                ) : notifications.length === 0 ? (
                    <div className="text-center py-16 space-y-2">
                        <Bell size={28} className="text-muted-foreground/30 mx-auto" />
                        <div className="text-sm text-muted-foreground">No notifications found.</div>
                        <div className="text-xs text-muted-foreground/60">
                            Seed the database or trigger a scan to generate notifications.
                        </div>
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {notifications.map((n) => (
                            <div
                                key={n.id}
                                className={cn(
                                    "flex items-start gap-4 px-5 py-4 transition-colors",
                                    n.is_read ? "opacity-50 hover:opacity-70" : "hover:bg-white/2"
                                )}
                            >
                                <div className="mt-1">
                                    <div
                                        className={cn(
                                            "w-2 h-2 rounded-full",
                                            n.is_read ? "bg-muted-foreground/30" : "bg-primary pulse-dot"
                                        )}
                                    />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={cn("text-xs font-semibold", TYPE_COLORS[n.type] ?? "text-foreground")}>
                                            {n.type}
                                        </span>
                                        <span className="text-[10px] text-muted-foreground">
                                            {format(new Date(n.created_at), "MMM d, h:mm a")}
                                        </span>
                                    </div>
                                    <p className="text-sm text-foreground/80">{n.message}</p>
                                </div>
                                {!n.is_read && (
                                    <button
                                        onClick={() => handleMarkRead(n.id)}
                                        className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs bg-white/5 text-muted-foreground hover:text-foreground transition-colors shrink-0"
                                    >
                                        <CheckCheck size={11} />
                                        Mark read
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
