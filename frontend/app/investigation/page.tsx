"use client";

import React from 'react';
import useSWR from 'swr';
import { Search, AlertOctagon, Fingerprint, MapPin, CreditCard, Activity, Box, Info } from 'lucide-react';

const postFetcher = (url: string) => fetch(url, { 
  method: 'POST', 
  headers: { 'Content-Type': 'application/json' }, 
  body: JSON.stringify({ count: 1, attack_ratio: 1.0 }) 
}).then(res => res.json());

export default function InvestigationDashboard() {
  const { data, error, isLoading } = useSWR('/api/simulate', postFetcher, { refreshInterval: 2000 });

  // Use live data if available, otherwise fallback to prevent crash
  const latestTxn = data?.sample_results?.[0] ?? null;
  
  const txnId = latestTxn?.transaction?.transaction_id ?? 'TXN-9843A-XQ2';
  const amount = latestTxn?.transaction?.amount ?? 4500.00;
  const timestamp = latestTxn?.transaction?.timestamp ?? '2026-08-27T10:24:12Z';
  const xgboostScore = latestTxn?.risk_result?.risk_score ?? 0.94;
  const decision = latestTxn?.risk_result?.decision ?? 'BLOCK';
  const rulesTriggered = latestTxn?.risk_result?.reasons ?? ['Velocity Threshold', 'Impossible Travel'];
  
  const features = {
    ip: latestTxn?.transaction?.ip_address ?? '192.168.1.1 (Proxy)',
    country: latestTxn?.transaction?.country ?? 'RU',
    device_id: latestTxn?.transaction?.device_type ?? 'DEV-NEW-8832',
    time_since_prev: latestTxn?.transaction?.seconds_since_prev ?? 15
  };

  const isBlocked = decision === 'BLOCK' || decision === 'REVIEW';

  return (
    <div className="w-full space-y-6">
      
      {/* Header Summary (Minimalist Fintech Style) */}
      <div className="bg-white rounded-2xl p-8 shadow-sm flex items-center justify-between border border-slate-200">
        <div>
          <div className={`font-semibold flex items-center gap-2 mb-4 text-xs w-fit px-2.5 py-1 rounded-md uppercase tracking-wider ${
            isBlocked ? 'text-rose-700 bg-rose-50 border border-rose-100' : 'text-emerald-700 bg-emerald-50 border border-emerald-100'
          }`}>
            <AlertOctagon className={`w-4 h-4 ${isBlocked ? 'text-rose-600' : 'text-emerald-600'}`} />
            Transaction {decision}
          </div>
          <div className="text-5xl font-extrabold tracking-tight mb-2 text-slate-900">
            {error ? 'OFFLINE' : isLoading ? 'Loading...' : txnId}
          </div>
          <div className="text-slate-400 text-sm font-mono">{timestamp}</div>
        </div>
        <div className="text-right">
          <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Amount Attempted</div>
          <div className="text-5xl font-extrabold text-slate-900">${amount.toFixed(0)} <span className="text-2xl font-medium text-slate-400">USD</span></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* AI Decision Engine */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-80 flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Decision Engine</h2>
            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
               <Box className="w-4 h-4 text-slate-400" />
            </div>
          </div>
          <div className="space-y-8 flex-1">
            <div>
              <div className="flex justify-between text-sm mb-3">
                <span className="text-slate-500 font-medium text-xs uppercase tracking-wider">
                  Risk Score
                </span>
                <span className="text-slate-900 font-extrabold text-lg">{(xgboostScore * 100).toFixed(1)} <span className="text-slate-400 text-sm font-normal">/ 100</span></span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className={`h-2 rounded-full transition-all duration-500 ${isBlocked ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${xgboostScore * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-4">Heuristic Rules Triggered</div>
              <div className="flex flex-col gap-3">
                {rulesTriggered.length === 0 ? (
                  <span className="text-sm text-slate-400 italic">No rules triggered</span>
                ) : rulesTriggered.map((rule: string, i: number) => (
                  <span key={i} className="px-4 py-2.5 bg-slate-50 border border-slate-100 text-slate-900 text-sm font-semibold rounded-xl flex items-center gap-3">
                    <AlertOctagon className="w-4 h-4 text-rose-500" />
                    {rule}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Feature Context */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-80 flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Feature Context</h2>
            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
               <Activity className="w-4 h-4 text-slate-400" />
            </div>
          </div>
          <div className="space-y-3 flex-1 text-sm">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center gap-3 text-slate-500 font-medium"><MapPin className="w-4 h-4 text-blue-600" /> Origin IP / Country</div>
              <div className="font-mono text-slate-900 font-semibold">{features.ip} ({features.country})</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center gap-3 text-slate-500 font-medium"><Fingerprint className="w-4 h-4 text-indigo-500" /> Device ID</div>
              <div className="font-mono text-slate-900 font-semibold">{features.device_id}</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center gap-3 text-slate-500 font-medium"><Activity className="w-4 h-4 text-rose-500" /> Time Since Prev</div>
              <div className="font-semibold text-rose-600">{features.time_since_prev.toFixed(1)} sec</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
