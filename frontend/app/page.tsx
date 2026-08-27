"use client";

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AlertTriangle, ShieldAlert, Activity, Smartphone, Zap } from 'lucide-react';

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
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-sans">
      <header className="mb-8 flex items-center justify-between border-b border-gray-800 pb-6">
        <div className="flex items-center gap-3">
          <ShieldAlert className="h-8 w-8 text-red-500" />
          <h1 className="text-3xl font-bold tracking-tight text-white">PAYSHIELD AI</h1>
        </div>
        <div className="text-sm font-medium px-3 py-1 bg-gray-800 text-gray-300 rounded-full border border-gray-700">
          System Status: Active
        </div>
      </header>

      <main className="max-w-6xl mx-auto space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Risk Score Card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg flex flex-col items-center justify-center relative overflow-hidden h-48">
            <div className="absolute top-4 left-4 text-gray-400 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              <span className="text-sm font-semibold uppercase tracking-wider">Risk Score</span>
            </div>
            <div className={`mt-6 text-7xl font-black ${mockData.risk_score > 0.8 ? 'text-red-500' : 'text-green-500'}`}>
              {(mockData.risk_score * 100).toFixed(0)}
            </div>
            <div className="text-gray-400 mt-2">Percentile Risk</div>
          </div>

          {/* Decision Card */}
          <div className={`bg-gray-900 border rounded-xl p-6 shadow-lg flex flex-col items-center justify-center h-48 ${isBlock ? 'border-red-900/50 bg-red-950/20' : 'border-green-900/50 bg-green-950/20'}`}>
            <div className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-2">
              AI Decision
            </div>
            <div className={`text-5xl font-extrabold tracking-widest ${isBlock ? 'text-red-500' : 'text-green-500'}`}>
              {mockData.decision}
            </div>
            {isBlock && (
              <div className="mt-4 flex items-center gap-2 text-red-400 text-sm bg-red-950/50 px-3 py-1 rounded-full">
                <AlertTriangle className="w-4 h-4" />
                Transaction Terminated
              </div>
            )}
          </div>

          {/* Reasons Card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg h-48 overflow-y-auto">
            <div className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">
              Flagged Indicators
            </div>
            <div className="flex flex-col gap-3">
              {mockData.reasons.map((reason, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2.5 bg-gray-800/50 border border-gray-700 rounded-lg">
                  {reason === 'new_device' && <Smartphone className="w-5 h-5 text-yellow-500" />}
                  {reason === 'high_velocity' && <Zap className="w-5 h-5 text-orange-500" />}
                  <span className="text-gray-200 font-medium capitalize">
                    {reason.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chart Section */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-lg mt-6">
          <div className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Risk Velocity Analysis
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="#9CA3AF" 
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  dy={10}
                />
                <YAxis 
                  stroke="#9CA3AF" 
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 1]}
                  dx={-10}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#F3F4F6', borderRadius: '0.5rem' }}
                  itemStyle={{ color: '#F87171', fontWeight: 'bold' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#EF4444" 
                  strokeWidth={3}
                  dot={{ fill: '#EF4444', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 8, fill: '#DC2626', stroke: '#FECACA' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </main>
    </div>
  );
}
