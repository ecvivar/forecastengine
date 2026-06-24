"use client";

import { useEffect, useState } from "react";
import { api, type WinnerProb, type TeamStageProb } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { Trophy, Shield, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function OverviewPage() {
  const [championProbs, setChampionProbs] = useState<WinnerProb[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard.get()
      .then((d) => setChampionProbs(d.winner_probs))
      .catch((err) => {
        console.error(err);
        setError("Unable to load tournament overview.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  const top15 = championProbs.slice(0, 15);
  const chartData = top15.map((w) => ({
    name: w.team_name,
    Champion: w.win_prob,
    Final: w.final_prob,
    Semifinal: w.sf_prob,
  }));

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Tournament</div>
        <h1 className="page-title">Tournament Overview</h1>
        <p className="page-subtitle">Champion, finalist, semifinal, and quarterfinal probabilities across all 48 teams.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Trophy className="w-4 h-4 text-yellow-500" />
            Stage Probability Comparison — Top 15
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 80, right: 20 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
                />
                <Bar dataKey="Semifinal" fill="#93c5fd" stackId="a" />
                <Bar dataKey="Final" fill="#60a5fa" stackId="a" />
                <Bar dataKey="Champion" fill="#2563eb" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-500" />
              Champion Ranking
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {top15.map((w, i) => (
                <div key={w.team_name} className="flex items-center gap-3 py-1.5 border-b border-[hsl(var(--border))] last:border-0">
                  <span className="text-xs font-bold text-[hsl(var(--muted))] w-5">{i + 1}</span>
                  <Badge variant={i < 3 ? "info" : "default"} className="w-8 text-center">{w.fifa_code || "?"}</Badge>
                  <span className="text-sm flex-1 truncate">{w.team_name}</span>
                  <div className="w-20 bg-gray-100 rounded-full h-1.5">
                    <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${w.win_prob}%` }} />
                  </div>
                  <span className="text-xs font-mono font-bold w-12 text-right">{w.win_prob.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Shield className="w-4 h-4 text-purple-500" />
              Final & Semifinal Probabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {top15.map((w) => (
                <div key={w.team_name} className="flex items-center gap-3 py-1.5 border-b border-[hsl(var(--border))] last:border-0 text-sm">
                  <span className="flex-1 truncate">{w.team_name}</span>
                  <span className="text-xs text-[hsl(var(--muted))] w-16 text-right">
                    F: <span className="font-mono font-medium">{w.final_prob.toFixed(1)}%</span>
                  </span>
                  <span className="text-xs text-[hsl(var(--muted))] w-16 text-right">
                    SF: <span className="font-mono font-medium">{w.sf_prob.toFixed(1)}%</span>
                  </span>
                  <span className="text-xs text-[hsl(var(--muted))] w-16 text-right">
                    QF: <span className="font-mono font-medium">{w.qf_prob.toFixed(1)}%</span>
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
