"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Activity,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Ban,
  RefreshCw,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

type Metrics = {
  total_transactions: number;
  approved: number;
  reviewed: number;
  blocked: number;
  average_risk_score: number;
};

type Transaction = {
  id?: number;
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

type TransactionResponse =
  | Transaction[]
  | {
      value?: Transaction[];
      transactions?: Transaction[];
      data?: Transaction[];
    };

function decisionClass(decision: string) {
  switch (decision) {
    case "BLOCK":
      return "bg-rose-50 text-rose-700 border-rose-100";

    case "REVIEW":
      return "bg-orange-50 text-orange-700 border-orange-100";

    case "APPROVE":
      return "bg-emerald-50 text-emerald-700 border-emerald-100";

    default:
      return "bg-slate-50 text-slate-600 border-slate-100";
  }
}

function riskClass(score: number) {
  if (score >= 0.8) {
    return "text-rose-600";
  }

  if (score >= 0.5) {
    return "text-orange-500";
  }

  return "text-emerald-600";
}

function normalizeTransactions(
  response: TransactionResponse
): Transaction[] {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response.value)) {
    return response.value;
  }

  if (Array.isArray(response.transactions)) {
    return response.transactions;
  }

  if (Array.isArray(response.data)) {
    return response.data;
  }

  return [];
}

function safeNumber(value: unknown, fallback = 0) {
  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : fallback;
}

