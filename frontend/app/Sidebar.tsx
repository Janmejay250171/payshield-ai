"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Home, Search, Skull, Swords } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Command Center', icon: Home },
    { href: '/red-team', label: 'Red Team Dashboard', icon: Skull },
    { href: '/blue-team', label: 'Blue Team Dashboard', icon: Shield },
    { href: '/battle', label: 'Adversarial Battle', icon: Swords },
    { href: '/investigation', label: 'Transaction Investigation', icon: Search },
  ];

  return (
    <aside className="w-64 bg-white rounded-2xl flex-shrink-0 hidden md:flex flex-col shadow-sm border border-slate-200 py-6 px-4">
      <div className="flex items-center px-4 mb-8">
        <Shield className="w-7 h-7 text-blue-600 mr-3" strokeWidth={2.5} />
        <span className="font-bold tracking-tight text-slate-900 text-xl">PAYSHIELD</span>
      </div>
      
      <nav className="flex-1 space-y-1.5">
        {links.map((link) => {
          const isActive = pathname === link.href;
          const Icon = link.icon;
          
          if (isActive) {
            return (
              <Link 
                key={link.href}
                href={link.href} 
                className="flex items-center gap-4 px-4 py-3 rounded-xl bg-green-50 text-green-800 transition-all font-semibold shadow-sm border border-green-100/50"
              >
                <Icon className="w-4 h-4 text-green-600" />
                <span className="text-sm">{link.label}</span>
              </Link>
            );
          }
          
          return (
            <Link 
              key={link.href}
              href={link.href} 
              className="flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-slate-50 text-slate-500 hover:text-slate-900 transition-all"
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium text-sm">{link.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
