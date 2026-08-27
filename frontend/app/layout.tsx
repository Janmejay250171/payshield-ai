import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { ShieldAlert, Skull, Shield, Swords, Search, Home } from "lucide-react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PAYSHIELD AI",
  description: "Enterprise Fraud Prevention",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-screen bg-[#f4f4f5] text-slate-900 font-sans p-4 gap-6">
        {/* Global Sidebar - Minimalist Fintech Style */}
        <aside className="w-64 bg-white rounded-2xl flex-shrink-0 hidden md:flex flex-col shadow-sm border border-slate-200 py-6 px-4">
          <div className="flex items-center px-4 mb-8">
            <Shield className="w-7 h-7 text-blue-600 mr-3" strokeWidth={2.5} />
            <span className="font-bold tracking-tight text-slate-900 text-xl">PAYSHIELD</span>
          </div>
          
          <nav className="flex-1 space-y-1.5">
            <Link 
              href="/" 
              className="flex items-center gap-4 px-4 py-3 rounded-xl bg-slate-100 text-slate-900 transition-all font-semibold shadow-sm border border-slate-200/50"
            >
              <Home className="w-4 h-4 text-blue-600" />
              <span className="text-sm">Command Center</span>
            </Link>

            <Link 
              href="/investigation" 
              className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-slate-900 transition-all"
            >
              <Search className="w-4 h-4" />
              <span className="font-medium text-sm">Investigation</span>
            </Link>

            <Link 
              href="/blue-team" 
              className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-slate-900 transition-all"
            >
              <Shield className="w-4 h-4" />
              <span className="font-medium text-sm">Defense Metrics</span>
            </Link>

            <Link 
              href="/red-team" 
              className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-slate-900 transition-all"
            >
              <Skull className="w-4 h-4" />
              <span className="font-medium text-sm">Threat Simulation</span>
            </Link>

            <Link 
              href="/battle" 
              className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-slate-900 transition-all"
            >
              <Swords className="w-4 h-4" />
              <span className="font-medium text-sm">Adversarial View</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-h-screen overflow-y-auto pb-4">
          {children}
        </div>
      </body>
    </html>
  );
}
