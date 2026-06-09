"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { api, type SimulationDetail, type SimulationResult } from "@/lib/api";
import { formatDateTime, formatPercent, getWinColor } from "@/lib/utils";
import SortableTable, { type Column } from "@/components/SortableTable";
import StageProgressBar from "@/components/StageProgressBar";
import DistributionHistogram from "@/components/DistributionHistogram";
import { ArrowLeft, Loader2, Trophy } from "lucide-react";
import Link from "next/link";

export default function SimulationDetailPage() {
  const params = useParams();
  const simId = params.id as string;

  const [sim, setSim] = useState<SimulationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!simId) return;
    api.simulations
      .get(simId)
      .then(setSim)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [simId]);

  if (loading) return <SkeletonPage />;

  if (error || !sim) {
    return (
      <div className="container-page text-center py-12">
        <p className="text-red-500">Simulation not found.</p>
        <Link href="/simulations" className="text-primary-600 hover:underline mt-4 inline-block">← All Simulations</Link>
      </div>
    );
  }

  const n = Math.max(sim.num_simulations, 1);
  const results = [...(sim.results || [])].sort((a, b) => b.won_tournament - a.won_tournament);
  const top3 = results.slice(0, 3);

  const columns: Column<SimulationResult>[] = [
    {
      key: "rank",
      label: "#",
      sortable: false,
      render: (_r, i) => <span>{(i ?? 0) + 1}</span>,
    },
    { key: "team_name", label: "Team", render: (r) => <span className="font-medium">{r.team_name}</span> },
    { key: "group_name", label: "Group", align: "center", render: (r) => <span className="text-gray-400">{r.group_name || "?"}</span> },
    {
      key: "reached_round_of_32",
      label: "R32",
      align: "center",
      render: (r) => <span className={getWinColor((r.reached_round_of_32 / n) * 100)}>{((r.reached_round_of_32 / n) * 100).toFixed(1)}%</span>,
      sortValue: (r) => r.reached_round_of_32,
    },
    {
      key: "reached_round_of_16",
      label: "R16",
      align: "center",
      render: (r) => <span className={getWinColor((r.reached_round_of_16 / n) * 100)}>{((r.reached_round_of_16 / n) * 100).toFixed(1)}%</span>,
      sortValue: (r) => r.reached_round_of_16,
    },
    {
      key: "reached_quarter_final",
      label: "QF",
      align: "center",
      render: (r) => <span className={getWinColor((r.reached_quarter_final / n) * 100)}>{((r.reached_quarter_final / n) * 100).toFixed(1)}%</span>,
      sortValue: (r) => r.reached_quarter_final,
    },
    {
      key: "reached_semi_final",
      label: "SF",
      align: "center",
      render: (r) => <span className={getWinColor((r.reached_semi_final / n) * 100)}>{((r.reached_semi_final / n) * 100).toFixed(1)}%</span>,
      sortValue: (r) => r.reached_semi_final,
    },
    {
      key: "reached_final",
      label: "Final",
      align: "center",
      render: (r) => <span className={getWinColor((r.reached_final / n) * 100)}>{((r.reached_final / n) * 100).toFixed(1)}%</span>,
      sortValue: (r) => r.reached_final,
    },
    {
      key: "won_tournament",
      label: "Champion",
      align: "center",
      render: (r) => <span className="font-bold text-yellow-600">{((r.won_tournament / n) * 100).toFixed(1)}%</span>,
      sortValue: (r) => r.won_tournament,
    },
  ];

  return (
    <div className="container-page space-y-6">
      <Link href="/simulations" className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600">
        <ArrowLeft className="w-4 h-4" /> Back to Simulations
      </Link>

      <Card>
        <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{sim.name || "Simulation"}</h1>
            <p className="text-sm text-gray-500">
              {sim.num_simulations.toLocaleString()} runs | Status:{" "}
              <Badge variant={sim.status === "completed" ? "success" : sim.status === "running" ? "warning" : "default"}>
                {sim.status}
              </Badge>
              {sim.completed_at && <span className="ml-2">Completed: {formatDateTime(sim.completed_at)}</span>}
            </p>
          </div>
        </CardContent>
      </Card>

      {sim.status === "completed" && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {top3.map((r, i) => (
              <Card key={r.id} className={`text-center ${i === 0 ? "border-2 border-yellow-400" : i === 1 ? "border-2 border-gray-300" : "border-2 border-orange-300"}`}>
                <CardContent className="p-6">
                  {i === 0 && <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-2" />}
                  <h3 className="text-lg font-bold">{r.team_name}</h3>
                  <div className="text-3xl font-bold text-primary-600 mt-2">{((r.won_tournament / n) * 100).toFixed(1)}%</div>
                  <div className="text-sm text-gray-500">Win Probability</div>
                  <div className="flex justify-center gap-3 mt-3 text-xs text-gray-400 flex-wrap">
                    <span>F: {((r.reached_final / n) * 100).toFixed(1)}%</span>
                    <span>SF: {((r.reached_semi_final / n) * 100).toFixed(1)}%</span>
                    <span>QF: {((r.reached_quarter_final / n) * 100).toFixed(1)}%</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Champion Probability Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DistributionHistogram results={results} numSimulations={sim.num_simulations} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>All Results</CardTitle>
            </CardHeader>
            <CardContent>
              <SortableTable columns={columns} data={results} defaultSort={{ key: "won_tournament", dir: "desc" }} />
            </CardContent>
          </Card>
        </>
      )}

      {sim.status !== "completed" && (
        <Card>
          <CardContent className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
            <p className="text-gray-500">Simulation is {sim.status}. Results will appear when complete.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
