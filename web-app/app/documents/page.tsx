"use client";

import { useState, useRef } from "react";
import { uploadDocument, searchDocuments } from "@/lib/api";
import type { HRCEDocument } from "@/types/hrce";
import { Upload, Search, FileText, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export default function DocumentsPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<HRCEDocument[]>([]);
    const [searching, setSearching] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [dragging, setDragging] = useState(false);
    const [uploadedFile, setUploadedFile] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    async function handleUpload(file: File) {
        setUploading(true);
        try {
            const r = await uploadDocument(file);
            setUploadedFile(r.title);
            toast.success(`Uploaded: ${r.title}`);
        } catch {
            toast.error("Upload failed — ensure the backend is running.");
        } finally {
            setUploading(false);
        }
    }

    async function handleSearch(e: React.FormEvent) {
        e.preventDefault();
        if (query.length < 3) { toast.warning("Query must be at least 3 characters."); return; }
        setSearching(true);
        try {
            const r = await searchDocuments(query);
            setResults(r);
            if (r.length === 0) toast.info("No matching documents found.");
        } catch {
            toast.error("Search failed — ensure the backend is running.");
        } finally {
            setSearching(false);
        }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="page-header">Documents</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Upload context documents and search with semantic AI retrieval
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Upload Zone */}
                <section className="space-y-4">
                    <h2 className="text-sm font-semibold text-foreground">Upload Document</h2>
                    <div
                        className={cn(
                            "glass rounded-xl p-10 flex flex-col items-center justify-center border-2 border-dashed cursor-pointer transition-all duration-200",
                            dragging ? "border-primary/60 bg-primary/5" : "border-white/10 hover:border-white/20"
                        )}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={(e) => {
                            e.preventDefault();
                            setDragging(false);
                            const f = e.dataTransfer.files[0];
                            if (f) handleUpload(f);
                        }}
                        onClick={() => inputRef.current?.click()}
                    >
                        <input
                            ref={inputRef}
                            type="file"
                            className="hidden"
                            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
                        />
                        {uploading ? (
                            <>
                                <Loader2 size={28} className="text-primary animate-spin mb-3" />
                                <p className="text-sm text-muted-foreground">Uploading…</p>
                            </>
                        ) : (
                            <>
                                <Upload size={28} className="text-muted-foreground/40 mb-3" />
                                <p className="text-sm font-medium text-foreground">Drop a file here</p>
                                <p className="text-xs text-muted-foreground mt-1">or click to browse · PDF, DOCX, TXT</p>
                            </>
                        )}
                    </div>
                    {uploadedFile && (
                        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm">
                            <FileText size={13} className="text-emerald-400 shrink-0" />
                            <span className="text-emerald-400 truncate">{uploadedFile}</span>
                            <button onClick={() => setUploadedFile(null)} className="ml-auto">
                                <X size={12} className="text-emerald-400/60" />
                            </button>
                        </div>
                    )}
                </section>

                {/* Search */}
                <section className="space-y-4">
                    <h2 className="text-sm font-semibold text-foreground">Semantic Search</h2>
                    <form onSubmit={handleSearch} className="flex gap-2">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search by meaning, not just keywords…"
                            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-primary/50"
                        />
                        <button
                            type="submit"
                            disabled={searching}
                            className="px-4 py-2 rounded-lg text-sm font-semibold text-black transition-all hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
                            style={{ background: "hsl(var(--primary))" }}
                        >
                            {searching ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />}
                            Search
                        </button>
                    </form>

                    <div className="space-y-2 min-h-40">
                        {results.length === 0 && !searching && (
                            <div className="text-center py-10 text-sm text-muted-foreground/60">
                                Search results will appear here
                            </div>
                        )}
                        {results.map((doc) => (
                            <div
                                key={doc.id}
                                className="glass rounded-lg px-4 py-3 flex items-center gap-3 hover:border-white/15 transition-colors"
                            >
                                <FileText size={14} className="text-primary shrink-0" />
                                <div className="min-w-0">
                                    <div className="text-sm font-medium text-foreground truncate">{doc.title}</div>
                                    <div className="text-xs text-muted-foreground">id: {doc.id}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
}
