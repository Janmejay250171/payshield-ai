"use client";

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Activity, Smartphone, Zap, ArrowUpRight, ShieldAlert } from 'lucide-react';

const mockData = {
  risk_score: 0.94,
  decision: 'BLOCK',
  reasons: ['new_device', 'high_velocity']
};

const historicalData = [
  { time: '10:00', score: 0.12 },
  { time: '10:05', score: 0.15 },
  { time: '10:10', score: 0.22 },
  { time: '10:15', score: 0.18 },
  { time: '10:20', score: 0.85 },
  { time: '10:25', score: 0.94 },
];

export default function CommandCenter() {
  const isBlock = mockData.decision === 'BLOCK';

  return (
    <div className="w-full space-y-6">
      
      {/* Top KPI Cards (Minimalist Fintech Style) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Risk Score Card */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Risk Score</span>
            <Activity className="w-4 h-4 text-rose-500" />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-rose-600">{(mockData.risk_score * 100).toFixed(0)}</span>
            <span className="text-xs font-medium text-rose-600 bg-rose-50 px-2.5 py-1 rounded-md flex items-center gap-1 border border-rose-100">
              <TrendingUp className="w-3 h-3" /> +12%
            </span>
          </div>
        </div>

        {/* Decision Card */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
           <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Automated Decision</span>
            <ShieldAlert className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-slate-900">{mockData.decision}</span>
            <span className="text-sm text-slate-400">
              Terminated
            </span>
          </div>
        </div>

        {/* Status Card */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">System Status</span>
            <Zap className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-emerald-600">Active</span>
            <span className="text-sm text-slate-400">
              Optimal
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Reasons Card */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 col-span-1 flex flex-col h-[28rem]">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-8">Flagged Indicators</h2>
          <div className="flex flex-col gap-5 flex-1">
            {mockData.reasons.map((reason, idx) => (
              <div key={idx} className="flex items-center gap-4 p-5 bg-slate-50 rounded-xl border border-slate-100">
                <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm border border-slate-200 flex-shrink-0">
                  {reason === 'new_device' && <Smartphone className="w-5 h-5 text-blue-600" />}
                  {reason === 'high_velocity' && <Zap className="w-5 h-5 text-orange-500" />}
                </div>
                <div>
                  <div className="text-slate-900 font-semibold text-sm capitalize">{reason.replace('_', ' ')}</div>
                  <div className="text-slate-400 text-sm mt-0.5">Primary vector detected</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chart Section */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 col-span-1 lg:col-span-2 h-[28rem] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Risk Velocity Analysis</h2>
            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
               <Activity className="w-4 h-4 text-slate-400" />
            </div>
          </div>
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalData} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="#94A3B8" 
                  tick={{ fill: '#64748B', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  dy={15}
                />
                <YAxis 
                  stroke="#94A3B8" 
                  tick={{ fill: '#64748B', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 1]}
                  dx={-15}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E2E8F0', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  itemStyle={{ color: '#3B82F6', fontWeight: '600' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#2563EB" 
                  strokeWidth={3}
                  dot={{ fill: '#ffffff', stroke: '#2563EB', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#2563EB', stroke: '#EFF6FF', strokeWidth: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
