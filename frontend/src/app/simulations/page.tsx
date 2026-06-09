"use client";

import { useEffect, useState } from "react";
import { api, SimulationDetail, SimulationResult } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatProbability } from "@/lib/utils";

export default function SimulationsPage() {
  const [sims, setSims] = useState<SimulationDetail[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSims = () => {
    setLoading(true);
    api.simulations.list().then(async (list) => {
      const details = await Promise.all(
        list.map((s) => api.simulations.get(s.id).catch(() => null))
      );
      setSims(details.filter(Boolean) as SimulationDetail[]);
    }).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { loadSims(); }, []);

  const runNew = async () => {
    try {
      const sim = await api.simulations.create({
        competition_id: "00000000-0000-0000-0000-000000000000",
        num_simulations: 10000,
      });
      await api.simulations.run(sim.id);
      loadSims();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="container-page">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="page-title">Simulations</h1>
          <p className="page-subtitle">
            Monte Carlo tournament results. Run 100k+ simulations to estimate probabilities.
          </p>
        </div>
        <Button onClick={runNew}>New Simulation</Button>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading simulations...</p>
      ) : sims.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">No simulations yet.</p>
            <Button onClick={runNew} className="mt-4">Run First Simulation</Button>
          </CardContent>
        </Card>
      ) : (
        sims.map((sim) => (
          <Card key={sim.id} className="mb-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{sim.name || "Simulation"}</CardTitle>
                <Badge variant={sim.status === "completed" ? "success" : "default"}>
                  {sim.status}
                </Badge>
              </div>
              <p className="text-sm text-gray-500">
                {sim.num_simulations.toLocaleString()} runs
                {sim.completed_at && <> &middot; Completed {new Date(sim.completed_at).toLocaleDateString()}</>}
              </p>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left">
                    <th className="px-4 py-2 font-medium text-gray-500">Team</th>
                    <th className="px-4 py-2 font-medium text-gray-500">R16</th>
                    <th className="px-4 py-2 font-medium text-gray-500">QF</th>
                    <th className="px-4 py-2 font-medium text-gray-500">SF</th>
                    <th className="px-4 py-2 font-medium text-gray-500">Final</th>
                    <th className="px-4 py-2 font-medium text-gray-500">Winner</th>
                  </tr>
                </thead>
                <tbody>
                  {sim.results
                    .sort((a, b) => b.won_tournament - a.won_tournament)
                    .slice(0, 20)
                    .map((r) => (
                      <tr key={r.id} className="border-b last:border-0 hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium">{r.team_name}</td>
                        <td className="px-4 py-2 font-mono">{r.reached_round_of_16}</td>
                        <td className="px-4 py-2 font-mono">{r.reached_quarter_final}</td>
                        <td className="px-4 py-2 font-mono">{r.reached_semi_final}</td>
                        <td className="px-4 py-2 font-mono">{r.reached_final}</td>
                        <td className="px-4 py-2">
                          <span className="font-bold text-primary-600">
                            {formatProbability(r.won_tournament / sim.num_simulations)}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
