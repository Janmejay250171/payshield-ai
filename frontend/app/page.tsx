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
  RefreshCw,
  ShieldCheck,
  ArrowUpRight,
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

type TransactionsResponse =
  | Transaction[]
  | {
      value: Transaction[];
      Count?: number;
    };

export default function CommandCenter() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadDashboard(isRefresh = false) {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const [metricsResponse, transactionsResponse] =
        await Promise.all([
          fetch(`${API_BASE}/api/metrics`, {
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/transactions?limit=10`, {
            cache: "no-store",
          }),
        ]);

      if (!metricsResponse.ok || !transactionsResponse.ok) {
        throw new Error("Backend request failed");
      }

      const metricsData: Metrics =
        await metricsResponse.json();

      const transactionsData: TransactionsResponse =
        await transactionsResponse.json();

      const transactionList: Transaction[] =
        Array.isArray(transactionsData)
          ? transactionsData
          : transactionsData.value || [];

      setMetrics(metricsData);
      setTransactions(transactionList);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to PayShield backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const latestTransaction = transactions[0];

  const riskScore =
    latestTransaction?.risk_score ?? 0;

  const decision =
    latestTransaction?.decision ?? "N/A";

  /*
   * ---------------------------------------------------------
   * HISTORICAL RISK DATA
   * ---------------------------------------------------------
   */

  const historicalData = [...transactions]
    .reverse()
    .map((transaction, index) => ({
      event: index + 1,
      time: new Date(
        transaction.timestamp
      ).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      score: transaction.risk_score,
    }));

  /*
   * ---------------------------------------------------------
   * RISK REASONS
   * ---------------------------------------------------------
   */

  const reasons = latestTransaction
    ? [
        latestTransaction.velocity_1h >= 8
          ? "High transaction velocity"
          : null,

        latestTransaction.device_risk >= 0.7
          ? "High device risk"
          : null,

        latestTransaction.ip_risk >= 0.7
          ? "High IP risk"
          : null,

        latestTransaction.country_risk >= 0.7
          ? "High country risk"
          : null,

        latestTransaction.amount >= 100000
          ? "High transaction amount"
          : null,
      ].filter(Boolean)
    : [];

  /*
   * ---------------------------------------------------------
   * DECISION HELPERS
   * ---------------------------------------------------------
   */

  const decisionLabel =
    decision === "BLOCK"
      ? "Transaction terminated"
      : decision === "REVIEW"
        ? "Manual review required"
        : decision === "APPROVE"
          ? "Transaction allowed"
          : "Awaiting evaluation";

  const decisionColor =
    decision === "BLOCK"
      ? "text-rose-600"
      : decision === "REVIEW"
        ? "text-amber-600"
        : decision === "APPROVE"
          ? "text-emerald-600"
          : "text-slate-900";

  /*
   * ---------------------------------------------------------
   * PAGE
   * ---------------------------------------------------------
   */

  return (
    <div className="w-full space-y-6">

      {/* =====================================================
          PAGE HEADER
          ===================================================== */}

      <header className="flex flex-col gap-5 rounded-2xl border border-slate-200 bg-white px-7 py-6 shadow-sm md:flex-row md:items-center md:justify-between">

        <div>
          <div className="mb-2 flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50">
              <ShieldCheck className="h-4 w-4 text-blue-600" />
            </div>

            <span className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">
              Command Center
            </span>
          </div>

          <h1 className="text-2xl font-extrabold tracking-tight text-slate-950 md:text-3xl">
            Real-Time Fraud Monitoring
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Live transaction intelligence and automated PayShield defense.
          </p>
        </div>

        <button
          type="button"
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw
            className={`h-4 w-4 ${
              refreshing ? "animate-spin" : ""
            }`}
          />

          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {/* =====================================================
          ERROR
          ===================================================== */}

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm font-medium text-rose-700">
          <ShieldAlert className="h-5 w-5 shrink-0" />
          {error}
        </div>
      )}

      {/* =====================================================
          TOP KPI CARDS
          ===================================================== */}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-3">

        {/* RISK SCORE */}

        <div className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">

          <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-rose-50 blur-2xl" />

          <div className="relative flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
              Risk Score
            </span>

            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-50">
              <Activity className="h-4 w-4 text-rose-500" />
            </div>
          </div>

          <div className="relative mt-8 flex items-end justify-between">

            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-black tracking-tight text-rose-600">
                {loading
                  ? "..."
                  : Math.round(riskScore * 100)}
              </span>

              <span className="text-sm font-medium text-slate-400">
                / 100
              </span>
            </div>

            <span className="inline-flex items-center gap-1.5 rounded-lg border border-rose-100 bg-rose-50 px-2.5 py-1.5 text-xs font-bold text-rose-600">
              <TrendingUp className="h-3 w-3" />
              Live
            </span>

          </div>
        </div>

        {/* DECISION */}

        <div className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">

          <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-indigo-50 blur-2xl" />

          <div className="relative flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
              Automated Decision
            </span>

            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50">
              <ShieldAlert className="h-4 w-4 text-indigo-500" />
            </div>
          </div>

          <div className="relative mt-8 flex items-end justify-between gap-3">

            <span
              className={`text-4xl font-black tracking-tight ${decisionColor}`}
            >
              {loading ? "..." : decision}
            </span>

            <span className="text-right text-xs font-medium text-slate-400">
              {decisionLabel}
            </span>

          </div>
        </div>

        {/* SYSTEM STATUS */}

        <div className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">

          <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-emerald-50 blur-2xl" />

          <div className="relative flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
              System Status
            </span>

            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
              <Zap className="h-4 w-4 text-emerald-500" />
            </div>
          </div>

          <div className="relative mt-8 flex items-end justify-between">

            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
              </span>

              <span className="text-4xl font-black tracking-tight text-emerald-600">
                Active
              </span>
            </div>

            <span className="text-xs font-medium text-slate-400">
              {metrics
                ? `${metrics.total_transactions} transactions`
                : "..."}
            </span>

          </div>
        </div>
      </div>

      {/* =====================================================
          MAIN ANALYTICS
          ===================================================== */}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">

        {/* FLAGGED INDICATORS */}

        <div className="flex min-h-[27rem] flex-col rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">

          <div className="mb-7 flex items-center justify-between">

            <div>
              <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                Flagged Indicators
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Evidence contributing to the decision
              </p>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-100 bg-slate-50">
              <ShieldAlert className="h-4 w-4 text-slate-400" />
            </div>

          </div>

          <div className="flex flex-1 flex-col gap-4">

            {reasons.length === 0 ? (
              <div className="flex flex-1 items-center justify-center text-sm text-slate-400">
                No major indicators detected.
              </div>
            ) : (
              reasons.map((reason, idx) => {

                const reasonText = String(reason);

                const isDevice =
                  reasonText.toLowerCase().includes("device");

                return (
                  <div
                    key={idx}
                    className="group flex items-center gap-4 rounded-xl border border-slate-100 bg-slate-50/80 p-4 transition-all hover:border-slate-200 hover:bg-white hover:shadow-sm"
                  >

                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm">

                      {isDevice ? (
                        <Smartphone className="h-5 w-5 text-blue-600" />
                      ) : (
                        <Zap className="h-5 w-5 text-orange-500" />
                      )}

                    </div>

                    <div className="min-w-0 flex-1">

                      <div className="flex items-center justify-between gap-2">
                        <div className="text-sm font-bold capitalize text-slate-900">
                          {reasonText}
                        </div>

                        <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-300 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                      </div>

                      <div className="mt-1 text-xs text-slate-400">
                        Primary risk indicator detected
                      </div>

                    </div>
                  </div>
                );
              })
            )}

          </div>
        </div>

        {/* RISK CHART */}

        <div className="flex min-h-[27rem] flex-col rounded-2xl border border-slate-200 bg-white p-7 shadow-sm lg:col-span-2">

          <div className="mb-5 flex items-center justify-between">

            <div>
              <h2 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                Risk Trend
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Recent transaction risk progression
              </p>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-100 bg-slate-50">
              <Activity className="h-4 w-4 text-blue-500" />
            </div>

          </div>

          <div className="min-h-0 flex-1 w-full">

            {historicalData.length > 0 ? (
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart
                  data={historicalData}
                  margin={{
                    top: 15,
                    right: 15,
                    bottom: 5,
                    left: 0,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#F1F5F9"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="event"
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 11,
                    }}
                    tickLine={false}
                    axisLine={false}
                    dy={12}
                    tickFormatter={(value) => `#${value}`}
                  />

                  <YAxis
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 11,
                    }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 1]}
                    tickFormatter={(value) =>
                      `${Math.round(value * 100)}`
                    }
                    width={35}
                  />

                  <Tooltip
                    cursor={{
                      stroke: "#CBD5E1",
                      strokeDasharray: "4 4",
                    }}
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#E2E8F0",
                      borderRadius: "12px",
                      boxShadow:
                        "0 8px 24px rgba(15, 23, 42, 0.08)",
                      padding: "10px 12px",
                    }}
                    labelFormatter={(label) => {
                      const item =
                        historicalData.find(
                          (entry) =>
                            entry.event === Number(label)
                        );

                      return item
                        ? `Event #${label} • ${item.time}`
                        : `Event #${label}`;
                    }}
                    formatter={(value) => [
                      `${Math.round(
                        Number(value) * 100
                      )} / 100`,
                      "Risk",
                    ]}
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
              <div className="flex h-full items-center justify-center text-sm text-slate-400">
                {loading
                  ? "Loading transaction data..."
                  : "No transaction data"}
              </div>
            )}

          </div>

          {/* Chart footer */}

          {latestTransaction && (
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-4">

              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="h-2 w-2 rounded-full bg-blue-500" />
                Latest evaluation
              </div>

              <div className="text-xs font-semibold text-slate-600">
                {latestTransaction.txn_id}
              </div>

            </div>
          )}

        </div>
      </div>

      {/* =====================================================
          LIVE TRANSACTION SUMMARY
          ===================================================== */}

      {latestTransaction && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">

            <div>
              <div className="mb-1 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />

                <span className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                  Latest Transaction
                </span>
              </div>

              <div className="text-lg font-extrabold text-slate-950">
                {latestTransaction.txn_id}
              </div>

              <div className="mt-1 text-xs text-slate-400">
                {latestTransaction.user_id} •{" "}
                {latestTransaction.merchant_id}
              </div>
            </div>

            <div className="flex items-center gap-8">

              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Amount
                </div>

                <div className="mt-1 text-lg font-extrabold text-slate-900">
                  {latestTransaction.currency}{" "}
                  {latestTransaction.amount.toLocaleString(
                    "en-IN",
                    {
                      maximumFractionDigits: 2,
                    }
                  )}
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Risk
                </div>

                <div className="mt-1 text-lg font-extrabold text-rose-600">
                  {Math.round(riskScore * 100)}
                </div>
              </div>

              <div
                className={`rounded-lg border px-3 py-2 text-xs font-bold ${
                  decision === "BLOCK"
                    ? "border-rose-100 bg-rose-50 text-rose-600"
                    : decision === "REVIEW"
                      ? "border-amber-100 bg-amber-50 text-amber-600"
                      : "border-emerald-100 bg-emerald-50 text-emerald-600"
                }`}
              >
                {decision}
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
}