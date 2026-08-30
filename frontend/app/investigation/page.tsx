"use client";

import React, { useState, useEffect } from 'react';
import { Search, AlertOctagon, Fingerprint, MapPin, CreditCard, Activity, Box, Info } from 'lucide-react';
import { fetchWrapper } from '../../lib/apiClient';

export default function InvestigationDashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchTransaction = async () => {
      const { data: resData, error: resError } = await fetchWrapper('api/transactions/TXN-82739');
      if (resError || !resData) {
        setError(true);
      } else {
        setData(resData);
        setError(false);
      }
      setIsLoading(false);
    };

    fetchTransaction();
    const interval = setInterval(fetchTransaction, 2000);
    return () => clearInterval(interval);
  }, []);

  const txnId = data?.id ?? 'Waiting...';
  const amount = data?.amount ?? 0;
  const timestamp = new Date().toISOString().split('T')[0] + ' 10:24:12Z';
  const rawScore = data?.xgboost_score ?? 0.0;
  const xgboostScore = rawScore <= 1.0 ? rawScore * 100 : rawScore;
  const decision = data?.status ?? 'PENDING';
  const rulesTriggered = data?.rules_triggered ?? [];
  
  const features = {
    ip: data?.user?.ip_address ?? '192.168.1.1 (Proxy)',
    country: data?.merchant?.category ?? 'Finance',
    device_id: data?.connected_entities?.[0]?.entity_type ?? 'Device_ID',
    time_since_prev: 15
  };

  const isBlocked = decision === 'BLOCK' || decision === 'BLOCKED' || decision === 'REVIEW';

  return (
    <div className="w-full space-y-6">
      
      {/* Header Summary (Minimalist Fintech Style) */}
      <div className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between border border-slate-200 h-fit">
        <div>
          <div className={`font-semibold flex items-center gap-1.5 mb-2 text-[10px] w-fit px-2 py-0.5 rounded-md uppercase tracking-wider ${
            isBlocked ? 'text-rose-700 bg-rose-50 border border-rose-100' : 'text-emerald-700 bg-emerald-50 border border-emerald-100'
          }`}>
            <AlertOctagon className={`w-3 h-3 ${isBlocked ? 'text-rose-600' : 'text-emerald-600'}`} />
            Transaction {decision}
          </div>
          <div className="text-3xl font-bold tracking-tight mb-1 text-slate-900">
            {error ? 'OFFLINE' : isLoading ? 'Loading...' : txnId}
          </div>
          <div className="text-slate-400 text-xs font-mono">{timestamp}</div>
        </div>
        <div className="text-right">
          <div className="text-slate-500 text-[10px] font-semibold uppercase tracking-wider mb-1">Amount Attempted</div>
          <div className="text-3xl font-bold text-slate-900">${amount.toFixed(0)} <span className="text-lg font-medium text-slate-400">USD</span></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* AI Decision Engine */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 h-fit flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Decision Engine</h2>
            <Box className="w-4 h-4 text-slate-400" />
          </div>
          <div className="space-y-5">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-500 font-medium text-xs uppercase tracking-wider">
                  Risk Score
                </span>
                <span className="text-slate-900 font-bold text-base">{isLoading ? '0.0' : xgboostScore.toFixed(1)} <span className="text-slate-400 text-xs font-normal">/ 100</span></span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5">
                <div className={`h-1.5 rounded-full transition-all duration-500 ${isBlocked ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${isLoading ? 0 : xgboostScore}%` }}></div>
              </div>
            </div>
            <div>
              <div className="text-slate-500 text-[10px] font-semibold uppercase tracking-wider mb-3">Heuristic Rules Triggered</div>
              <div className="flex flex-col gap-2">
                {isLoading ? (
                  <span className="text-xs text-slate-400 italic">Loading...</span>
                ) : rulesTriggered.length === 0 ? (
                  <span className="text-xs text-slate-400 italic">No rules triggered</span>
                ) : rulesTriggered.map((rule: any, i: number) => (
                  <span key={i} className="px-3 py-2 bg-slate-50 border border-slate-100 text-slate-900 text-xs font-semibold rounded-lg flex items-center gap-2">
                    <AlertOctagon className="w-3.5 h-3.5 text-rose-500" />
                    {rule.name}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Entity Graph Visualization */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 h-fit flex flex-col relative overflow-hidden">
          <div className="flex items-center justify-between mb-4 relative z-20">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Entity Graph Visualization</h2>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          
          <div className="relative w-full h-64 flex items-center justify-center mt-2">
            {/* SVG Connecting Edges - lowest z-index */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" style={{ top: 0, left: 0 }}>
              {/* Line to Device_ID (Top) */}
              <line x1="50%" y1="50%" x2="50%" y2="15%" className="stroke-slate-400" strokeWidth="2" />
              {/* Line to Previous_Fraud_Acct (Bottom Left) */}
              <line x1="50%" y1="50%" x2="25%" y2="85%" className="stroke-slate-400" strokeWidth="2" />
              {/* Line to Shared_IP (Bottom Right) */}
              <line x1="50%" y1="50%" x2="75%" y2="85%" className="stroke-slate-400" strokeWidth="2" />
            </svg>

            {/* Central Node */}
            <div className="absolute z-10 flex items-center justify-center" style={{ top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
              <div className="bg-black rounded-full w-12 h-12 shadow-md border-[3px] border-white z-10"></div>
              <span className="text-[10px] font-semibold text-slate-800 absolute -bottom-8 bg-white px-2 py-0.5 rounded-md shadow-sm border border-slate-200 whitespace-nowrap z-20">Central_Target</span>
            </div>

            {/* Top Node: Device_ID */}
            <div className="absolute z-10 flex items-center justify-center" style={{ top: '15%', left: '50%', transform: 'translate(-50%, -50%)' }}>
              <div className="bg-black rounded-full w-12 h-12 shadow-md border-[3px] border-white z-10"></div>
              <span className="text-[10px] font-semibold text-slate-800 absolute -bottom-8 bg-white px-2 py-0.5 rounded-md shadow-sm border border-slate-200 whitespace-nowrap z-20">Device_ID</span>
            </div>

            {/* Bottom Left Node: Previous_Fraud_Acct */}
            <div className="absolute z-10 flex items-center justify-center" style={{ top: '85%', left: '25%', transform: 'translate(-50%, -50%)' }}>
              <div className="bg-black rounded-full w-12 h-12 shadow-md border-[3px] border-white z-10"></div>
              <span className="text-[10px] font-semibold text-slate-800 absolute -bottom-8 bg-white px-2 py-0.5 rounded-md shadow-sm border border-slate-200 whitespace-nowrap z-20">Previous_Fraud_Acct</span>
            </div>

            {/* Bottom Right Node: Shared_IP */}
            <div className="absolute z-10 flex items-center justify-center" style={{ top: '85%', left: '75%', transform: 'translate(-50%, -50%)' }}>
              <div className="bg-black rounded-full w-12 h-12 shadow-md border-[3px] border-white z-10"></div>
              <span className="text-[10px] font-semibold text-slate-800 absolute -bottom-8 bg-white px-2 py-0.5 rounded-md shadow-sm border border-slate-200 whitespace-nowrap z-20">Shared_IP</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
