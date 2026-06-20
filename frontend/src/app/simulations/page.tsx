"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { api, getApiErrorMessage, type Simulation, type SimulationDetail } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { Play, Loader2, Trophy, BarChart4, AlertTriangle, RefreshCw } from "lucide-react";

export default function SimulationsPage() {
  const [sims, setSims] = useState<Simulation[]>([]);
  const [details, setDetails] = useState<Record<string, SimulationDetail>>({});
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSims = () => {
    setLoading(true);
    setError(null);
    api.simulations
      .list()
      .then(async (list) => {
        setSims(list);
        const d: Record<string, SimulationDetail> = {};
        await Promise.all(
          list.map(async (s) => {
            try {
              const sd = await api.simulations.get(s.id);
              d[s.id] = sd;
            } catch {
              // ignore load errors per-sim
            }
          })
        );
        setDetails(d);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSims();
  }, []);

  const runNew = async () => {
    setRunning(true);
    try {
      const comp = await api.competitions.current();
      const created = await api.simulations.create({
        competition_id: comp.id,
        num_simulations: 10000,
      });
      await api.simulations.run(created.id);
      loadSims();
    } catch (e) {
      console.error("Simulation failed:", e);
    }
    setRunning(false);
  };

  if (loading) return <SkeletonPage />;

  if (error) {
    return (
      <div className="container-page flex items-center justify-center min-h-[60vh]">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Failed to load simulations</h2>
            <p className="text-sm text-gray-500 mb-6">{error}</p>
            <button
              onClick={loadSims}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Try again
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getTopChampion = (simId: string): { name: string; prob: number } | null => {
    const d = details[simId];
    if (!d?.results?.length) return null;
    const top = [...d.results].sort((a, b) => b.won_tournament - a.won_tournament)[0];
    const n = Math.max(d.num_simulations, 1);
    return { name: top.team_name, prob: (top.won_tournament / n) * 100 };
  };

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Monte Carlo Simulations</h1>
          <p className="page-subtitle">
            Run 10,000+ tournament simulations to compute knockout probabilities
          </p>
        </div>
        <button
          onClick={runNew}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {running ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {running ? "Running..." : "New Simulation"}
        </button>
      </div>

      {sims.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <BarChart4 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">
              No simulations yet. Run your first Monte Carlo simulation to see results.
            </p>
            <button
              onClick={runNew}
              disabled={running}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {running ? "Running..." : "Run First Simulation"}
            </button>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {sims.map((sim) => {
          const top = getTopChampion(sim.id);
          return (
            <Link key={sim.id} href={`/simulations/${sim.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold">
                        {sim.name || "Unnamed Simulation"}
                      </h3>
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
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {sim.num_simulations.toLocaleString()} runs
                      {sim.completed_at &&
                        ` | Completed: ${formatDateTime(sim.completed_at)}`}
                    </p>
                  </div>
                  {top && sim.status === "completed" && (
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <Trophy className="w-4 h-4 text-yellow-500" />
                        <span className="font-semibold">{top.name}</span>
                      </div>
                      <span className="text-sm text-yellow-600 font-bold">
                        {top.prob.toFixed(1)}% champion
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
