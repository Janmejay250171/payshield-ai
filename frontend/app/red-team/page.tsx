"use client";

import React, { useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Target,
  TrendingUp,
  ShieldAlert,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";

type BattleResult = {
  scenario_id: string;
  attack_type: string;
  description: string;
  risk_score: number;
  decision: string;
};

type BattleResponse = {
  rounds_completed: number;
  results: BattleResult[];
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function formatAttackType(type: string) {
  return type
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getDecisionClass(decision: string) {
  if (decision === "BLOCK") {
    return "text-rose-600 bg-rose-50 border-rose-100";
  }

  if (decision === "REVIEW") {
    return "text-amber-600 bg-amber-50 border-amber-100";
  }

  return "text-emerald-600 bg-emerald-50 border-emerald-100";
}

function getDecisionIcon(decision: string) {
  if (decision === "BLOCK") {
    return <XCircle className="w-4 h-4" />;
  }

  if (decision === "REVIEW") {
    return <AlertTriangle className="w-4 h-4" />;
  }

  return <CheckCircle2 className="w-4 h-4" />;
}

export default function RedTeamDashboard() {
  const [rounds, setRounds] = useState(5);
  const [data, setData] = useState<BattleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runSimulation() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE}/api/adversarial-battle`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            rounds,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Backend returned HTTP ${response.status}`
        );
      }

      const result: BattleResponse = await response.json();

      setData(result);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the PayShield backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  const results = data?.results || [];

  const blocked = results.filter(
    (r) => r.decision === "BLOCK"
  ).length;

  const reviewed = results.filter(
    (r) => r.decision === "REVIEW"
  ).length;

  const approved = results.filter(
    (r) => r.decision === "APPROVE"
  ).length;

  const bypassRate =
    results.length > 0
      ? approved / results.length
      : 0;

  const averageRisk =
    results.length > 0
      ? results.reduce(
          (sum, r) => sum + r.risk_score,
          0
        ) / results.length
      : 0;

  const attackFamilies = useMemo(() => {
    const groups: Record<
      string,
      {
        total: number;
        blocked: number;
        reviewed: number;
        approved: number;
      }
    > = {};

    for (const result of results) {
      if (!groups[result.attack_type]) {
        groups[result.attack_type] = {
          total: 0,
          blocked: 0,
          reviewed: 0,
          approved: 0,
        };
      }

      groups[result.attack_type].total += 1;

      if (result.decision === "BLOCK") {
        groups[result.attack_type].blocked += 1;
      } else if (result.decision === "REVIEW") {
        groups[result.attack_type].reviewed += 1;
      } else {
        groups[result.attack_type].approved += 1;
      }
    }

    return Object.entries(groups).map(
      ([name, stats]) => ({
        name,
        ...stats,
        detectionRate:
          stats.total > 0
            ? stats.blocked / stats.total
            : 0,
      })
    );
  }, [results]);

  const timelineData = results.map(
    (result, index) => ({
      round: `R${index + 1}`,
      risk: Number(
        result.risk_score.toFixed(3)
      ),
      blocked:
        result.decision === "BLOCK" ? 1 : 0,
    })
  );

  return (
    <div className="w-full space-y-6">

      {/* ===================================================== */}
      {/* HEADER */}
      {/* ===================================================== */}

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">

          <div>
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-blue-600" />

              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Adversarial Security Testing
              </span>
            </div>

            <h1 className="text-2xl font-extrabold text-slate-900">
              Red Team Simulation
            </h1>

            <p className="text-sm text-slate-500 mt-1">
              Generate adversarial transaction mutations and evaluate
              them through the live Blue Team risk engine.
            </p>
          </div>

          <div className="flex items-center gap-3">

            <select
              value={rounds}
              onChange={(e) =>
                setRounds(Number(e.target.value))
              }
              disabled={loading}
              className="h-11 px-4 rounded-xl border border-slate-200 bg-white text-sm font-semibold text-slate-700 outline-none"
            >
              <option value={3}>3 rounds</option>
              <option value={5}>5 rounds</option>
              <option value={10}>10 rounds</option>
              <option value={15}>15 rounds</option>
              <option value={20}>20 rounds</option>
            </select>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="h-11 px-5 rounded-xl bg-blue-600 text-white text-sm font-semibold flex items-center gap-2 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Simulation
                </>
              )}
            </button>

          </div>
        </div>

        {error && (
          <div className="mt-5 px-4 py-3 rounded-xl border border-rose-100 bg-rose-50 text-rose-700 text-sm font-medium">
            {error}
          </div>
        )}
      </div>


      {/* ===================================================== */}
      {/* KPI CARDS */}
      {/* ===================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

        {/* Generated */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Attacks Generated
            </span>

            <Activity className="w-4 h-4 text-blue-600" />
          </div>

          <div className="mt-7">
            <span className="text-5xl font-extrabold text-slate-900">
              {results.length}
            </span>

            <span className="ml-2 text-sm text-slate-400">
              scenarios
            </span>
          </div>

          <div className="mt-4 text-xs text-slate-400">
            {data
              ? `${data.rounds_completed} rounds completed`
              : "No simulation executed yet"}
          </div>
        </div>


        {/* Detection */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Detection Rate
            </span>

            <ShieldAlert className="w-4 h-4 text-emerald-500" />
          </div>

          <div className="mt-7">
            <span className="text-5xl font-extrabold text-slate-900">
              {results.length
                ? `${((blocked / results.length) * 100).toFixed(1)}`
                : "—"}
            </span>

            {results.length > 0 && (
              <span className="text-2xl font-bold text-slate-900">
                %
              </span>
            )}
          </div>

          <div className="mt-4 text-xs text-slate-400">
            Transactions blocked by Blue Team
          </div>
        </div>


        {/* Average risk */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Average Risk
            </span>

            <TrendingUp className="w-4 h-4 text-blue-600" />
          </div>

          <div className="mt-7">
            <span className="text-5xl font-extrabold text-slate-900">
              {results.length
                ? `${(averageRisk * 100).toFixed(1)}`
                : "—"}
            </span>

            {results.length > 0 && (
              <span className="text-2xl font-bold text-slate-400">
                /100
              </span>
            )}
          </div>

          <div className="mt-4 text-xs text-slate-400">
            Mean Blue Team risk score
          </div>
        </div>


        {/* Bypass */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              System Bypass
            </span>

            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>

          <div className="mt-7">
            <span className="text-5xl font-extrabold text-rose-600">
              {results.length
                ? `${(bypassRate * 100).toFixed(1)}`
                : "—"}
            </span>

            {results.length > 0 && (
              <span className="text-2xl font-bold text-rose-600">
                %
              </span>
            )}
          </div>

          <div className="mt-4 text-xs text-slate-400">
            Adversarial scenarios approved by engine
          </div>
        </div>

      </div>


      {/* ===================================================== */}
      {/* LIVE RESULT SUMMARY */}
      {/* ===================================================== */}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Blocked
              </div>

              <div className="text-3xl font-extrabold text-rose-600 mt-2">
                {blocked}
              </div>
            </div>

            <XCircle className="w-8 h-8 text-rose-500" />
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Review
              </div>

              <div className="text-3xl font-extrabold text-amber-600 mt-2">
                {reviewed}
              </div>
            </div>

            <AlertTriangle className="w-8 h-8 text-amber-500" />
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Approved
              </div>

              <div className="text-3xl font-extrabold text-emerald-600 mt-2">
                {approved}
              </div>
            </div>

            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
          </div>

        </div>
      )}


      {/* ===================================================== */}
      {/* MAIN CONTENT */}
      {/* ===================================================== */}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Active attack families */}

        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 lg:col-span-1 min-h-[28rem]">

          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Attack Families
            </h2>

            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
              <Target className="w-4 h-4 text-slate-400" />
            </div>
          </div>

          {!data ? (
            <div className="h-80 flex items-center justify-center text-center">
              <div>
                <Target className="w-10 h-10 text-slate-200 mx-auto mb-4" />

                <p className="text-sm font-semibold text-slate-500">
                  No simulation data
                </p>

                <p className="text-xs text-slate-400 mt-1">
                  Run an adversarial simulation
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">

              {attackFamilies.map((family) => (

                <div
                  key={family.name}
                  className="space-y-3"
                >

                  <div className="flex justify-between items-end">

                    <span className="text-slate-900 font-semibold text-sm">
                      {formatAttackType(family.name)}
                    </span>

                    <span className="text-xs text-slate-400">
                      {family.blocked}/{family.total} blocked
                    </span>

                  </div>

                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">

                    <div
                      className="h-full bg-blue-600 rounded-full transition-all"
                      style={{
                        width: `${
                          family.detectionRate * 100
                        }%`,
                      }}
                    />

                  </div>

                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>
                      Detection{" "}
                      {(family.detectionRate * 100).toFixed(0)}%
                    </span>

                    <span>
                      {family.total} scenario
                      {family.total !== 1 ? "s" : ""}
                    </span>
                  </div>

                </div>

              ))}

            </div>
          )}

        </div>


        {/* Timeline */}

        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 lg:col-span-2 min-h-[28rem] flex flex-col">

          <div className="flex items-center justify-between mb-8">

            <div>
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Adversarial Risk Timeline
              </h2>

              <p className="text-xs text-slate-400 mt-1">
                Risk generated by the real Blue Team engine
              </p>
            </div>

            <div className="p-2 bg-slate-50 rounded-full border border-slate-100">
              <TrendingUp className="w-4 h-4 text-slate-400" />
            </div>

          </div>

          <div className="flex-1 min-h-[20rem]">

            {!data ? (

              <div className="h-full min-h-[20rem] flex items-center justify-center text-center">
                <div>
                  <Activity className="w-10 h-10 text-slate-200 mx-auto mb-4" />

                  <p className="text-sm font-semibold text-slate-500">
                    Waiting for simulation
                  </p>

                  <p className="text-xs text-slate-400 mt-1">
                    Results will appear here
                  </p>
                </div>
              </div>

            ) : (

              <ResponsiveContainer width="100%" height="100%">

                <AreaChart
                  data={timelineData}
                  margin={{
                    top: 10,
                    right: 10,
                    left: -20,
                    bottom: 0,
                  }}
                >

                  <defs>

                    <linearGradient
                      id="riskGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor="#2563EB"
                        stopOpacity={0.18}
                      />

                      <stop
                        offset="95%"
                        stopColor="#2563EB"
                        stopOpacity={0}
                      />
                    </linearGradient>

                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#F1F5F9"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="round"
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                    dy={15}
                  />

                  <YAxis
                    domain={[0, 1]}
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                    dx={-15}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#E2E8F0",
                      borderRadius: "12px",
                      boxShadow:
                        "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                    formatter={(value: any) => [
                      `${(Number(value) * 100).toFixed(1)}%`,
                      "Risk",
                    ]}
                  />

                  <Area
                    type="monotone"
                    dataKey="risk"
                    name="Blue Team Risk"
                    stroke="#2563EB"
                    fillOpacity={1}
                    fill="url(#riskGradient)"
                    strokeWidth={2}
                  />

                </AreaChart>

              </ResponsiveContainer>

            )}

          </div>

        </div>

      </div>


      {/* ===================================================== */}
      {/* ACTUAL BATTLE RESULTS */}
      {/* ===================================================== */}

      {data && (

        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between mb-6">

            <div>
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Red Team → Blue Team Results
              </h2>

              <p className="text-xs text-slate-400 mt-1">
                Every row below was evaluated by the backend risk engine.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              LIVE BACKEND RESULTS
            </div>

          </div>

          <div className="overflow-x-auto">

            <table className="w-full text-left">

              <thead>

                <tr className="border-b border-slate-100">

                  <th className="pb-4 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    Scenario
                  </th>

                  <th className="pb-4 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    Attack Type
                  </th>

                  <th className="pb-4 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    Risk
                  </th>

                  <th className="pb-4 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    Decision
                  </th>

                </tr>

              </thead>

              <tbody>

                {results.map((result) => (

                  <tr
                    key={result.scenario_id}
                    className="border-b border-slate-50 last:border-0"
                  >

                    <td className="py-4">
                      <span className="font-mono text-sm font-semibold text-slate-900">
                        {result.scenario_id}
                      </span>
                    </td>

                    <td className="py-4">
                      <span className="text-sm font-medium text-slate-700">
                        {formatAttackType(
                          result.attack_type
                        )}
                      </span>
                    </td>

                    <td className="py-4">
                      <span className="font-mono text-sm font-bold text-slate-900">
                        {(result.risk_score * 100).toFixed(1)}
                      </span>

                      <span className="text-xs text-slate-400 ml-1">
                        / 100
                      </span>
                    </td>

                    <td className="py-4">

                      <span
                        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold ${getDecisionClass(
                          result.decision
                        )}`}
                      >
                        {getDecisionIcon(
                          result.decision
                        )}

                        {result.decision}
                      </span>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        </div>

      )}

    </div>
  );
}