export default function BlueTeamDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadBlueTeamData = useCallback(
    async (showRefresh = false) => {
      try {
        if (showRefresh) {
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

        if (!metricsResponse.ok) {
          throw new Error(
            `Metrics request failed: ${metricsResponse.status}`
          );
        }

        if (!transactionsResponse.ok) {
          throw new Error(
            `Transactions request failed: ${transactionsResponse.status}`
          );
        }

        const metricsData =
          (await metricsResponse.json()) as Metrics;

        const transactionsRaw =
          (await transactionsResponse.json()) as TransactionResponse;

        const normalizedTransactions =
          normalizeTransactions(transactionsRaw);

        setMetrics(metricsData);
        setTransactions(normalizedTransactions);
      } catch (err) {
        console.error("Blue Team API error:", err);

        setError(
          "Unable to connect to PayShield backend. Make sure FastAPI is running on port 8000."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    []
  );

  useEffect(() => {
    void loadBlueTeamData();

    const interval = window.setInterval(() => {
      void loadBlueTeamData(true);
    }, 10000);

    return () => {
      window.clearInterval(interval);
    };
  }, [loadBlueTeamData]);

  const interceptionRate = useMemo(() => {
    if (!metrics || metrics.total_transactions <= 0) {
      return 0;
    }

    return (
      ((safeNumber(metrics.blocked) +
        safeNumber(metrics.reviewed)) /
        safeNumber(metrics.total_transactions)) *
      100
    );
  }, [metrics]);

  const averageRisk = useMemo(() => {
    if (!metrics) {
      return 0;
    }

    return safeNumber(metrics.average_risk_score) * 100;
  }, [metrics]);

  const decisionData = useMemo(() => {
    if (!metrics) {
      return [];
    }

    return [
      {
        decision: "Blocked",
        count: safeNumber(metrics.blocked),
      },
      {
        decision: "Review",
        count: safeNumber(metrics.reviewed),
      },
      {
        decision: "Approved",
        count: safeNumber(metrics.approved),
      },
    ];
  }, [metrics]);

  /*
   * Sort newest first.
   *
   * Backend normally returns newest transactions first.
   * We still sort here so the frontend remains reliable.
   */
  const sortedTransactions = useMemo(() => {
    return [...transactions].sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();

      if (
        Number.isFinite(timeA) &&
        Number.isFinite(timeB)
      ) {
        return timeB - timeA;
      }

      return safeNumber(b.id) - safeNumber(a.id);
    });
  }, [transactions]);

  const latestTransaction = sortedTransactions[0];

  const signalData = useMemo(() => {
    if (!latestTransaction) {
      return [];
    }

    const deviceRisk = Math.max(
      0,
      Math.min(
        1,
        safeNumber(latestTransaction.device_risk)
      )
    );

    const ipRisk = Math.max(
      0,
      Math.min(
        1,
        safeNumber(latestTransaction.ip_risk)
      )
    );

    const countryRisk = Math.max(
      0,
      Math.min(
        1,
        safeNumber(latestTransaction.country_risk)
      )
    );

    const velocity = Math.max(
      0,
      Math.min(
        1,
        safeNumber(latestTransaction.velocity_1h) / 10
      )
    );

    return [
      {
        signal: "Device",
        value: Number(deviceRisk.toFixed(2)),
        percentage: Math.round(deviceRisk * 100),
      },
      {
        signal: "IP",
        value: Number(ipRisk.toFixed(2)),
        percentage: Math.round(ipRisk * 100),
      },
      {
        signal: "Country",
        value: Number(countryRisk.toFixed(2)),
        percentage: Math.round(countryRisk * 100),
      },
      {
        signal: "Velocity",
        value: Number(velocity.toFixed(2)),
        percentage: Math.round(velocity * 100),
      },
    ];
  }, [latestTransaction]);

  return (
    <div className="w-full space-y-6">

      {/* ERROR */}
      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 flex items-center gap-3">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />

          <span>{error}</span>
        </div>
      )}

      {/* HEADER */}
      <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

        <div className="flex items-center justify-between gap-6">

          <div>

            <div className="flex items-center gap-2 mb-2">

              <ShieldCheck className="w-5 h-5 text-blue-600" />

              <span className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                Blue Team
              </span>

            </div>

            <h1 className="text-2xl font-bold text-slate-900">
              Real-Time Threat Detection
            </h1>

            <p className="text-sm text-slate-500 mt-1">
              Live transaction scoring and automated defense telemetry.
            </p>

          </div>

          <button
            onClick={() => void loadBlueTeamData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 ${
                refreshing ? "animate-spin" : ""
              }`}
            />

            Refresh
          </button>

        </div>

      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* THREAT INTERCEPTION */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-48 flex flex-col justify-between">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Threat Interception
            </span>

            <ShieldCheck className="w-4 h-4 text-blue-600" />

          </div>

          <div className="flex items-end justify-between">

            <span className="text-5xl font-extrabold text-blue-600">
              {loading
                ? "..."
                : `${interceptionRate.toFixed(1)}%`}
            </span>

            <span className="text-xs text-slate-400">
              Blocked + Review
            </span>

          </div>

        </div>

        {/* AVERAGE RISK */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-48 flex flex-col justify-between">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Average Risk
            </span>

            <Activity className="w-4 h-4 text-rose-500" />

          </div>

          <div className="flex items-end justify-between">

            <span
              className={`text-5xl font-extrabold ${
                loading
                  ? "text-slate-300"
                  : riskClass(averageRisk / 100)
              }`}
            >
              {loading
                ? "..."
                : Math.round(averageRisk)}
            </span>

            <span className="text-sm text-slate-400">
              / 100
            </span>

          </div>

        </div>

        {/* TRANSACTIONS */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-48 flex flex-col justify-between">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Transactions Evaluated
            </span>

            <Activity className="w-4 h-4 text-indigo-500" />

          </div>

          <div className="flex items-end justify-between">

            <span className="text-5xl font-extrabold text-slate-900">
              {loading
                ? "..."
                : metrics?.total_transactions ?? 0}
            </span>

            <span className="text-sm text-slate-400">
              Live
            </span>

          </div>

        </div>

      </div>

      {/* CHART GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* DECISION DISTRIBUTION */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-[28rem] flex flex-col">

          <div className="flex items-center justify-between mb-8">

            <div>

              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Decision Distribution
              </h2>

              <p className="text-sm text-slate-400 mt-1">
                Current backend transaction outcomes
              </p>

            </div>

            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
              <Activity className="w-4 h-4 text-slate-400" />
            </div>

          </div>

          <div className="flex-1 min-h-0">

            {loading ? (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                Loading defense telemetry...
              </div>
            ) : (
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={decisionData}
                  margin={{
                    top: 10,
                    right: 10,
                    left: -20,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#F1F5F9"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="decision"
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <YAxis
                    allowDecimals={false}
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#E2E8F0",
                      borderRadius: "12px",
                    }}
                  />

                  <Bar
                    dataKey="count"
                    fill="#2563EB"
                    radius={[6, 6, 0, 0]}
                    barSize={42}
                  />

                </BarChart>
              </ResponsiveContainer>
            )}

          </div>

        </div>

        {/* LATEST RISK SIGNALS */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 h-[28rem] flex flex-col">

          <div className="flex items-center justify-between mb-6">

            <div>

              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Latest Risk Signals
              </h2>

              <p className="text-sm text-slate-400 mt-1">
                Signals from the latest evaluated transaction
              </p>

            </div>

            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
              <ShieldAlert className="w-4 h-4 text-slate-400" />
            </div>

          </div>

          {latestTransaction && (
            <div className="mb-4 flex items-center justify-between rounded-xl bg-slate-50 border border-slate-100 px-4 py-3">

              <div>

                <p className="text-xs text-slate-400 uppercase tracking-wide">
                  Latest transaction
                </p>

                <p className="text-sm font-semibold text-slate-900">
                  {latestTransaction.txn_id}
                </p>

              </div>

              <span
                className={`px-3 py-1.5 rounded-md border text-xs font-semibold ${decisionClass(
                  latestTransaction.decision
                )}`}
              >
                {latestTransaction.decision}
              </span>

            </div>
          )}

          <div className="flex-1 min-h-0">

            {!latestTransaction ? (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                No transaction telemetry available.
              </div>
            ) : (
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={signalData}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 30,
                    left: 20,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#F1F5F9"
                    horizontal={false}
                  />

                  <XAxis
                    type="number"
                    domain={[0, 1]}
                    ticks={[0, 0.25, 0.5, 0.75, 1]}
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 11,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <YAxis
                    type="category"
                    dataKey="signal"
                    width={65}
                    stroke="#64748B"
                    tick={{
                      fill: "#64748B",
                      fontSize: 13,
                      fontWeight: 500,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    formatter={(
                      value: unknown
                    ) => {
                      const numericValue =
                        safeNumber(value);

                      return [
                        `${Math.round(
                          numericValue * 100
                        )}%`,
                        "Risk",
                      ];
                    }}
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#E2E8F0",
                      borderRadius: "12px",
                    }}
                  />

                  <Bar
                    dataKey="value"
                    fill="#2563EB"
                    radius={[0, 6, 6, 0]}
                    barSize={22}
                    minPointSize={4}
                  />

                </BarChart>
              </ResponsiveContainer>
            )}

          </div>

        </div>

      </div>

      {/* RECENT DETECTION EVENTS */}
      <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

        <div className="flex items-center justify-between mb-8">

          <div>

            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Recent Detection Events
            </h2>

            <p className="text-sm text-slate-400 mt-1">
              Transactions currently stored by PayShield
            </p>

          </div>

          <Activity className="w-4 h-4 text-slate-400" />

        </div>

        <div className="overflow-x-auto">

          {sortedTransactions.length === 0 ? (
            <div className="py-10 text-center text-sm text-slate-400">
              No transactions available.
            </div>
          ) : (
            <table className="w-full">

              <thead>

                <tr className="border-b border-slate-100">

                  <th className="text-left py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Transaction
                  </th>

                  <th className="text-left py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    User
                  </th>

                  <th className="text-right py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Amount
                  </th>

                  <th className="text-right py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Risk
                  </th>

                  <th className="text-right py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Decision
                  </th>

                </tr>

              </thead>

              <tbody>

                {sortedTransactions.map(
                  (transaction) => (
                    <tr
                      key={
                        transaction.txn_id
                      }
                      className="border-b border-slate-50 last:border-0"
                    >

                      <td className="py-4">

                        <div className="flex items-center gap-3">

                          <div className="w-9 h-9 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center">

                            {transaction.decision ===
                            "BLOCK" ? (
                              <Ban className="w-4 h-4 text-rose-500" />
                            ) : transaction.decision ===
                              "REVIEW" ? (
                              <AlertTriangle className="w-4 h-4 text-orange-500" />
                            ) : (
                              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            )}

                          </div>

                          <div>

                            <div className="text-sm font-semibold text-slate-900">
                              {
                                transaction.txn_id
                              }
                            </div>

                            <div className="text-xs text-slate-400">
                              {
                                transaction.merchant_id
                              }
                            </div>

                          </div>

                        </div>

                      </td>

                      <td className="py-4 text-sm text-slate-600">
                        {transaction.user_id}
                      </td>

                      <td className="py-4 text-right text-sm font-medium text-slate-900">

                        {transaction.currency}{" "}
                        {safeNumber(
                          transaction.amount
                        ).toLocaleString(
                          "en-IN"
                        )}

                      </td>

                      <td
                        className={`py-4 text-right text-sm font-bold ${riskClass(
                          safeNumber(
                            transaction.risk_score
                          )
                        )}`}
                      >
                        {Math.round(
                          safeNumber(
                            transaction.risk_score
                          ) * 100
                        )}
                      </td>

                      <td className="py-4 text-right">

                        <span
                          className={`inline-flex items-center px-3 py-1.5 rounded-md border text-xs font-semibold ${decisionClass(
                            transaction.decision
                          )}`}
                        >
                          {
                            transaction.decision
                          }
                        </span>

                      </td>

                    </tr>
                  )
                )}

              </tbody>

            </table>
          )}

        </div>

      </div>

    </div>
  );
}