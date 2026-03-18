"use client";
import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register, setToken } from "@/lib/auth";

export default function RegisterPage() {
    const router = useRouter();
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const token = await register(email, password, fullName || undefined);
            setToken(token.access_token);
            router.push("/");
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Registration failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center" style={{ background: "hsl(220 40% 5%)" }}>
            <div className="w-full max-w-md">
                {/* Logo / Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
                        style={{ background: "linear-gradient(135deg, hsl(217 91% 60%), hsl(270 80% 65%))" }}>
                        <span className="text-2xl">⚡</span>
                    </div>
                    <h1 className="text-2xl font-bold" style={{ color: "hsl(210 40% 95%)" }}>HRCE</h1>
                    <p className="text-sm mt-1" style={{ color: "hsl(215 20% 55%)" }}>
                        Human Responsibility Computing Engine
                    </p>
                </div>

                {/* Card */}
                <div className="rounded-2xl p-8" style={{
                    background: "hsl(220 40% 9%)",
                    border: "1px solid hsl(217 33% 18%)",
                    boxShadow: "0 0 40px -10px hsl(217 91% 60% / 0.15)",
                }}>
                    <h2 className="text-xl font-semibold mb-6" style={{ color: "hsl(210 40% 95%)" }}>
                        Create your account
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1.5" style={{ color: "hsl(215 20% 65%)" }}>
                                Full name <span style={{ color: "hsl(215 20% 40%)" }}>(optional)</span>
                            </label>
                            <input
                                id="register-fullname"
                                type="text"
                                autoComplete="name"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="Jane Smith"
                                className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
                                style={{
                                    background: "hsl(220 40% 13%)",
                                    border: "1px solid hsl(217 33% 22%)",
                                    color: "hsl(210 40% 95%)",
                                }}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1.5" style={{ color: "hsl(215 20% 65%)" }}>
                                Email address
                            </label>
                            <input
                                id="register-email"
                                type="email"
                                required
                                autoComplete="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
                                style={{
                                    background: "hsl(220 40% 13%)",
                                    border: "1px solid hsl(217 33% 22%)",
                                    color: "hsl(210 40% 95%)",
                                }}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1.5" style={{ color: "hsl(215 20% 65%)" }}>
                                Password
                            </label>
                            <input
                                id="register-password"
                                type="password"
                                required
                                autoComplete="new-password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Min. 8 characters"
                                minLength={8}
                                className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
                                style={{
                                    background: "hsl(220 40% 13%)",
                                    border: "1px solid hsl(217 33% 22%)",
                                    color: "hsl(210 40% 95%)",
                                }}
                            />
                        </div>

                        {error && (
                            <div className="rounded-xl px-4 py-3 text-sm" style={{
                                background: "hsl(0 60% 15%)",
                                border: "1px solid hsl(0 60% 30%)",
                                color: "hsl(0 80% 70%)",
                            }}>
                                {error}
                            </div>
                        )}

                        <button
                            id="register-submit"
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 rounded-xl font-semibold text-sm transition-all mt-2"
                            style={{
                                background: "linear-gradient(135deg, hsl(217 91% 55%), hsl(270 80% 60%))",
                                color: "white",
                                opacity: loading ? 0.7 : 1,
                                cursor: loading ? "not-allowed" : "pointer",
                            }}
                        >
                            {loading ? "Creating account…" : "Create account"}
                        </button>
                    </form>

                    <p className="text-sm text-center mt-6" style={{ color: "hsl(215 20% 55%)" }}>
                        Already have an account?{" "}
                        <Link href="/login" style={{ color: "hsl(217 91% 65%)" }} className="font-medium hover:underline">
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
