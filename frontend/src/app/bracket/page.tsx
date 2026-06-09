"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type SimulationProbabilities } from "@/lib/api";
import Bracket from "@/components/Bracket";
import { Trophy, Swords } from "lucide-react";
import Link from "next/link";

export default function BracketPage() {
  const [data, setData] = useState<SimulationProbabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.simulations
      .list()
      .then((sims) => {
        const completed = sims.find((s) => s.status === "completed");
        if (!completed) {
          setError("No completed simulations found");
          return null;
        }
        return api.simulations.probabilities(completed.id);
      })
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="container-page">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container-page text-center py-12">
        <Swords className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">No Bracket Data</h2>
        <p className="text-gray-500 mb-4">
          {error || "No simulation data available. Run a simulation first."}
        </p>
        <Link
          href="/simulations"
          className="text-primary-600 hover:underline"
        >
          Go to Simulations →
        </Link>
      </div>
    );
  }

  // Build bracket rounds from simulation probabilities
  const sortedTeams = [...data.teams]
    .sort((a, b) => b.win_prob - a.win_prob)
    .slice(0, 32);

  const round32: { top: { name: string; prob?: number; isWinner?: boolean }; bottom: { name: string; prob?: number; isWinner?: boolean } }[] = [];
  for (let i = 0; i < sortedTeams.length; i += 2) {
    if (i + 1 < sortedTeams.length) {
      round32.push({
        top: { name: sortedTeams[i].team_name, prob: sortedTeams[i].qualify_r32_prob },
        bottom: { name: sortedTeams[i + 1].team_name, prob: sortedTeams[i + 1].qualify_r32_prob },
      });
    }
  }

  const round16: { top: { name: string; prob?: number; isWinner?: boolean }; bottom: { name: string; prob?: number; isWinner?: boolean } }[] = [];
  for (let i = 0; i < sortedTeams.length; i += 4) {
    if (i + 3 < sortedTeams.length) {
      round16.push({
        top: { name: sortedTeams[i].team_name, prob: sortedTeams[i].r16_prob },
        bottom: { name: sortedTeams[i + 3].team_name, prob: sortedTeams[i + 3].r16_prob },
      });
    }
  }

  const rounds = [
    { name: "round_of_32", matches: round32.slice(0, 16) },
    { name: "round_of_16", matches: round16.slice(0, 8) },
    {
      name: "quarter_final",
      matches: sortedTeams.slice(0, 8).map((t, i) => ({
        top: { name: t.team_name, prob: t.qf_prob } as const,
        bottom: { name: sortedTeams[7 - i]?.team_name || "?", prob: sortedTeams[7 - i]?.qf_prob } as const,
      })),
    },
    {
      name: "semi_final",
      matches: sortedTeams.slice(0, 4).map((t, i) => ({
        top: { name: t.team_name, prob: t.sf_prob } as const,
        bottom: { name: sortedTeams[3 - i]?.team_name || "?", prob: sortedTeams[3 - i]?.sf_prob } as const,
      })),
    },
    {
      name: "final",
      matches: [
        {
          top: { name: sortedTeams[0]?.team_name || "?", prob: sortedTeams[0]?.win_prob, isWinner: true } as const,
          bottom: { name: sortedTeams[1]?.team_name || "?", prob: sortedTeams[1]?.win_prob } as const,
        },
      ],
    },
  ];

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">
            <Trophy className="w-6 h-6 inline mr-2 text-yellow-500" />
            Tournament Bracket
          </h1>
          <p className="page-subtitle">
            Projected bracket based on {data.num_simulations.toLocaleString()} simulations
          </p>
        </div>
        <Badge variant="info" className="text-sm px-3 py-1">
          {data.num_simulations.toLocaleString()} sims
        </Badge>
      </div>

      <Card>
        <CardContent className="p-6">
          <Bracket rounds={rounds} />
        </CardContent>
      </Card>

      {/* Champion Prediction */}
      <Card>
        <CardHeader>
          <CardTitle>🏆 Projected Champion: {sortedTeams[0]?.team_name || "?"}</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-3xl font-bold text-yellow-600">
              {sortedTeams[0]?.win_prob.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Win Probability</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-blue-600">
              {sortedTeams[0]?.final_prob.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Final Probability</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-3xl font-bold text-orange-600">
              {sortedTeams[0]?.sf_prob.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Semi-Final Probability</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {sortedTeams[0]?.qf_prob.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">Quarter-Final Probability</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-600">
              {sortedTeams[0]?.qualify_r32_prob.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">R32 Probability</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
