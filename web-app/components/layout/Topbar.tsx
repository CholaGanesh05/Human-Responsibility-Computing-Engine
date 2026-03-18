"use client";

import { Wifi, WifiOff, Bell } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { getToken } from "@/lib/auth";

export default function Topbar({ title }: { title?: string }) {
    const [userId, setUserId] = useState<string>("");

    useEffect(() => {
        const token = getToken();
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split(".")[1]));
                if (payload.sub) setUserId(payload.sub);
            } catch {
                // Ignore parse errors safely
            }
        }
    }, []);

    const { messages, connected } = useWebSocket(userId);
    const [showDot, setShowDot] = useState(false);

    // Flash notification dot whenever a new WS message arrives
    useEffect(() => {
        if (messages.length > 0) setShowDot(true);
    }, [messages]);

    const notifCount = messages.filter((m) => m.event === "notification").length;

    return (
        <header
            className="fixed top-0 right-0 z-20 flex items-center justify-between px-6 h-14 glass"
            style={{
                left: 240,
                borderBottom: "1px solid var(--glass-border)",
            }}
        >
            <h1 className="text-sm font-semibold text-foreground tracking-tight">
                {title ?? "HRCE Platform"}
            </h1>

            <div className="flex items-center gap-4">
                {/* Connection status */}
                <div className="flex items-center gap-1.5 text-xs">
                    {connected ? (
                        <>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-dot" />
                            <Wifi size={12} className="text-emerald-400" />
                            <span className="text-muted-foreground hidden sm:inline">Live</span>
                        </>
                    ) : (
                        <>
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                            <WifiOff size={12} className="text-red-400" />
                            <span className="text-muted-foreground hidden sm:inline">Offline</span>
                        </>
                    )}
                </div>

                {/* Notification bell */}
                <button
                    className="relative p-2 rounded-lg hover:bg-white/5 transition-colors"
                    onClick={() => setShowDot(false)}
                    aria-label="Notifications"
                >
                    <Bell size={16} className={cn("text-muted-foreground", showDot && "text-primary")} />
                    {notifCount > 0 && (
                        <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-primary text-black text-[9px] font-bold flex items-center justify-center">
                            {notifCount > 9 ? "9+" : notifCount}
                        </span>
                    )}
                </button>
            </div>
        </header>
    );
}
