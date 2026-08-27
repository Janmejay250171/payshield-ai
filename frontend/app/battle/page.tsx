"use client";

import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Activity, ShieldAlert, ShieldCheck } from 'lucide-react';

const battleTimeline = [
  { time: '00:00', load: 100, mitigated: 98 },
  { time: '00:01', load: 150, mitigated: 145 },
  { time: '00:02', load: 300, mitigated: 210 }, 
  { time: '00:03', load: 280, mitigated: 275 }, 
  { time: '00:04', load: 400, mitigated: 390 },
  { time: '00:05', load: 550, mitigated: 420 }, 
  { time: '00:06', load: 450, mitigated: 445 }, 
];

export default function BattleDashboard() {
  return (
    <div className="w-full space-y-6">
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Threat Load Side */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Simulated Threat Load</span>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-rose-600">450 <span className="text-xl font-medium text-slate-400">req/s</span></span>
            <span className="text-sm text-slate-400">
              Red Team
            </span>
          </div>
        </div>
        
        {/* Mitigation Side */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Mitigation Capacity</span>
            <ShieldCheck className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-blue-600">445 <span className="text-xl font-medium text-slate-400">req/s</span></span>
            <span className="text-sm text-slate-400">
              Blue Team
            </span>
          </div>
        </div>
      </div>

      {/* Tug of War Chart */}
      <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 flex flex-col h-[500px]">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Live Combat Timeline</h2>
          <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
             <Activity className="w-4 h-4 text-slate-400" />
          </div>
        </div>
        <div className="flex-1 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={battleTimeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#E11D48" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#E11D48" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorMitigated" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563EB" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
              <XAxis dataKey="time" stroke="#94A3B8" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} dy={15} />
              <YAxis stroke="#94A3B8" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} dx={-15} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E2E8F0', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
              />
              <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '13px', fontWeight: 500 }} />
              <Area type="monotone" dataKey="load" name="Threat Load (Red)" stroke="#E11D48" fill="url(#colorLoad)" strokeWidth={3} />
              <Area type="monotone" dataKey="mitigated" name="Mitigated Requests (Blue)" stroke="#2563EB" fill="url(#colorMitigated)" strokeWidth={3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
