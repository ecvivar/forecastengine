"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { api, type SimulationProbabilities, type TeamStageProb } from "@/lib/api";
import { formatPercent, getWinColor } from "@/lib/utils";
import SortableTable, { type Column } from "@/components/SortableTable";
import StageProgressBar from "@/components/StageProgressBar";
import { Trophy, Medal, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function KnockoutPage() {
  const [data, setData] = useState<SimulationProbabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"win" | "final" | "sf">("win");

  useEffect(() => {
    api.simulations
      .list()
      .then((sims) => {
        const completed = sims.find((s) => s.status === "completed");
        if (completed) {
          return api.simulations.probabilities(completed.id);
        }
        return null;
      })
      .then(setData)
      .catch((err) => {
        console.error(err);
        setError("Unable to load knockout probabilities.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  if (!data) {
    return (
      <div className="container-page text-center py-12">
        <Trophy className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">No Simulation Data</h2>
        <p className="text-gray-500 mb-4">
          Run a Monte Carlo simulation first to see knockout probabilities.
        </p>
        <Link href="/simulations" className="text-primary-600 hover:underline">Go to Simulations →</Link>
      </div>
    );
  }

  const sorted = [...data.teams].sort((a, b) => {
    if (sortBy === "win") return b.win_prob - a.win_prob;
    if (sortBy === "final") return b.final_prob - a.final_prob;
    return b.sf_prob - a.sf_prob;
  });

  const tabs: { key: typeof sortBy; label: string }[] = [
    { key: "win", label: "Champion" },
    { key: "final", label: "Final" },
    { key: "sf", label: "Semi-Final" },
  ];

  const columns: Column<TeamStageProb>[] = [
    { key: "team_name", label: "Team", render: (t) => <span className="font-medium">{t.team_name}</span> },
    { key: "group_name", label: "Group", align: "center", render: (t) => <span className="text-gray-400">{t.group_name}</span> },
    { key: "qualify_r32_prob", label: "R32", align: "center", render: (t) => <span className={getWinColor(t.qualify_r32_prob)}>{t.qualify_r32_prob.toFixed(1)}%</span>, sortValue: (t) => t.qualify_r32_prob },
    { key: "r16_prob", label: "R16", align: "center", render: (t) => <span className={getWinColor(t.r16_prob)}>{t.r16_prob.toFixed(1)}%</span>, sortValue: (t) => t.r16_prob },
    { key: "qf_prob", label: "QF", align: "center", render: (t) => <span className={getWinColor(t.qf_prob)}>{t.qf_prob.toFixed(1)}%</span>, sortValue: (t) => t.qf_prob },
    { key: "sf_prob", label: "SF", align: "center", render: (t) => <span className={getWinColor(t.sf_prob)}>{t.sf_prob.toFixed(1)}%</span>, sortValue: (t) => t.sf_prob },
    { key: "final_prob", label: "Final", align: "center", render: (t) => <span className={getWinColor(t.final_prob)}>{t.final_prob.toFixed(1)}%</span>, sortValue: (t) => t.final_prob },
    { key: "win_prob", label: "Champion", align: "center", render: (t) => <span className="font-bold text-yellow-600">{t.win_prob.toFixed(1)}%</span>, sortValue: (t) => t.win_prob },
    { key: "avg_points", label: "Avg Pts", align: "center", render: (t) => <span className="text-gray-400">{t.avg_points.toFixed(1)}</span>, sortValue: (t) => t.avg_points },
  ];

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="page-title">Knockout Stage Probabilities</h1>
          <p className="page-subtitle">Based on {data.num_simulations.toLocaleString()} Monte Carlo simulations</p>
        </div>
        <Link href="/bracket" className="text-sm text-primary-600 hover:underline flex items-center gap-1">View Bracket <span>→</span></Link>
      </div>

      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setSortBy(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              sortBy === t.key ? "bg-primary-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {sorted.slice(0, 3).map((t, i) => (
          <Card key={t.team_name} className={`border-2 ${i === 0 ? "border-yellow-400" : i === 1 ? "border-gray-300" : "border-orange-300"}`}>
            <CardContent className="p-6 text-center">
              {i === 0 && <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-2" />}
              {i === 1 && <Medal className="w-8 h-8 text-gray-400 mx-auto mb-2" />}
              {i === 2 && <Medal className="w-8 h-8 text-orange-400 mx-auto mb-2" />}
              <h3 className="text-lg font-bold">{t.team_name}</h3>
              <div className="text-3xl font-bold text-primary-600 mt-2">{t.win_prob.toFixed(1)}%</div>
              <div className="text-sm text-gray-500 mt-1">Win Probability</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Teams — Stage Probabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <SortableTable columns={columns} data={sorted} defaultSort={{ key: "win_prob", dir: "desc" }} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Stage Advancement Profiles — Top 16</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {sorted.slice(0, 16).map((t) => (
              <div key={t.team_name} className="border border-gray-100 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm">{t.team_name}</span>
                  <Badge variant="info">{t.win_prob.toFixed(1)}% Win</Badge>
                </div>
                <StageProgressBar
                  stages={[
                    { label: "R32", prob: t.qualify_r32_prob, color: "#3b82f6" },
                    { label: "R16", prob: t.r16_prob, color: "#22c55e" },
                    { label: "QF", prob: t.qf_prob, color: "#f59e0b" },
                    { label: "SF", prob: t.sf_prob, color: "#f97316" },
                    { label: "F", prob: t.final_prob, color: "#ef4444" },
                    { label: "W", prob: t.win_prob, color: "#8b5cf6" },
                  ]}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
