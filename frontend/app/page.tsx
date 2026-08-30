"use client";

import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, CreditCard, Play, Square, Loader2, CheckCircle2, AlertCircle, Zap } from 'lucide-react';
import { fetchWrapper } from '../lib/apiClient';

export default function CommandCenter() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simStatus, setSimStatus] = useState<'idle' | 'running' | 'stopped'>('idle');
  const [batchId, setBatchId] = useState<string | null>(null);
  const [demoStep, setDemoStep] = useState<string | null>(null);

  const [metricsData, setMetricsData] = useState<any>(null);
  const [metricsError, setMetricsError] = useState<boolean>(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      const { data, error } = await fetchWrapper('api/metrics');
      if (error || !data) {
        setMetricsError(true);
      } else {
        setMetricsData(data);
        setMetricsError(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000);
    return () => clearInterval(interval);
  }, []);

  const totalTransactions = metricsData?.total_processed ?? 0;
  const threatLevel = metricsData?.threat_level ?? 'UNKNOWN';
  const resilienceScore = metricsData?.resilience_score ?? 0;

  const handleStartSimulation = async () => {
    setIsLoading(true);
    setError(null);
    setBatchId(null);
    
    try {
      const response = await fetch('http://localhost:8001/api/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ count: 100, attack_ratio: 0.2 }),
      });

      if (!response.ok) {
        throw new Error('Simulation backend unreachable or returned an error.');
      }

      const data = await response.json();
      setBatchId(data.batch_id || `BATCH-${Math.random().toString(36).substring(2, 8).toUpperCase()}`);
      setSimStatus('running');
    } catch (err: any) {
      setError(err.message || 'Failed to connect to simulation backend.');
      setSimStatus('idle');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopSimulation = () => {
    setSimStatus('stopped');
    setBatchId(null);
    setError(null);
    setDemoStep(null);
  };

  const handleDemoMode = async () => {
    setSimStatus('running');
    setBatchId('DEMO-SEQ-001');
    
    // 0s: Normal transactions
    setDemoStep('0s: Initializing normal traffic baseline...');
    await fetchWrapper('api/simulate', {
      method: 'POST',
      body: JSON.stringify({ count: 100, attack_ratio: 0.0 })
    });

    // 20s: ATO
    setTimeout(async () => {
      setDemoStep('20s: Injecting Account Takeover (ATO) attacks...');
      await fetchWrapper('api/generate-attacks', {
        method: 'POST',
        body: JSON.stringify({ family: 'ACCOUNT_TAKEOVER' })
      });
    }, 20000);

    // 40s: Adaptive Attack
    setTimeout(async () => {
      setDemoStep('40s: Injecting Adaptive Mutation attacks...');
      await fetchWrapper('api/generate-attacks', {
        method: 'POST',
        body: JSON.stringify({ family: 'ADAPTIVE_MUTATION' })
      });
    }, 40000);

    // 70s: Stop Simulation
    setTimeout(() => {
      setDemoStep('70s: Halting simulation for manual investigation...');
      setTimeout(() => {
        handleStopSimulation();
      }, 3000);
    }, 70000);
  };

  return (
    <div className="w-full space-y-6">
      
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
        
        {/* Total Transactions */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Transactions</h2>
            <CreditCard className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {metricsError ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : (
              <span className="text-3xl font-bold text-slate-900 tracking-tight">{totalTransactions.toLocaleString()}</span>
            )}
          </div>
        </div>

        {/* Current Threat Level */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Current Threat Level</h2>
            <ShieldAlert className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {metricsError ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : (
              <span className={`text-3xl font-bold tracking-tight ${threatLevel === 'CRITICAL' ? 'text-rose-600' : threatLevel === 'ELEVATED' ? 'text-orange-600' : 'text-slate-900'}`}>
                {threatLevel}
              </span>
            )}
          </div>
        </div>

        {/* System Resilience Score */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">System Resilience Score</h2>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-baseline gap-3">
            {metricsError ? (
              <span className="text-3xl font-bold text-slate-400 tracking-tight">Offline</span>
            ) : (
              <span className="text-3xl font-bold text-slate-900 tracking-tight">{resilienceScore}<span className="text-xl text-slate-400 font-medium">/100</span></span>
            )}
          </div>
        </div>

      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Simulation Controls */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 h-fit">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold text-slate-900">Global System Controls</h2>
            {simStatus === 'running' && (
              <span className="flex items-center gap-2 text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                LIVE BATCH: {batchId}
              </span>
            )}
            {simStatus === 'stopped' && (
              <span className="flex items-center gap-1 text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
                <Square className="w-3 h-3" /> HALTED
              </span>
            )}
          </div>
          
          <p className="text-slate-500 text-sm mb-6">
            Engage the automated attack generator to stress-test the machine learning defense models in real-time.
          </p>

          {error && (
            <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-700 text-sm font-medium">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {error}
            </div>
          )}

          {demoStep && (
            <div className="mb-6 p-4 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center gap-3 text-indigo-700 text-sm font-medium shadow-sm">
              <Loader2 className="w-5 h-5 flex-shrink-0 animate-spin text-indigo-600" />
              <div className="flex flex-col">
                <span className="font-bold text-indigo-900">Demo Sequence Active</span>
                <span>{demoStep}</span>
              </div>
            </div>
          )}

          <div className="flex items-center gap-4">
            <button 
              onClick={handleStartSimulation}
              disabled={isLoading || simStatus === 'running'}
              className="flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold py-2.5 px-5 rounded-xl transition-colors shadow-sm min-w-[160px]"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : simStatus === 'running' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )}
              {isLoading ? 'Starting...' : simStatus === 'running' ? 'Running' : 'Start Simulation'}
            </button>
            <button 
              onClick={handleStopSimulation}
              disabled={simStatus !== 'running'}
              className="flex items-center justify-center gap-2 bg-white hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed text-slate-700 text-sm font-semibold py-2.5 px-5 rounded-xl transition-colors border border-slate-200 shadow-sm min-w-[160px]"
            >
              <Square className="w-4 h-4 fill-current" />
              Stop Simulation
            </button>
            <div className="h-8 w-px bg-slate-200 mx-2"></div>
            <button 
              onClick={handleDemoMode}
              disabled={simStatus === 'running' || demoStep !== null}
              className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold py-2.5 px-5 rounded-xl transition-colors shadow-sm min-w-[160px]"
            >
              <Zap className="w-4 h-4 fill-current" />
              Demo Mode
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
