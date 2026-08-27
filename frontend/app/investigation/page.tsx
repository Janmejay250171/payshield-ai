"use client";

import React from 'react';
import { Search, AlertOctagon, Fingerprint, MapPin, CreditCard, Activity, Box, Info } from 'lucide-react';

const mockTxn = {
  id: 'TXN-9843A-XQ2',
  amount: 4500.00,
  currency: 'USD',
  status: 'BLOCKED',
  timestamp: '2026-08-27T10:24:12Z',
  xgboost_score: 0.94,
  rules_triggered: ['R-101 (Velocity)', 'R-103 (Impossible Travel)'],
  features: {
    ip: '192.168.1.1 (Proxy)',
    country: 'RU',
    device_id: 'DEV-NEW-8832',
    account_age_days: 2,
    distance_from_last_txn_km: 8400
  }
};

export default function InvestigationDashboard() {
  return (
    <div className="w-full space-y-6">
      
      {/* Header Summary (Minimalist Fintech Style) */}
      <div className="bg-white rounded-2xl p-8 shadow-sm flex items-center justify-between border border-slate-200">
        <div>
          <div className="font-semibold flex items-center gap-2 mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-100 w-fit px-2.5 py-1 rounded-md uppercase tracking-wider">
            <AlertOctagon className="w-4 h-4 text-rose-600" />
            Transaction Blocked
          </div>
          <div className="text-5xl font-extrabold tracking-tight mb-2 text-slate-900">{mockTxn.id}</div>
          <div className="text-slate-400 text-sm font-mono">{mockTxn.timestamp}</div>
        </div>
        <div className="text-right">
          <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Amount Attempted</div>
          <div className="text-5xl font-extrabold text-slate-900">${mockTxn.amount.toFixed(0)} <span className="text-2xl font-medium text-slate-400">{mockTxn.currency}</span></div>
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
                <span className="text-slate-900 font-extrabold text-lg">{(mockTxn.xgboost_score * 100).toFixed(1)} <span className="text-slate-400 text-sm font-normal">/ 100</span></span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-rose-500 h-2 rounded-full" style={{ width: `${mockTxn.xgboost_score * 100}%` }}></div>
              </div>
            </div>
            <div>
              <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-4">Heuristic Rules Triggered</div>
              <div className="flex flex-col gap-3">
                {mockTxn.rules_triggered.map((rule, i) => (
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
              <div className="flex items-center gap-3 text-slate-500 font-medium"><MapPin className="w-4 h-4 text-blue-600" /> Origin IP</div>
              <div className="font-mono text-slate-900 font-semibold">{mockTxn.features.ip}</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center gap-3 text-slate-500 font-medium"><Fingerprint className="w-4 h-4 text-indigo-500" /> Device ID</div>
              <div className="font-mono text-slate-900 font-semibold">{mockTxn.features.device_id}</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center gap-3 text-slate-500 font-medium"><CreditCard className="w-4 h-4 text-emerald-500" /> Account Age</div>
              <div className="font-semibold text-slate-900">{mockTxn.features.account_age_days} Days</div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
              <div className="flex items-center gap-3 text-slate-500 font-medium"><Activity className="w-4 h-4 text-rose-500" /> Travel Velocity</div>
              <div className="font-semibold text-rose-600">{mockTxn.features.distance_from_last_txn_km} km</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
