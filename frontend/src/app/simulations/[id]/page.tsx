"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type SimulationDetail, type SimulationResult } from "@/lib/api";
import { formatDateTime, formatPercent, getWinColor } from "@/lib/utils";
import StageProgressBar from "@/components/StageProgressBar";
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

  if (loading) {
    return (
      <div className="container-page">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      </div>
    );
  }

  if (error || !sim) {
    return (
      <div className="container-page text-center py-12">
        <p className="text-red-500">Simulation not found.</p>
        <Link href="/simulations" className="text-primary-600 hover:underline mt-4 inline-block">
          ← All Simulations
        </Link>
      </div>
    );
  }

  const n = Math.max(sim.num_simulations, 1);
  const results = [...(sim.results || [])].sort(
    (a, b) => b.won_tournament - a.won_tournament
  );

  const top3 = results.slice(0, 3);

  return (
    <div className="container-page space-y-6">
      <Link
        href="/simulations"
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Simulations
      </Link>

      {/* Header */}
      <Card>
        <CardContent className="p-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{sim.name || "Simulation"}</h1>
            <p className="text-sm text-gray-500">
              {sim.num_simulations.toLocaleString()} runs | Status:{" "}
              <Badge
                variant={
                  sim.status === "completed"
                    ? "success"
                    : sim.status === "running"
                      ? "warning"
                      : "default"
                }
              >
                {sim.status}
              </Badge>
              {sim.completed_at && (
                <span className="ml-2">
                  Completed: {formatDateTime(sim.completed_at)}
                </span>
              )}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Top 3 Podium */}
      {sim.status === "completed" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {top3.map((r, i) => (
            <Card
              key={r.id}
              className={`text-center ${
                i === 0
                  ? "border-2 border-yellow-400"
                  : i === 1
                    ? "border-2 border-gray-300"
                    : "border-2 border-orange-300"
              }`}
            >
              <CardContent className="p-6">
                {i === 0 && <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-2" />}
                <h3 className="text-lg font-bold">{r.team_name}</h3>
                <div className="text-3xl font-bold text-primary-600 mt-2">
                  {((r.won_tournament / n) * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">Win Probability</div>
                <div className="flex justify-center gap-3 mt-3 text-xs text-gray-400">
                  <span>F: {((r.reached_final / n) * 100).toFixed(1)}%</span>
                  <span>SF: {((r.reached_semi_final / n) * 100).toFixed(1)}%</span>
                  <span>QF: {((r.reached_quarter_final / n) * 100).toFixed(1)}%</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Results Table */}
      {sim.status === "completed" && (
        <Card>
          <CardHeader>
            <CardTitle>All Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500 text-xs uppercase">
                    <th className="text-left py-2">Rank</th>
                    <th className="text-left py-2">Team</th>
                    <th className="text-center py-2">Group</th>
                    <th className="text-center py-2">R32</th>
                    <th className="text-center py-2">R16</th>
                    <th className="text-center py-2">QF</th>
                    <th className="text-center py-2">SF</th>
                    <th className="text-center py-2">Final</th>
                    <th className="text-center py-2 font-bold">Champion</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr
                      key={r.id}
                      className="border-b border-gray-50 hover:bg-gray-50"
                    >
                      <td className="py-2">{i + 1}</td>
                      <td className="py-2 font-medium">{r.team_name}</td>
                      <td className="text-center py-2 text-gray-400">
                        {r.group_name || "?"}
                      </td>
                      <td className="text-center py-2">
                        {((r.reached_round_of_32 / n) * 100).toFixed(1)}%
                      </td>
                      <td className="text-center py-2">
                        {((r.reached_round_of_16 / n) * 100).toFixed(1)}%
                      </td>
                      <td className="text-center py-2">
                        {((r.reached_quarter_final / n) * 100).toFixed(1)}%
                      </td>
                      <td className="text-center py-2">
                        {((r.reached_semi_final / n) * 100).toFixed(1)}%
                      </td>
                      <td className="text-center py-2">
                        {((r.reached_final / n) * 100).toFixed(1)}%
                      </td>
                      <td className="text-center py-2 font-bold text-yellow-600">
                        {((r.won_tournament / n) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {sim.status !== "completed" && (
        <Card>
          <CardContent className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
            <p className="text-gray-500">
              Simulation is {sim.status}. Results will appear when complete.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
