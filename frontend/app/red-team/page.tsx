"use client";

import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Target, TrendingUp, ShieldAlert, Activity, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { fetchWrapper } from '../../lib/apiClient';



export default function RedTeamDashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    const fetchBattle = async () => {
      const { data: resData, error: resError } = await fetchWrapper('api/adversarial-battle');
      if (resError || !resData) {
        setError(true);
      } else {
        setData(resData);
        setError(false);
        setChartData((prev) => {
          const newPoint = {
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            generation: resData.red_attacks_generated ?? 0,
            bypasses: Math.round((resData.red_attacks_generated ?? 0) * (resData.red_success_rate ?? 0))
          };
          const updated = [...prev, newPoint];
          return updated.slice(-20);
        });
      }
      setIsLoading(false);
    };

    fetchBattle();
    const interval = setInterval(fetchBattle, 2000);
    return () => clearInterval(interval);
  }, []);

  const generated = data?.red_attacks_generated ?? 0;
  const successRate = data?.red_success_rate ?? 0.0;
  
  // The backend returns a list of strings for active_attack_families, NOT a dictionary.
  const rawFamilies = data?.active_attack_families ?? [];
  
  const activeVectors = rawFamilies.map((name: string, idx: number) => ({
    name: name.replace(/_/g, ' '),
    load: 100 - (idx * 15), // Mock visually descending load since the API only gives names
    success_rate: successRate
  }));

  return (
    <div className="w-full space-y-6">
      
      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
        
        {/* Load Rate Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Simulated Load</h2>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {error ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : isLoading ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight animate-pulse">Loading...</span>
            ) : (
              <span className="text-3xl font-bold text-slate-900 tracking-tight">{generated}</span>
            )}
            <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-100 flex items-center gap-1">
              <ArrowUpRight className="w-3 h-3" /> Live
            </span>
          </div>
        </div>

        {/* Bypass Rate Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">System Bypass Rate</h2>
            <ShieldAlert className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {error ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : isLoading ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight animate-pulse">Loading...</span>
            ) : (
              <span className="text-3xl font-bold text-slate-900 tracking-tight">{(successRate * 100).toFixed(1)}%</span>
            )}
            <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2 py-1 rounded-md border border-rose-100 flex items-center gap-1">
              <ArrowDownRight className="w-3 h-3" /> Tracked
            </span>
          </div>
        </div>

      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 gap-6">
        
        {/* Active Vectors Breakdown */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col h-[28rem]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Vectors</h2>
            <Target className="w-4 h-4 text-slate-400" />
          </div>
          
          <div className="flex flex-col gap-6 flex-1 overflow-y-auto pr-2">
            {activeVectors.map((vector, idx) => (
              <div key={idx} className="space-y-3">
                <div className="flex justify-between items-end">
                  <span className="text-slate-900 font-semibold text-sm">{vector.name}</span>
                  <span className="text-sm text-slate-400">Load: {vector.load}</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-600 rounded-full transition-all duration-1000" 
                    style={{ width: `${Math.min(100, vector.load)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Timeline Chart */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col h-[28rem]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Simulation Timeline Volume</h2>
            <TrendingUp className="w-4 h-4 text-slate-400" />
          </div>
          
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorGen" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorBypass" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E11D48" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#E11D48" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                <XAxis dataKey="time" stroke="#94A3B8" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} dy={15} />
                <YAxis stroke="#94A3B8" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} dx={-15} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E2E8F0', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '13px', fontWeight: 500 }} />
                <Area 
                  type="monotone" 
                  dataKey="generation" 
                  name="Test Load (req/s)"
                  stroke="#2563EB" 
                  fillOpacity={1} 
                  fill="url(#colorGen)" 
                  strokeWidth={2}
                />
                <Area 
                  type="monotone" 
                  dataKey="bypasses" 
                  name="Successful Penetrations"
                  stroke="#E11D48" 
                  fillOpacity={1} 
                  fill="url(#colorBypass)" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        
      </div>
    </div>
  );
}
