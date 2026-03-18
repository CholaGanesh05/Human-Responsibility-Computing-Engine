"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    addEdge,
    useNodesState,
    useEdgesState,
    type Connection,
    type Node,
    type Edge,
    BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";

import { getAllResponsibilities } from "@/lib/api";
import type { Responsibility } from "@/types/hrce";

// Status → node color
const STATUS_COLOR: Record<string, string> = {
    PENDING: "#eab308",
    ACTIVE: "#38bdf8",
    COMPLETED: "#22c55e",
    BLOCKED: "#ef4444",
};

function buildGraph(responsibilities: Responsibility[]): {
    nodes: Node[];
    edges: Edge[];
} {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    if (!responsibilities) return { nodes, edges };

    function process(r: Responsibility, x: number, y: number) {
        const color = STATUS_COLOR[r.status] ?? "#64748b";
        nodes.push({
            id: r.id,
            position: { x, y },
            data: {
                label: (
                    <div style={{ fontSize: 11, lineHeight: 1.4 }}>
                        <div style={{ fontWeight: 600, color: "#f1f5f9", marginBottom: 2 }}>
                            {r.title.length > 28 ? r.title.slice(0, 28) + "…" : r.title}
                        </div>
                        <div style={{ color: color, fontSize: 9, fontWeight: 700 }}>{r.status}</div>
                        <div style={{ color: "#64748b", fontSize: 9 }}>E:{r.effort_score}/10 · {r.urgency}</div>
                    </div>
                ),
            },
            style: {
                background: "hsl(220 40% 9%)",
                border: `1.5px solid ${color}55`,
                borderRadius: 10,
                padding: "8px 12px",
                minWidth: 160,
                boxShadow: `0 0 12px ${color}22`,
                color: "#f1f5f9",
            },
        });

        if (r.sub_responsibilities) {
            r.sub_responsibilities.forEach((sub, idx) => {
                edges.push({
                    id: `${r.id}->${sub.id}`,
                    source: r.id,
                    target: sub.id,
                    style: { stroke: "#334155", strokeWidth: 1.5 },
                    animated: sub.status === "ACTIVE",
                });
                process(sub, x + (idx - (r.sub_responsibilities!.length - 1) / 2) * 220, y + 160);
            });
        }
    }

    let xOffset = 0;
    responsibilities.forEach((r, i) => {
        process(r, xOffset, i * 160);
        xOffset += 260;
    });

    return { nodes, edges };
}

export default function GraphPage() {
    const [pageLoading, setPageLoading] = useState(true);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        async function load() {
            setPageLoading(true);
            try {
                const data = await getAllResponsibilities();
                const { nodes: newNodes, edges: newEdges } = buildGraph(data);
                setNodes(newNodes);
                setEdges(newEdges);
            } catch {
                console.error("Failed to load graph data");
            } finally {
                setPageLoading(false);
            }
        }
        load();
    }, [setNodes, setEdges]);

    const onConnect = useCallback(
        (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
        [setEdges]
    );

    return (
        <div className="space-y-4 animate-fade-in">
            <div>
                <h1 className="page-header">Graph View</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Interactive responsibility dependency graph — animated edges = active tasks
                </p>
            </div>

            <div
                className="glass rounded-xl overflow-hidden relative"
                style={{ height: "calc(100vh - 200px)", minHeight: 500 }}
            >
                {pageLoading ? (
                    <div className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground z-10">
                        Loading graph…
                    </div>
                ) : nodes.length === 0 ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-sm text-muted-foreground z-10">
                        No responsibilities found.
                    </div>
                ) : (
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    fitView
                    attributionPosition="bottom-left"
                >
                    <Background
                        variant={BackgroundVariant.Dots}
                        gap={20}
                        size={1}
                        color="#1e293b"
                    />
                    <Controls
                        style={{
                            background: "hsl(220 40% 9%)",
                            border: "1px solid hsl(217 33% 18%)",
                            borderRadius: 8,
                        }}
                    />
                    <MiniMap
                        style={{
                            background: "hsl(222 47% 5%)",
                            border: "1px solid hsl(217 33% 18%)",
                        }}
                        nodeColor={(n) => (n.style?.borderTop as string) ?? "#334155"}
                        maskColor="rgba(0,0,0,0.6)"
                    />
                </ReactFlow>
                )}
            </div>
        </div>
    );
}
