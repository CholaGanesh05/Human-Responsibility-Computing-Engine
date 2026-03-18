"use client";
/**
 * AuthGuard — Stage 11
 * Client-side component that redirects unauthenticated users to /login.
 * Pages at /login and /register are always rendered without the shell layout.
 */
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

const PUBLIC_PATHS = ["/login", "/register"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const router = useRouter();
    const [checked, setChecked] = useState(false);
    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

    useEffect(() => {
        if (isPublic) {
            // eslint-disable-next-line
            setChecked(true);
            return;
        }
        if (!isAuthenticated()) {
            router.replace("/login");
        } else {
            // eslint-disable-next-line
            setChecked(true);
        }
    }, [pathname, isPublic, router]);

    // On public pages, render without the shell (login/register have their own full-screen layout)
    if (isPublic) return <>{children}</>;

    // While checking auth, render nothing (avoids flash of dashboard)
    if (!checked) return null;

    return <>{children}</>;
}
