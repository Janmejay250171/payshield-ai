"use client";

import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  Activity,
  Smartphone,
  Zap,
  ShieldAlert,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

type Transaction = {
  id: number;
  txn_id: string;
  user_id: string;
  amount: number;
  currency: string;
  merchant_id: string;
  device_id: string;
  ip_address: string;
  timestamp: string;
  country: string;
  velocity_1h: number;
  device_risk: number;
  ip_risk: number;
  country_risk: number;
  risk_score: number;
  decision: string;
};

type Metrics = {
  total_transactions: number;
  approved: number;
  reviewed: number;
  blocked: number;
  average_risk_score: number;
};

export default function CommandCenter() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [metricsResponse, transactionsResponse] = await Promise.all([
          fetch(`${API_BASE}/api/metrics`),
          fetch(`${API_BASE}/api/transactions?limit=10`),
        ]);

        if (!metricsResponse.ok || !transactionsResponse.ok) {
          throw new Error("Backend request failed");
        }

        const metricsData = await metricsResponse.json();
        const transactionsData = await transactionsResponse.json();

        setMetrics(metricsData);
        setTransactions(transactionsData);
      } catch (err) {
        console.error(err);
        setError(
          "Unable to connect to PayShield backend. Make sure FastAPI is running."
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const latestTransaction = transactions[0];

  const riskScore = latestTransaction?.risk_score ?? 0;
  const decision = latestTransaction?.decision ?? "N/A";

  const historicalData = [...transactions]
    .reverse()
    .map((transaction) => ({
      time: new Date(transaction.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      score: transaction.risk_score,
    }));

  const reasons = latestTransaction
    ? [
        latestTransaction.velocity_1h >= 8
          ? "high velocity"
          : null,
        latestTransaction.device_risk >= 0.7
          ? "high device risk"
          : null,
        latestTransaction.ip_risk >= 0.7
          ? "high IP risk"
          : null,
        latestTransaction.country_risk >= 0.7
          ? "high country risk"
          : null,
        latestTransaction.amount >= 100000
          ? "high transaction amount"
          : null,
      ].filter(Boolean)
    : [];

  return (
    <div className="w-full space-y-6">
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Risk Score */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Risk Score
            </span>
            <Activity className="w-4 h-4 text-rose-500" />
          </div>

          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-rose-600">
              {loading ? "..." : Math.round(riskScore * 100)}
            </span>

            <span className="text-xs font-medium text-rose-600 bg-rose-50 px-2.5 py-1 rounded-md flex items-center gap-1 border border-rose-100">
              <TrendingUp className="w-3 h-3" />
              Live
            </span>
          </div>
        </div>

        {/* Decision */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Automated Decision
            </span>
            <ShieldAlert className="w-4 h-4 text-indigo-500" />
          </div>

          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-slate-900">
              {loading ? "..." : decision}
            </span>

            <span className="text-sm text-slate-400">
              {decision === "BLOCK"
                ? "Terminated"
                : decision === "REVIEW"
                  ? "Manual review"
                  : decision === "APPROVE"
                    ? "Allowed"
                    : ""}
            </span>
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-2xl p-8 shadow-sm flex flex-col justify-between h-48 border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              System Status
            </span>
            <Zap className="w-4 h-4 text-emerald-500" />
          </div>

          <div className="flex items-end justify-between">
            <span className="text-5xl font-extrabold text-emerald-600">
              Active
            </span>

            <span className="text-sm text-slate-400">
              {metrics ? `${metrics.total_transactions} transactions` : "..."}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Flagged Indicators */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 col-span-1 flex flex-col h-[28rem]">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-8">
            Flagged Indicators
          </h2>

          <div className="flex flex-col gap-5 flex-1">
            {reasons.length === 0 ? (
              <div className="text-sm text-slate-400">
                No major indicators detected.
              </div>
            ) : (
              reasons.map((reason, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-4 p-5 bg-slate-50 rounded-xl border border-slate-100"
                >
                  <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm border border-slate-200 flex-shrink-0">
                    {String(reason).includes("device") ? (
                      <Smartphone className="w-5 h-5 text-blue-600" />
                    ) : (
                      <Zap className="w-5 h-5 text-orange-500" />
                    )}
                  </div>

                  <div>
                    <div className="text-slate-900 font-semibold text-sm capitalize">
                      {String(reason)}
                    </div>

                    <div className="text-slate-400 text-sm mt-0.5">
                      Primary risk indicator detected
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 col-span-1 lg:col-span-2 h-[28rem] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Risk Velocity Analysis
            </h2>

            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
              <Activity className="w-4 h-4 text-slate-400" />
            </div>
          </div>

          <div className="flex-1 w-full">
            {historicalData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={historicalData}
                  margin={{
                    top: 5,
                    right: 20,
                    bottom: 5,
                    left: -20,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#F1F5F9"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="time"
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    tickLine={false}
                    axisLine={false}
                    dy={15}
                  />

                  <YAxis
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 1]}
                    dx={-15}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#E2E8F0",
                      borderRadius: "12px",
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#2563EB"
                    strokeWidth={3}
                    dot={{
                      fill: "#ffffff",
                      stroke: "#2563EB",
                      strokeWidth: 2,
                      r: 4,
                    }}
                    activeDot={{
                      r: 6,
                      fill: "#2563EB",
                      stroke: "#EFF6FF",
                      strokeWidth: 4,
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                {loading ? "Loading transaction data..." : "No transaction data"}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}