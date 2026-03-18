"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { WSPayload } from "@/types/hrce";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
const PING_INTERVAL_MS = 30_000;
const MAX_RETRIES = 10;

export function useWebSocket(userId: string) {
    const [messages, setMessages] = useState<WSPayload[]>([]);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const retryRef = useRef(0);
    const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const connect = useCallback(function doConnect() {
        if (!userId) return;
        const ws = new WebSocket(`${WS_BASE}/ws/${userId}`);
        wsRef.current = ws;

        ws.onopen = () => {
            setConnected(true);
            retryRef.current = 0;
            // Keep-alive ping
            pingRef.current = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) ws.send("ping");
            }, PING_INTERVAL_MS);
        };

        ws.onmessage = (ev) => {
            if (ev.data === "pong") return;
            try {
                const payload = JSON.parse(ev.data) as WSPayload;
                setMessages((prev) => [payload, ...prev.slice(0, 99)]);
            } catch {
                // ignore malformed frames
            }
        };

        ws.onclose = () => {
            setConnected(false);
            if (pingRef.current) clearInterval(pingRef.current);
            if (retryRef.current < MAX_RETRIES) {
                const delay = Math.min(1000 * 2 ** retryRef.current, 30_000);
                retryRef.current += 1;
                setTimeout(() => doConnect(), delay);
            }
        };

        ws.onerror = () => ws.close();
    }, [userId]);

    useEffect(() => {
        connect();
        return () => {
            if (pingRef.current) clearInterval(pingRef.current);
            wsRef.current?.close();
        };
    }, [connect]);

    const clearMessages = useCallback(() => setMessages([]), []);

    return { messages, connected, clearMessages };
}
