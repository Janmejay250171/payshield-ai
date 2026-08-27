"use client";

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';
import { Target, Lock, CheckCircle2, ShieldCheck, Activity, ArrowUpRight } from 'lucide-react';

const mockMetrics = {
  detection_rate: 0.985,
  avg_confidence: 0.92,
  active_rules: [
    { id: 'R-101', name: 'Velocity Threshold Breach', status: 'Active', severity: 'High' },
    { id: 'R-102', name: 'Known Bad IP Subnet', status: 'Active', severity: 'Critical' },
    { id: 'R-103', name: 'Impossible Travel', status: 'Active', severity: 'Medium' },
    { id: 'R-104', name: 'Device Fingerprint Mismatch', status: 'Active', severity: 'High' },
  ]
};

const shapData = [
  { feature: 'Device Age', importance: 0.35 },
  { feature: 'IP Velocity', importance: 0.28 },
  { feature: 'Card Country Match', importance: 0.15 },
  { feature: 'Txn Amount Diff', importance: 0.12 },
  { feature: 'Time of Day', importance: 0.10 },
].reverse(); // Reverse for horizontal bar chart

export default function BlueTeamDashboard() {
  return (
    <div className="w-full space-y-6">
      
      {/* Top KPI Cards (Minimalist Fintech Style) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Detection Rate Card */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex items-center justify-between h-48 border border-slate-200">
          <div className="flex flex-col justify-between h-full">
             <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Detection Rate</span>
              <Target className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <span className="text-5xl font-extrabold text-slate-900">{(mockMetrics.detection_rate * 100).toFixed(1)}%</span>
            </div>
          </div>
          <div className="h-32 w-32">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="100%" barSize={10} data={[{ name: 'Detection', value: 98.5, fill: '#2563EB' }]}>
                <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                <RadialBar background={{ fill: '#F1F5F9' }} clockWise dataKey="value" cornerRadius={10} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Confidence Card */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
           <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Model Confidence</span>
            <Lock className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-slate-900">{(mockMetrics.avg_confidence * 100).toFixed(1)}%</span>
            <span className="text-xs font-medium text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-md flex items-center gap-1 border border-indigo-100">
              <ArrowUpRight className="w-3 h-3" /> +2.1%
            </span>
          </div>
        </div>

      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* SHAP Feature Importance */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 flex flex-col h-[28rem]">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">SHAP Feature Importance (XGBoost)</h2>
            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
               <Activity className="w-4 h-4 text-slate-400" />
            </div>
          </div>
          
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={shapData} layout="vertical" margin={{ top: 0, right: 0, left: 30, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" horizontal={false} />
                <XAxis type="number" stroke="#94A3B8" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="feature" stroke="#64748B" tick={{ fill: '#64748B', fontSize: 13, fontWeight: 500 }} axisLine={false} tickLine={false} dx={-10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#E2E8F0', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
                  cursor={{ fill: '#F8FAFC' }} 
                />
                <Bar dataKey="importance" fill="#2563EB" radius={[0, 6, 6, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Active Rules List */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 flex flex-col h-[28rem]">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Heuristic Rules</h2>
            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
               <ShieldCheck className="w-4 h-4 text-slate-400" />
            </div>
          </div>
          
          <div className="flex flex-col gap-4 flex-1">
            {mockMetrics.active_rules.map((rule, idx) => (
              <div key={idx} className="flex items-center justify-between p-5 bg-slate-50 rounded-xl border border-slate-100">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm border border-slate-200 flex-shrink-0">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <div className="text-slate-900 font-semibold text-sm">{rule.name}</div>
                    <div className="text-slate-400 text-sm mt-0.5">{rule.id}</div>
                  </div>
                </div>
                <div className={`text-xs font-semibold px-3 py-1.5 rounded-md border ${
                  rule.severity === 'Critical' ? 'bg-rose-50 text-rose-700 border-rose-100' :
                  rule.severity === 'High' ? 'bg-orange-50 text-orange-700 border-orange-100' :
                  'bg-yellow-50 text-yellow-700 border-yellow-100'
                }`}>
                  {rule.severity}
                </div>
              </div>
            ))}
          </div>
        </div>
        
      </div>
    </div>
  );
}
