"use client";

import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Activity, ShieldAlert, ShieldCheck } from 'lucide-react';
import { fetchWrapper } from '../../lib/apiClient';

export default function BattleDashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [combatData, setCombatData] = useState<any[]>([]);

  useEffect(() => {
    const fetchBattle = async () => {
      const { data: resData, error: resError } = await fetchWrapper('api/adversarial-battle');
      if (resError || !resData) {
        setError(true);
      } else {
        setData(resData);
        setError(false);
        setCombatData((prev) => {
          const newPoint = {
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            load: resData.red_attacks_generated ?? 0,
            mitigated: Math.round((resData.red_attacks_generated ?? 0) * (resData.blue_catch_rate ?? 0))
          };
          return [...prev, newPoint].slice(-20);
        });
      }
      setIsLoading(false);
    };

    fetchBattle();
    const interval = setInterval(fetchBattle, 2000);
    return () => clearInterval(interval);
  }, []);

  const generated = data?.red_attacks_generated ?? 0;
  const caught = data ? Math.round(generated * data.blue_catch_rate) : 0;

  return (
    <div className="w-full space-y-6">
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* Threat Load Side */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Simulated Threat Load</h2>
            <ShieldAlert className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {error ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : isLoading ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight animate-pulse">Loading...</span>
            ) : (
              <span className="text-3xl font-bold text-slate-900 tracking-tight">{generated} <span className="text-xl font-medium text-slate-400">total</span></span>
            )}
            <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2 py-1 rounded-md border border-rose-100">
              Red Team
            </span>
          </div>
        </div>
        
        {/* Mitigation Side */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Mitigation Capacity</h2>
            <ShieldCheck className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {error ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : isLoading ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight animate-pulse">Loading...</span>
            ) : (
              <span className="text-3xl font-bold text-slate-900 tracking-tight">{caught} <span className="text-xl font-medium text-slate-400">total</span></span>
            )}
            <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-100">
              Blue Team
            </span>
          </div>
        </div>
      </div>

      {/* Tug of War Chart */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col h-[28rem]">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Live Combat Timeline</h2>
          <Activity className="w-4 h-4 text-slate-400" />
        </div>
        <div className="flex-1 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={combatData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
