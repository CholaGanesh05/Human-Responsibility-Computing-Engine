import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AuthGuard from "@/components/layout/AuthGuard";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "HRCE — Responsibility Engine",
  description: "Human Responsibility Computing Engine — AI-powered obligation management platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthGuard>
          <Sidebar />
          <Topbar />
          <main
            className="min-h-screen pt-14 animate-fade-in"
            style={{ marginLeft: 240 }}
          >
            <div className="p-6 md:p-8">{children}</div>
          </main>
        </AuthGuard>
        <Toaster
          theme="dark"
          position="top-right"
          toastOptions={{
            style: {
              background: "hsl(220 40% 9%)",
              border: "1px solid hsl(217 33% 18%)",
              color: "hsl(210 40% 95%)",
            },
          }}
        />
      </body>
    </html>
  );
}
