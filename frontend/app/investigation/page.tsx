"use client";

import React, { useEffect, useState } from "react";
import {
  AlertOctagon,
  ShieldAlert,
  ShieldCheck,
  Fingerprint,
  MapPin,
  CreditCard,
  Activity,
  Box,
  Loader2,
  User,
  Network,
  RefreshCw,
  Zap,
  Globe2,
  BrainCircuit,
  CircleCheck,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

/* =========================================================
   TYPES
   ========================================================= */

type ConnectedNode = {
  id: string;
  type: string;
};

type ConnectedEdge = {
  source: string;
  target: string;
  relation: string;
  txn_id?: string | null;
};

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

  connected_entities?: {
    nodes: ConnectedNode[];
    edges: ConnectedEdge[];
  };
};

type TransactionsResponse =
  | Transaction[]
  | {
      value: Transaction[];
      Count?: number;
    };

type RiskSignal = {
  label: string;
  value: number;
  description: string;
  icon: React.ReactNode;
};

type EvidenceItem = {
  title: string;
  detail: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  icon: React.ReactNode;
};

/* =========================================================
   MAIN COMPONENT
   ========================================================= */

export default function InvestigationDashboard() {
  const [transaction, setTransaction] =
    useState<Transaction | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /* =======================================================
     LOAD INVESTIGATION
     ======================================================= */

  async function loadInvestigation() {
    try {
      setLoading(true);
      setError("");

      /* ---------------------------------------------------
         1. Get latest transaction
         --------------------------------------------------- */

      const recentResponse = await fetch(
        `${API_BASE}/api/transactions?limit=1`,
        {
          cache: "no-store",
        }
      );

      if (!recentResponse.ok) {
        throw new Error(
          `Unable to fetch recent transactions (${recentResponse.status})`
        );
      }

      const recentData: TransactionsResponse =
        await recentResponse.json();

      const recentTransactions: Transaction[] =
        Array.isArray(recentData)
          ? recentData
          : recentData.value || [];

      if (recentTransactions.length === 0) {
        throw new Error(
          "No transactions are available for investigation."
        );
      }

      /* ---------------------------------------------------
         2. Get complete transaction
         --------------------------------------------------- */

      const latestTxnId =
        recentTransactions[0].txn_id;

      const detailResponse = await fetch(
        `${API_BASE}/api/transactions/${encodeURIComponent(
          latestTxnId
        )}`,
        {
          cache: "no-store",
        }
      );

      if (!detailResponse.ok) {
        throw new Error(
          `Unable to fetch transaction details (${detailResponse.status})`
        );
      }

      const detailData: Transaction =
        await detailResponse.json();

      setTransaction(detailData);
    } catch (err) {
      console.error(
        "Failed to load investigation:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load investigation data from PAYSHIELD backend."
      );
    } finally {
      setLoading(false);
    }
  }

  /* =======================================================
     EFFECT
     
     IMPORTANT:
     This is the only effect and it is ALWAYS called.
     ======================================================= */

  useEffect(() => {
    loadInvestigation();
  }, []);

  /* =======================================================
     LOADING STATE
     ======================================================= */

  if (loading) {
    return (
      <div className="w-full min-h-[600px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">

          <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
          </div>

          <div className="text-sm font-semibold text-slate-600">
            Loading investigation...
          </div>

          <div className="text-xs text-slate-400">
            Fetching transaction intelligence
          </div>

        </div>
      </div>
    );
  }

  /* =======================================================
     ERROR STATE
     ======================================================= */

  if (error || !transaction) {
    return (
      <div className="w-full">

        <div className="bg-white rounded-2xl p-10 border border-rose-200 shadow-sm">

          <div className="flex items-start gap-4">

            <div className="w-11 h-11 rounded-xl bg-rose-50 flex items-center justify-center flex-shrink-0">
              <AlertOctagon className="w-6 h-6 text-rose-600" />
            </div>

            <div>

              <div className="font-bold text-slate-900 text-lg">
                Investigation Unavailable
              </div>

              <div className="text-sm text-slate-500 mt-1">
                {error ||
                  "No transaction is available for investigation."}
              </div>

              <button
                onClick={loadInvestigation}
                className="mt-5 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition"
              >
                <RefreshCw className="w-4 h-4" />
                Retry Investigation
              </button>

            </div>

          </div>

        </div>

      </div>
    );
  }

  /* =======================================================
     DERIVED VALUES
     
     These are NOT hooks.
     They are safe after the loading/error returns.
     ======================================================= */

  const riskScore = Number(
    transaction.risk_score || 0
  );

  const riskPercent = Math.min(
    100,
    Math.max(0, riskScore * 100)
  );

  const decision = String(
    transaction.decision || ""
  ).toUpperCase();

  const isBlocked =
    decision === "BLOCK" ||
    decision === "BLOCKED";

  const isReview =
    decision === "REVIEW";

  const isApproved =
    decision === "APPROVE" ||
    decision === "APPROVED";

  const formattedTimestamp =
    new Date(
      transaction.timestamp
    ).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  const connectedNodes =
    transaction.connected_entities?.nodes || [];

  const connectedEdges =
    transaction.connected_entities?.edges || [];

  /* =======================================================
     RISK SIGNALS
     ======================================================= */

  const riskSignals: RiskSignal[] = [
    {
      label: "Device Risk",
      value: Number(transaction.device_risk || 0),
      description:
        "Device reputation and fingerprint signal",
      icon: (
        <Fingerprint className="w-4 h-4" />
      ),
    },

    {
      label: "IP Risk",
      value: Number(transaction.ip_risk || 0),
      description:
        "Origin network reputation signal",
      icon: (
        <Globe2 className="w-4 h-4" />
      ),
    },

    {
      label: "Country Risk",
      value: Number(transaction.country_risk || 0),
      description:
        "Geographic anomaly signal",
      icon: (
        <MapPin className="w-4 h-4" />
      ),
    },
  ];

  /* =======================================================
     EVIDENCE
     
     IMPORTANT:
     This is now a normal calculation, NOT useMemo.
     Therefore there is no hook-order problem.
     ======================================================= */

  const evidence: EvidenceItem[] = [];

  if (
    Number(transaction.velocity_1h || 0) >= 8
  ) {
    evidence.push({
      title: "High transaction velocity",

      detail:
        `${transaction.velocity_1h} transactions detected within 1 hour`,

      severity: "HIGH",

      icon: (
        <Zap className="w-4 h-4" />
      ),
    });
  }

  if (
    Number(transaction.device_risk || 0) >= 0.7
  ) {
    evidence.push({
      title: "Suspicious device signal",

      detail:
        `Device risk score ${(Number(
          transaction.device_risk
        ) * 100).toFixed(0)}/100`,

      severity:
        Number(transaction.device_risk) >= 0.9
          ? "CRITICAL"
          : "HIGH",

      icon: (
        <Fingerprint className="w-4 h-4" />
      ),
    });
  }

  if (
    Number(transaction.ip_risk || 0) >= 0.7
  ) {
    evidence.push({
      title: "High-risk network origin",

      detail:
        `IP risk score ${(Number(
          transaction.ip_risk
        ) * 100).toFixed(0)}/100 from ${transaction.ip_address}`,

      severity:
        Number(transaction.ip_risk) >= 0.9
          ? "CRITICAL"
          : "HIGH",

      icon: (
        <Network className="w-4 h-4" />
      ),
    });
  }

  if (
    Number(transaction.country_risk || 0) >= 0.7
  ) {
    evidence.push({
      title: "Geographic risk detected",

      detail:
        `Country risk score ${(Number(
          transaction.country_risk
        ) * 100).toFixed(0)}/100 --- ${transaction.country}`,

      severity:
        Number(transaction.country_risk) >= 0.9
          ? "CRITICAL"
          : "HIGH",

      icon: (
        <MapPin className="w-4 h-4" />
      ),
    });
  }

  if (
    Number(transaction.amount || 0) >= 100000
  ) {
    evidence.push({
      title: "High-value transaction",

      detail:
        `Attempted amount: ${
          transaction.currency === "INR"
            ? "₹"
            : ""
        }${Number(
          transaction.amount || 0
        ).toLocaleString("en-IN")}`,

      severity: "HIGH",

      icon: (
        <CreditCard className="w-4 h-4" />
      ),
    });
  }

  /* =======================================================
     DECISION TEXT
     ======================================================= */

  const decisionTitle =
    isBlocked
      ? "Transaction blocked"
      : isReview
        ? "Transaction sent for review"
        : "Transaction approved";

  const decisionDescription =
    isBlocked
      ? "PayShield detected a combination of elevated transaction, device, network and geographic risk signals."
      : isReview
        ? "PayShield detected elevated risk signals that require additional review."
        : "PayShield did not detect sufficient risk to block the transaction.";

  /* =======================================================
     PAGE
     ======================================================= */

  return (
    <div className="w-full space-y-6">

      {/* ===================================================
          PAGE HEADER
          =================================================== */}

      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">

        <div>

          <div className="flex items-center gap-2 text-blue-600 mb-2">

            <ShieldAlert className="w-4 h-4" />

            <span className="text-xs font-bold uppercase tracking-wider">
              Fraud Investigation
            </span>

          </div>

          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900">
            Transaction Intelligence
          </h1>

          <p className="text-sm text-slate-500 mt-1">
            Explainable risk assessment powered by PayShield.
          </p>

        </div>

        <button
          onClick={loadInvestigation}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 shadow-sm text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>

      </div>


      {/* ===================================================
          TRANSACTION HEADER
          =================================================== */}

      <div className="bg-white rounded-2xl p-7 md:p-8 shadow-sm border border-slate-200">

        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">

          <div>

            <div
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-bold uppercase tracking-wider ${
                isBlocked
                  ? "text-rose-700 bg-rose-50 border-rose-100"
                  : isReview
                    ? "text-amber-700 bg-amber-50 border-amber-100"
                    : "text-emerald-700 bg-emerald-50 border-emerald-100"
              }`}
            >

              {isBlocked ? (
                <AlertOctagon className="w-4 h-4" />
              ) : isReview ? (
                <ShieldAlert className="w-4 h-4" />
              ) : (
                <ShieldCheck className="w-4 h-4" />
              )}

              Transaction {decision}

            </div>

            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 mt-4">
              {transaction.txn_id}
            </h2>

            <div className="text-slate-400 text-sm font-mono mt-2">
              {formattedTimestamp}
            </div>

          </div>


          <div className="lg:text-right">

            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Amount Attempted
            </div>

            <div className="text-4xl md:text-5xl font-extrabold text-slate-900">

              {transaction.currency === "INR"
                ? "₹"
                : ""}

              {Number(
                transaction.amount || 0
              ).toLocaleString("en-IN", {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
              })}

              <span className="text-xl font-medium text-slate-400 ml-2">
                {transaction.currency}
              </span>

            </div>

          </div>

        </div>

      </div>


      {/* ===================================================
          DECISION BANNER
          =================================================== */}

      <div
        className={`rounded-2xl border p-6 ${
          isBlocked
            ? "bg-rose-50 border-rose-100"
            : isReview
              ? "bg-amber-50 border-amber-100"
              : "bg-emerald-50 border-emerald-100"
        }`}
      >

        <div className="flex items-start gap-4">

          <div
            className={`w-11 h-11 rounded-xl flex items-center justify-center ${
              isBlocked
                ? "bg-white text-rose-600"
                : isReview
                  ? "bg-white text-amber-600"
                  : "bg-white text-emerald-600"
            }`}
          >

            {isBlocked ? (
              <ShieldAlert className="w-6 h-6" />
            ) : isReview ? (
              <AlertOctagon className="w-6 h-6" />
            ) : (
              <ShieldCheck className="w-6 h-6" />
            )}

          </div>


          <div className="flex-1">

            <div
              className={`text-lg font-extrabold ${
                isBlocked
                  ? "text-rose-800"
                  : isReview
                    ? "text-amber-800"
                    : "text-emerald-800"
              }`}
            >
              {decisionTitle}
            </div>

            <div
              className={`text-sm mt-1 ${
                isBlocked
                  ? "text-rose-700"
                  : isReview
                    ? "text-amber-700"
                    : "text-emerald-700"
              }`}
            >
              {decisionDescription}
            </div>

          </div>


          <div
            className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border text-xs font-bold ${
              isBlocked
                ? "text-rose-700 border-rose-100"
                : isReview
                  ? "text-amber-700 border-amber-100"
                  : "text-emerald-700 border-emerald-100"
            }`}
          >

            <CircleCheck className="w-3.5 h-3.5" />

            ENGINE ACTIVE

          </div>

        </div>

      </div>


      {/* ===================================================
          CORE METRICS
          =================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Composite Risk */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between mb-6">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Composite Risk
            </span>

            <Activity className="w-4 h-4 text-rose-500" />

          </div>

          <div className="flex items-end gap-2">

            <span
              className={`text-5xl font-extrabold ${
                isBlocked
                  ? "text-rose-600"
                  : isReview
                    ? "text-amber-600"
                    : "text-emerald-600"
              }`}
            >
              {riskPercent.toFixed(0)}
            </span>

            <span className="text-sm text-slate-400 mb-2">
              / 100
            </span>

          </div>

          <div className="mt-5 h-2 bg-slate-100 rounded-full overflow-hidden">

            <div
              className={`h-full rounded-full ${
                isBlocked
                  ? "bg-rose-500"
                  : isReview
                    ? "bg-amber-500"
                    : "bg-emerald-500"
              }`}
              style={{
                width: `${riskPercent}%`,
              }}
            />

          </div>

        </div>


        {/* Velocity */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between mb-6">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Transaction Velocity
            </span>

            <Zap className="w-4 h-4 text-orange-500" />

          </div>

          <div className="flex items-end gap-2">

            <span className="text-5xl font-extrabold text-slate-900">
              {transaction.velocity_1h}
            </span>

            <span className="text-sm text-slate-400 mb-2">
              / hour
            </span>

          </div>

          <div className="text-xs text-slate-400 mt-4">
            Recent transaction frequency
          </div>

        </div>


        {/* Active Signals */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between mb-6">

            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Risk Signals
            </span>

            <BrainCircuit className="w-4 h-4 text-indigo-500" />

          </div>

          <div className="flex items-end gap-2">

            <span className="text-5xl font-extrabold text-slate-900">
              {evidence.length}
            </span>

            <span className="text-sm text-slate-400 mb-2">
              indicators
            </span>

          </div>

          <div className="text-xs text-slate-400 mt-4">
            Evidence contributing to the decision
          </div>

        </div>

      </div>


      {/* ===================================================
          USER / MERCHANT / DEVICE CONTEXT
          =================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* User */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center">
              <User className="w-4 h-4 text-indigo-500" />
            </div>

            <div>

              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                User
              </div>

              <div className="font-semibold text-slate-900 mt-0.5">
                {transaction.user_id}
              </div>

            </div>

          </div>

        </div>


        {/* Merchant */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center">
              <CreditCard className="w-4 h-4 text-emerald-500" />
            </div>

            <div>

              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Merchant
              </div>

              <div className="font-semibold text-slate-900 mt-0.5">
                {transaction.merchant_id}
              </div>

            </div>

          </div>

        </div>


        {/* Device */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center">
              <Fingerprint className="w-4 h-4 text-blue-500" />
            </div>

            <div className="min-w-0">

              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Device
              </div>

              <div className="font-semibold text-slate-900 mt-0.5 truncate">
                {transaction.device_id}
              </div>

            </div>

          </div>

        </div>

      </div>


      {/* ===================================================
          NETWORK CONTEXT
          =================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* IP */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            IP Address
          </div>

          <div className="text-lg font-bold text-slate-900 mt-2 font-mono">
            {transaction.ip_address}
          </div>

        </div>


        {/* Country */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Country
          </div>

          <div className="text-lg font-bold text-slate-900 mt-2">
            {transaction.country}
          </div>

        </div>


        {/* Graph */}

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">

          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Connected Entities
          </div>

          <div className="flex items-end gap-5 mt-2">

            <div>
              <div className="text-2xl font-extrabold text-slate-900">
                {connectedNodes.length}
              </div>

              <div className="text-xs text-slate-400">
                nodes
              </div>
            </div>

            <div>
              <div className="text-2xl font-extrabold text-slate-900">
                {connectedEdges.length}
              </div>

              <div className="text-xs text-slate-400">
                relationships
              </div>
            </div>

          </div>

        </div>

      </div>


      {/* ===================================================
          RISK SIGNAL BREAKDOWN
          =================================================== */}

      <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

        <div className="flex items-center justify-between mb-7">

          <div>

            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Risk Signal Breakdown
            </h2>

            <p className="text-sm text-slate-400 mt-1">
              Individual signals contributing to the assessment
            </p>

          </div>

          <Activity className="w-5 h-5 text-indigo-500" />

        </div>


        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

          {riskSignals.map((signal) => {

            const percentage = Math.min(
              100,
              Math.max(
                0,
                Number(signal.value || 0) * 100
              )
            );

            return (
              <div
                key={signal.label}
                className="p-5 rounded-xl bg-slate-50 border border-slate-100"
              >

                <div className="flex items-center justify-between">

                  <div className="flex items-center gap-3">

                    <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                      {signal.icon}
                    </div>

                    <div>

                      <div className="text-sm font-bold text-slate-900">
                        {signal.label}
                      </div>

                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {signal.description}
                      </div>

                    </div>

                  </div>

                  <div className="text-lg font-extrabold text-slate-900">
                    {percentage.toFixed(0)}
                  </div>

                </div>


                <div className="mt-4 h-2 bg-white rounded-full overflow-hidden border border-slate-100">

                  <div
                    className={`h-full rounded-full ${
                      percentage >= 90
                        ? "bg-rose-500"
                        : percentage >= 70
                          ? "bg-orange-500"
                          : percentage >= 40
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                    }`}
                    style={{
                      width: `${percentage}%`,
                    }}
                  />

                </div>

              </div>
            );
          })}

        </div>

      </div>


      {/* ===================================================
          WHY PAYSHiELD FLAGGED THIS
          =================================================== */}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* Evidence */}

        <div className="lg:col-span-3 bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between mb-6">

            <div>

              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Why PayShield Flagged This
              </h2>

              <p className="text-sm text-slate-400 mt-1">
                Evidence contributing to the transaction decision
              </p>

            </div>

            <ShieldAlert className="w-5 h-5 text-rose-500" />

          </div>


          {evidence.length === 0 ? (

            <div className="p-5 rounded-xl bg-slate-50 border border-slate-100 text-sm text-slate-500">
              No elevated risk indicators were detected.
            </div>

          ) : (

            <div className="space-y-3">

              {evidence.map(
                (item, index) => (

                  <div
                    key={`${item.title}-${index}`}
                    className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100"
                  >

                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        item.severity === "CRITICAL"
                          ? "bg-rose-100 text-rose-600"
                          : item.severity === "HIGH"
                            ? "bg-orange-100 text-orange-600"
                            : "bg-amber-100 text-amber-600"
                      }`}
                    >
                      {item.icon}
                    </div>


                    <div className="flex-1 min-w-0">

                      <div className="font-bold text-sm text-slate-900">
                        {item.title}
                      </div>

                      <div className="text-xs text-slate-500 mt-1">
                        {item.detail}
                      </div>

                    </div>


                    <div
                      className={`text-[10px] font-extrabold tracking-wider px-2.5 py-1 rounded-md border ${
                        item.severity === "CRITICAL"
                          ? "text-rose-700 bg-rose-50 border-rose-100"
                          : item.severity === "HIGH"
                            ? "text-orange-700 bg-orange-50 border-orange-100"
                            : "text-amber-700 bg-amber-50 border-amber-100"
                      }`}
                    >
                      {item.severity}
                    </div>

                  </div>

                )
              )}

            </div>

          )}

        </div>


        {/* =================================================
            DECISION ENGINE
            ================================================= */}

        <div className="lg:col-span-2 bg-slate-900 rounded-2xl p-7 shadow-sm text-white">

          <div className="flex items-center justify-between mb-7">

            <div>

              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-bold">
                Decision Engine
              </div>

              <div className="text-xl font-extrabold mt-1">
                Risk Assessment
              </div>

            </div>

            <Box className="w-5 h-5 text-slate-400" />

          </div>


          <div className="space-y-5">

            {/* Engine */}

            <div className="flex items-center gap-3">

              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
                <BrainCircuit className="w-4 h-4" />
              </div>

              <div className="flex-1">

                <div className="text-xs text-slate-400">
                  Risk engine
                </div>

                <div className="text-sm font-bold">
                  ML + Rules + Graph
                </div>

              </div>

              <div className="text-xs font-bold text-emerald-400">
                ACTIVE
              </div>

            </div>


            <div className="h-px bg-white/10" />


            {/* Score */}

            <div>

              <div className="text-xs text-slate-400 mb-2">
                Composite score
              </div>

              <div className="text-4xl font-extrabold">
                {riskPercent.toFixed(1)}

                <span className="text-lg text-slate-500">
                  {" "}
                  / 100
                </span>
              </div>

            </div>


            <div className="h-px bg-white/10" />


            {/* Decision */}

            <div>

              <div className="text-xs text-slate-400 mb-2">
                Final action
              </div>

              <div
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-extrabold ${
                  isBlocked
                    ? "bg-rose-500/15 text-rose-300"
                    : isReview
                      ? "bg-amber-500/15 text-amber-300"
                      : "bg-emerald-500/15 text-emerald-300"
                }`}
              >

                {isBlocked ? (
                  <ShieldAlert className="w-4 h-4" />
                ) : isReview ? (
                  <AlertOctagon className="w-4 h-4" />
                ) : (
                  <ShieldCheck className="w-4 h-4" />
                )}

                {decision}

              </div>

            </div>


            <div className="h-px bg-white/10" />


            {/* Model */}

            <div>

              <div className="text-xs text-slate-400 mb-3">
                Assessment pipeline
              </div>

              <div className="space-y-2">

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">
                    ML signals
                  </span>
                  <span className="text-emerald-400 font-bold">
                    ACTIVE
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">
                    Rule engine
                  </span>
                  <span className="text-emerald-400 font-bold">
                    ACTIVE
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">
                    Graph analysis
                  </span>
                  <span className="text-emerald-400 font-bold">
                    ACTIVE
                  </span>
                </div>

              </div>

            </div>


            <div className="pt-2">

              <div className="text-xs leading-5 text-slate-400">
                Decision generated from the transaction&apos;s
                observed risk signals and PayShield&apos;s configured
                decision logic.
              </div>

            </div>

          </div>

        </div>

      </div>


      {/* ===================================================
          GRAPH ENTITIES
          =================================================== */}

      {connectedNodes.length > 0 && (

        <div className="bg-white rounded-2xl p-7 shadow-sm border border-slate-200">

          <div className="flex items-center justify-between mb-6">

            <div>

              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Connected Entity Analysis
              </h2>

              <p className="text-sm text-slate-400 mt-1">
                Network entities associated with this transaction
              </p>

            </div>

            <Network className="w-5 h-5 text-indigo-500" />

          </div>


          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {connectedNodes.map(
              (node) => (

                <div
                  key={node.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-100"
                >

                  <div className="flex items-center gap-3">

                    <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                      <Network className="w-4 h-4 text-indigo-500" />
                    </div>

                    <div>

                      <div className="text-sm font-bold text-slate-900">
                        {node.id}
                      </div>

                      <div className="text-[11px] text-slate-400 uppercase tracking-wider mt-0.5">
                        {node.type}
                      </div>

                    </div>

                  </div>

                </div>

              )
            )}

          </div>


          {connectedEdges.length > 0 && (

            <div className="mt-5 pt-5 border-t border-slate-100">

              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                Relationships
              </div>

              <div className="space-y-2">

                {connectedEdges.map(
                  (edge, index) => (

                    <div
                      key={`${edge.source}-${edge.target}-${index}`}
                      className="flex flex-col sm:flex-row sm:items-center gap-2 p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                    >

                      <span className="font-semibold text-slate-700">
                        {edge.source}
                      </span>

                      <span className="text-slate-400">
                        →
                      </span>

                      <span className="font-semibold text-slate-700">
                        {edge.target}
                      </span>

                      <span className="sm:ml-auto px-2 py-1 rounded-md bg-white border border-slate-200 text-slate-500 uppercase tracking-wider">
                        {edge.relation}
                      </span>

                    </div>

                  )
                )}

              </div>

            </div>

          )}

        </div>

      )}


      {/* ===================================================
          FOOTER
          =================================================== */}

      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">

          <div className="flex items-center gap-2">

            <ShieldCheck className="w-4 h-4 text-emerald-500" />

            <span className="text-sm font-semibold text-slate-700">
              PayShield decision engine active
            </span>

          </div>

          <div className="text-xs text-slate-400 font-mono">
            Transaction ID: {transaction.txn_id}
          </div>

        </div>

      </div>

    </div>
  );
}


