"use client";

import React, { useMemo, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  Play,
  RefreshCw,
  Target,
  Zap,
  Lock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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

type TimelinePoint = {
  event: number;
  risk: number;
  blocked: number;
};

function formatAttackType(type: string) {
  return type
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function getAttackReason(type: string) {
  switch (type) {
    case "ACCOUNT_TAKEOVER":
      return "Foreign location + suspicious device + high-value burst";

    case "SYNTHETIC_IDENTITY":
      return "Shared device/network infrastructure across identities";

    case "AI_IMPERSONATION":
      return "High-risk location and anomalous device signals";

    case "SMURFING":
      return "Multiple source accounts converging on a common recipient";

    case "ADAPTIVE_MUTATION":
      return "Mutated transaction pattern retained high-risk behavioural signals";

    default:
      return "Multiple anomalous transaction signals detected";
  }
}

function getAttackColor(type: string) {
  switch (type) {
    case "ACCOUNT_TAKEOVER":
      return "text-rose-700 bg-rose-50 border-rose-100";

    case "SYNTHETIC_IDENTITY":
      return "text-orange-700 bg-orange-50 border-orange-100";

    case "AI_IMPERSONATION":
      return "text-purple-700 bg-purple-50 border-purple-100";

    case "SMURFING":
      return "text-amber-700 bg-amber-50 border-amber-100";

    case "ADAPTIVE_MUTATION":
      return "text-indigo-700 bg-indigo-50 border-indigo-100";

    default:
      return "text-slate-700 bg-slate-50 border-slate-100";
  }
}

export default function BattleDashboard() {
  const [rounds, setRounds] = useState(5);
  const [battle, setBattle] = useState<BattleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  async function runBattle() {
    setLoading(true);
    setError("");
    setExpanded(null);

    try {
      const response = await fetch(`${API_BASE}/api/adversarial-battle`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rounds,
        }),
      });

      if (!response.ok) {
        throw new Error("Battle API request failed");
      }

      const data: BattleResponse = await response.json();

      setBattle(data);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to PayShield backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  const results = battle?.results ?? [];

  const totalAttacks = results.length;

  const blocked = results.filter(
    (result) => result.decision === "BLOCK"
  ).length;

  const reviewed = results.filter(
    (result) => result.decision === "REVIEW"
  ).length;

  const approved = results.filter(
    (result) => result.decision === "APPROVE"
  ).length;

  const averageRisk =
    totalAttacks > 0
      ? results.reduce((sum, result) => sum + result.risk_score, 0) /
        totalAttacks
      : 0;

  const mitigationRate =
    totalAttacks > 0 ? ((blocked + reviewed) / totalAttacks) * 100 : 0;

  const attackBreakdown = useMemo(() => {
    const counts: Record<string, number> = {};

    results.forEach((result) => {
      counts[result.attack_type] =
        (counts[result.attack_type] || 0) + 1;
    });

    return Object.entries(counts).map(([type, count]) => ({
      type,
      count,
    }));
  }, [results]);

  const timeline: TimelinePoint[] = results.map((result, index) => ({
    event: index + 1,
    risk: Math.round(result.risk_score * 100),
    blocked: result.decision === "BLOCK" ? 100 : 0,
  }));

  return (
    <div className="w-full space-y-6">

      {/* HEADER */}
      <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">

          <div>
            <div className="flex items-center gap-2 mb-3">
              <ShieldAlert className="w-5 h-5 text-rose-600" />

              <span className="text-xs font-semibold uppercase tracking-wider text-rose-600">
                Red Team vs Blue Team
              </span>
            </div>

            <h1 className="text-3xl font-extrabold text-slate-900">
              Adversarial Battle
            </h1>

            <p className="text-sm text-slate-500 mt-2">
              Generate adversarial payment attacks and evaluate PayShield's
              real-time defensive response.
            </p>
          </div>

          <div className="flex items-center gap-3">

            <select
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
              disabled={loading}
              className="h-11 rounded-xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 outline-none focus:border-blue-500"
            >
              <option value={1}>1 Round</option>
              <option value={2}>2 Rounds</option>
              <option value={3}>3 Rounds</option>
              <option value={4}>4 Rounds</option>
              <option value={5}>5 Rounds</option>
              <option value={6}>6 Rounds</option>
              <option value={8}>8 Rounds</option>
              <option value={10}>10 Rounds</option>
            </select>

            <button
              onClick={runBattle}
              disabled={loading}
              className="h-11 px-5 rounded-xl bg-slate-950 text-white text-sm font-semibold flex items-center gap-2 hover:bg-slate-800 disabled:opacity-60 transition"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Battle
                </>
              )}
            </button>

          </div>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        )}
      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">

        {/* ATTACKS */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Threat Load
            </span>

            <ShieldAlert className="w-4 h-4 text-rose-500" />

          </div>

          <div className="mt-8 flex items-end gap-2">

            <span className="text-5xl font-extrabold text-rose-600">
              {totalAttacks}
            </span>

            <span className="text-sm text-slate-400 mb-2">
              attack vectors
            </span>

          </div>

          <p className="text-xs text-slate-400 mt-3">
            Generated by Red Team
          </p>

        </div>

        {/* BLOCKED */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Blocked
            </span>

            <ShieldCheck className="w-4 h-4 text-emerald-500" />

          </div>

          <div className="mt-8 flex items-end gap-2">

            <span className="text-5xl font-extrabold text-emerald-600">
              {blocked}
            </span>

            <span className="text-sm text-slate-400 mb-2">
              attacks
            </span>

          </div>

          <p className="text-xs text-slate-400 mt-3">
            Prevented by Blue Team
          </p>

        </div>

        {/* RISK */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Average Risk
            </span>

            <Activity className="w-4 h-4 text-blue-600" />

          </div>

          <div className="mt-8 flex items-end gap-2">

            <span className="text-5xl font-extrabold text-slate-900">
              {Math.round(averageRisk * 100)}
            </span>

            <span className="text-lg text-slate-400 mb-1">
              /100
            </span>

          </div>

          <p className="text-xs text-slate-400 mt-3">
            Composite PayShield risk score
          </p>

        </div>

        {/* MITIGATION */}
        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Defence Rate
            </span>

            <Target className="w-4 h-4 text-indigo-600" />

          </div>

          <div className="mt-8 flex items-end gap-2">

            <span className="text-5xl font-extrabold text-indigo-600">
              {Math.round(mitigationRate)}
            </span>

            <span className="text-lg text-slate-400 mb-1">
              %
            </span>

          </div>

          <p className="text-xs text-slate-400 mt-3">
            Blocked + reviewed attacks
          </p>

        </div>

      </div>

      {/* EMPTY STATE */}
      {!battle && !loading && (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-slate-200 text-center">

          <div className="mx-auto w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-center">
            <Zap className="w-6 h-6 text-slate-400" />
          </div>

          <h2 className="mt-5 text-lg font-bold text-slate-900">
            Ready for adversarial evaluation
          </h2>

          <p className="text-sm text-slate-500 mt-2 max-w-lg mx-auto">
            Launch a Red Team campaign to generate realistic payment attack
            scenarios and measure how PayShield responds.
          </p>

          <button
            onClick={runBattle}
            className="mt-6 px-6 py-3 rounded-xl bg-slate-950 text-white text-sm font-semibold inline-flex items-center gap-2"
          >
            <Play className="w-4 h-4" />
            Start {rounds}-Round Battle
          </button>

        </div>
      )}

      {/* LOADING */}
      {loading && (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-slate-200 text-center">

          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto" />

          <h2 className="mt-5 text-lg font-bold text-slate-900">
            Running adversarial evaluation
          </h2>

          <p className="text-sm text-slate-500 mt-2">
            Red Team is generating attacks while Blue Team evaluates them...
          </p>

        </div>
      )}

      {/* RESULTS */}
      {battle && !loading && (

        <>
          {/* DEFENCE SUMMARY */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <div className="lg:col-span-2 bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

              <div className="flex items-center justify-between mb-7">

                <div>
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Battle Outcome
                  </h2>

                  <p className="text-sm text-slate-400 mt-1">
                    {battle.rounds_completed} rounds completed
                  </p>
                </div>

                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-100">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />

                  <span className="text-xs font-semibold text-emerald-700">
                    DEFENCE ACTIVE
                  </span>
                </div>

              </div>

              <div className="grid grid-cols-3 gap-4">

                <div className="rounded-xl bg-emerald-50 border border-emerald-100 p-5">
                  <div className="text-xs font-semibold uppercase text-emerald-700">
                    Blocked
                  </div>

                  <div className="text-3xl font-extrabold text-emerald-700 mt-3">
                    {blocked}
                  </div>
                </div>

                <div className="rounded-xl bg-amber-50 border border-amber-100 p-5">
                  <div className="text-xs font-semibold uppercase text-amber-700">
                    Review
                  </div>

                  <div className="text-3xl font-extrabold text-amber-700 mt-3">
                    {reviewed}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 border border-slate-200 p-5">
                  <div className="text-xs font-semibold uppercase text-slate-600">
                    Approved
                  </div>

                  <div className="text-3xl font-extrabold text-slate-700 mt-3">
                    {approved}
                  </div>
                </div>

              </div>

            </div>

            {/* ATTACK BREAKDOWN */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

              <div className="flex items-center justify-between mb-6">

                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Attack Composition
                </h2>

                <Activity className="w-4 h-4 text-slate-400" />

              </div>

              <div className="space-y-4">

                {attackBreakdown.map((item) => (

                  <div key={item.type}>

                    <div className="flex items-center justify-between mb-2">

                      <span className="text-xs font-medium text-slate-600">
                        {formatAttackType(item.type)}
                      </span>

                      <span className="text-xs font-bold text-slate-900">
                        {item.count}
                      </span>

                    </div>

                    <div className="h-2 rounded-full bg-slate-100 overflow-hidden">

                      <div
                        className="h-full rounded-full bg-slate-900"
                        style={{
                          width: `${(item.count / totalAttacks) * 100}%`,
                        }}
                      />

                    </div>

                  </div>

                ))}

              </div>

            </div>

          </div>

          {/* TIMELINE */}
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">

            <div className="flex items-center justify-between mb-8">

              <div>

                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Live Combat Timeline
                </h2>

                <p className="text-sm text-slate-400 mt-1">
                  Risk response across generated attack events
                </p>

              </div>

              <div className="p-2 rounded-full bg-slate-50 border border-slate-100">
                <Activity className="w-4 h-4 text-slate-400" />
              </div>

            </div>

            <div className="h-[320px] w-full">

              <ResponsiveContainer width="100%" height="100%">

                <AreaChart
                  data={timeline}
                  margin={{
                    top: 10,
                    right: 10,
                    left: -20,
                    bottom: 0,
                  }}
                >

                  <defs>

                    <linearGradient
                      id="battleRiskGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor="#E11D48"
                        stopOpacity={0.18}
                      />

                      <stop
                        offset="95%"
                        stopColor="#E11D48"
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
                    dataKey="event"
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                    label={{
                      value: "Attack Event",
                      position: "insideBottom",
                      offset: -5,
                      fill: "#94A3B8",
                      fontSize: 11,
                    }}
                  />

                  <YAxis
                    domain={[0, 100]}
                    stroke="#94A3B8"
                    tick={{
                      fill: "#64748B",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                    dx={-10}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderColor: "#E2E8F0",
                      borderRadius: "12px",
                      boxShadow:
                        "0 4px 12px rgba(15, 23, 42, 0.08)",
                    }}
                    formatter={(value) => [
  `${typeof value === "number" ? value : 0}`,
  "Risk Score",
]}
                    labelFormatter={(label) =>
                      `Attack Event ${label}`
                    }
                  />

                  <Area
                    type="monotone"
                    dataKey="risk"
                    stroke="#E11D48"
                    fill="url(#battleRiskGradient)"
                    strokeWidth={3}
                  />

                </AreaChart>

              </ResponsiveContainer>

            </div>

          </div>

          {/* ATTACK EVENTS */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">

            <div className="p-8 border-b border-slate-100">

              <div className="flex items-center justify-between">

                <div>

                  <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Attack Events
                  </h2>

                  <p className="text-sm text-slate-400 mt-1">
                    Red Team scenarios evaluated by PayShield
                  </p>

                </div>

                <span className="text-xs font-semibold text-slate-500">
                  {totalAttacks} EVENTS
                </span>

              </div>

            </div>

            <div className="divide-y divide-slate-100">

              {results.map((result, index) => {

                const isExpanded =
                  expanded === result.scenario_id;

                return (
                  <div key={`${result.scenario_id}-${index}`}>

                    <button
                      onClick={() =>
                        setExpanded(
                          isExpanded
                            ? null
                            : result.scenario_id
                        )
                      }
                      className="w-full text-left p-6 hover:bg-slate-50 transition"
                    >

                      <div className="flex items-center gap-5">

                        {/* EVENT NUMBER */}
                        <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center flex-shrink-0">

                          <span className="text-xs font-bold text-slate-500">
                            {String(index + 1).padStart(2, "0")}
                          </span>

                        </div>

                        {/* MAIN */}
                        <div className="flex-1 min-w-0">

                          <div className="flex flex-wrap items-center gap-2">

                            <span className="font-semibold text-sm text-slate-900">
                              {formatAttackType(
                                result.attack_type
                              )}
                            </span>

                            <span
                              className={`text-[11px] font-semibold px-2.5 py-1 rounded-md border ${getAttackColor(
                                result.attack_type
                              )}`}
                            >
                              RED TEAM
                            </span>

                          </div>

                          <div className="text-xs text-slate-400 mt-1">
                            {result.scenario_id}
                          </div>

                        </div>

                        {/* RISK */}
                        <div className="hidden sm:block text-right">

                          <div className="text-[11px] uppercase tracking-wider text-slate-400">
                            Risk
                          </div>

                          <div className="text-lg font-extrabold text-rose-600">
                            {Math.round(
                              result.risk_score * 100
                            )}
                          </div>

                        </div>

                        {/* DECISION */}
                        <div>

                          <span
                            className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg border ${
                              result.decision === "BLOCK"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-100"
                                : result.decision === "REVIEW"
                                  ? "bg-amber-50 text-amber-700 border-amber-100"
                                  : "bg-slate-50 text-slate-700 border-slate-200"
                            }`}
                          >

                            {result.decision === "BLOCK" ? (
                              <ShieldCheck className="w-3.5 h-3.5" />
                            ) : (
                              <Lock className="w-3.5 h-3.5" />
                            )}

                            {result.decision}

                          </span>

                        </div>

                        {/* ARROW */}
                        <div className="text-slate-400">

                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}

                        </div>

                      </div>

                    </button>

                    {/* EXPANDED DETAILS */}
                    {isExpanded && (

                      <div className="px-6 pb-6">

                        <div className="ml-[60px] rounded-xl bg-slate-50 border border-slate-100 p-6">

                          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                            <div className="lg:col-span-2">

                              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                                Attack Description
                              </div>

                              <p className="text-sm text-slate-700 mt-2 leading-6">
                                {result.description}
                              </p>

                            </div>

                            <div>

                              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                                Detection Signals
                              </div>

                              <p className="text-sm text-slate-700 mt-2 leading-6">
                                {getAttackReason(
                                  result.attack_type
                                )}
                              </p>

                            </div>

                          </div>

                          <div className="mt-6 pt-5 border-t border-slate-200 flex flex-wrap gap-6">

                            <div>

                              <div className="text-[11px] uppercase tracking-wider text-slate-400">
                                Scenario ID
                              </div>

                              <div className="text-xs font-semibold text-slate-700 mt-1">
                                {result.scenario_id}
                              </div>

                            </div>

                            <div>

                              <div className="text-[11px] uppercase tracking-wider text-slate-400">
                                Risk Score
                              </div>

                              <div className="text-xs font-semibold text-rose-600 mt-1">
                                {result.risk_score.toFixed(4)}
                              </div>

                            </div>

                            <div>

                              <div className="text-[11px] uppercase tracking-wider text-slate-400">
                                Blue Team Decision
                              </div>

                              <div className="text-xs font-semibold text-emerald-600 mt-1">
                                {result.decision}
                              </div>

                            </div>

                          </div>

                        </div>

                      </div>

                    )}

                  </div>
                );
              })}

            </div>

          </div>

        </>

      )}

    </div>
  );
}
