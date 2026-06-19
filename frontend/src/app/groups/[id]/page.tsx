"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import {
  api,
  getApiErrorMessage,
  type GroupDetail,
  type SimulationProbabilities,
  type TeamStageProb,
} from "@/lib/api";
import StageProgressBar from "@/components/StageProgressBar";
import { AlertTriangle, RefreshCw, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function GroupDetailPage() {
  const params = useParams();
  const groupName = params.id as string;

  const [group, setGroup] = useState<GroupDetail | null>(null);
  const [probs, setProbs] = useState<SimulationProbabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.groups.get(groupName),
      api.simulations.list().then((sims) => {
        const completed = sims.find((s) => s.status === "completed");
        return completed ? api.simulations.probabilities(completed.id) : null;
      }),
    ])
      .then(([g, simProbs]) => {
        if (!g) {
          setError("Group not found");
          return;
        }
        setGroup(g);
        setProbs(simProbs);
      })
      .catch((err) => {
        setGroup(null);
        setError(getApiErrorMessage(err));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [groupName]);

  if (loading) return <SkeletonPage />;

  if (error) {
    return (
      <div className="container-page flex items-center justify-center min-h-[60vh]">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Failed to load group details</h2>
            <p className="text-sm text-gray-500 mb-2">{error}</p>
            <p className="text-sm text-gray-400 mb-6">Group: {groupName}</p>
            <button
              onClick={load}
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

  if (!group) {
    return (
      <div className="container-page flex items-center justify-center min-h-[60vh]">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Group not found</h2>
            <p className="text-sm text-gray-500 mb-6">
              Group &quot;{groupName}&quot; does not exist.
            </p>
            <Link
              href="/groups"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              ← Back to Groups
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const groupProbs = probs?.groups[groupName.toUpperCase()] || [];

  const getTeamProbs = (teamName: string): TeamStageProb | undefined => {
    return probs?.teams.find(
      (t) => t.team_name.toUpperCase() === teamName.toUpperCase()
    );
  };

  return (
    <div className="container-page space-y-6">
      <Link
        href="/groups"
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Groups
      </Link>

      <h1 className="page-title">Group {group.name}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Standings */}
        <Card>
          <CardHeader>
            <CardTitle>Standings</CardTitle>
          </CardHeader>
          <CardContent>
            {Array.isArray(group.standings) && group.standings.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500 text-xs uppercase">
                    <th className="text-left py-2 w-8">#</th>
                    <th className="text-left py-2">Team</th>
                    <th className="text-center py-2">Pld</th>
                    <th className="text-center py-2">W</th>
                    <th className="text-center py-2">D</th>
                    <th className="text-center py-2">L</th>
                    <th className="text-center py-2">GF</th>
                    <th className="text-center py-2">GA</th>
                    <th className="text-center py-2">GD</th>
                    <th className="text-center py-2 font-bold">Pts</th>
                  </tr>
                </thead>
                <tbody>
                  {[...group.standings]
                    .sort((a, b) => a.position - b.position)
                    .map((s) => (
                    <tr
                      key={s.id}
                      className="border-b border-gray-50 hover:bg-gray-50"
                    >
                      <td className="py-2">
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                            s.position <= 2 ? "bg-green-500" : "bg-gray-300"
                          }`}
                        >
                          {s.position}
                        </span>
                      </td>
                      <td className="py-2 font-medium flex items-center gap-2">
                        {s.team_name}
                        {s.qualified && (
                          <Badge variant="success" className="text-[10px]">
                            Q
                          </Badge>
                        )}
                      </td>
                      <td className="text-center py-2">{s.played}</td>
                      <td className="text-center py-2 text-green-600">{s.won}</td>
                      <td className="text-center py-2 text-gray-500">{s.drawn}</td>
                      <td className="text-center py-2 text-red-500">{s.lost}</td>
                      <td className="text-center py-2">{s.goals_for}</td>
                      <td className="text-center py-2">{s.goals_against}</td>
                      <td className="text-center py-2 font-medium">
                        {s.goal_difference > 0 ? "+" : ""}
                        {s.goal_difference}
                      </td>
                      <td className="text-center py-2 font-bold text-primary-700">
                        {s.points}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-gray-400 italic py-4 text-center">
                No standings data available for this group.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Qualification Probabilities */}
        <Card>
          <CardHeader>
            <CardTitle>Qualification Probabilities</CardTitle>
          </CardHeader>
          <CardContent>
            {groupProbs.length > 0 ? (
              <div className="space-y-4">
                {groupProbs.map((gp) => {
                  const tp = getTeamProbs(gp.team_name);
                  const stage = tp
                    ? [
                        { label: "R32", prob: tp.qualify_r32_prob, color: "#3b82f6" },
                        { label: "R16", prob: tp.r16_prob, color: "#22c55e" },
                        { label: "QF", prob: tp.qf_prob, color: "#f59e0b" },
                        { label: "SF", prob: tp.sf_prob, color: "#f97316" },
                        { label: "Final", prob: tp.final_prob, color: "#ef4444" },
                        { label: "Win", prob: tp.win_prob, color: "#8b5cf6" },
                      ]
                    : [];
                  return (
                    <div
                      key={gp.team_name}
                      className="border border-gray-100 rounded-lg p-3"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{gp.team_name}</span>
                        <span className="font-bold text-green-600">
                          {gp.qualify_r32_prob.toFixed(1)}% R32
                        </span>
                      </div>
                      <StageProgressBar stages={stage} />
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-sm text-gray-400 italic py-4 text-center">
                No simulation data available. Run a simulation to see qualification probabilities.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
