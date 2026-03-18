"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Calendar,
    List,
    CheckSquare2,
    GitFork,
    Bell,
    FileSearch,
    ShieldAlert,
    ClipboardCheck,
    Bot,
    Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/calendar", label: "Calendar", icon: Calendar },
    { href: "/events", label: "Events", icon: List },
    { href: "/responsibilities", label: "Responsibilities", icon: CheckSquare2 },
    { href: "/graph", label: "Graph View", icon: GitFork },
    { href: "/notifications", label: "Notifications", icon: Bell },
    { href: "/documents", label: "Documents", icon: FileSearch },
    { href: "/risk", label: "Risk", icon: ShieldAlert },
    { href: "/review", label: "Review", icon: ClipboardCheck },
    { href: "/agents", label: "AI Agents", icon: Bot },
];

export default function Sidebar() {
    const path = usePathname();

    return (
        <aside
            className="fixed left-0 top-0 h-screen z-30 flex flex-col"
            style={{
                width: 240,
                background: "hsl(var(--sidebar-bg))",
                borderRight: "1px solid hsl(var(--sidebar-border))",
            }}
        >
            {/* Logo */}
            <div className="flex items-center gap-2.5 px-4 py-5 border-b"
                style={{ borderColor: "hsl(var(--sidebar-border))" }}>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center glow-primary"
                    style={{ background: "hsl(var(--primary))" }}>
                    <Zap size={16} className="text-black" />
                </div>
                <div>
                    <div className="text-sm font-bold text-foreground tracking-tight">HRCE</div>
                    <div className="text-[10px] text-muted-foreground leading-tight">Responsibility Engine</div>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
                {NAV.map(({ href, label, icon: Icon }) => {
                    const active = href === "/" ? path === "/" : path.startsWith(href);
                    return (
                        <Link
                            key={href}
                            href={href}
                            className={cn("sidebar-item", active && "sidebar-item-active")}
                        >
                            <Icon size={16} />
                            <span>{label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="px-4 py-4 border-t text-[11px] text-muted-foreground"
                style={{ borderColor: "hsl(var(--sidebar-border))" }}>
                Stage 12 · Complete
            </div>
        </aside>
    );
}
