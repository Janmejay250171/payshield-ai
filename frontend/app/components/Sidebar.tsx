"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  Skull,
  Swords,
  Search,
  Home,
} from "lucide-react";

const navItems = [
  {
    href: "/",
    label: "Command Center",
    icon: Home,
  },
  {
    href: "/investigation",
    label: "Investigation",
    icon: Search,
  },
  {
    href: "/blue-team",
    label: "Defense Metrics",
    icon: Shield,
  },
  {
    href: "/red-team",
    label: "Threat Simulation",
    icon: Skull,
  },
  {
    href: "/battle",
    label: "Adversarial View",
    icon: Swords,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white rounded-2xl flex-shrink-0 hidden md:flex flex-col shadow-sm border border-slate-200 py-6 px-4">
      
      {/* Logo */}
      <div className="flex items-center px-4 mb-8">
        <Shield
          className="w-7 h-7 text-blue-600 mr-3"
          strokeWidth={2.5}
        />
        <span className="font-bold tracking-tight text-slate-900 text-xl">
          PAYSHIELD
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;

          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? "bg-slate-100 text-slate-900 font-semibold shadow-sm border border-slate-200/50"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <Icon
                className={`w-4 h-4 ${
                  isActive ? "text-blue-600" : ""
                }`}
              />

              <span className="text-sm">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}