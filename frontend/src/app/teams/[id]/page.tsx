"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { api, type IGFScore, type SimulationProbabilities, type TeamStageProb } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";
import { BarChart, Bar, XAxis, YAxis, Cell } from "recharts";
import { Shield, BarChart3, Activity, TrendingUp } from "lucide-react";

const COLORS = ["#3b82f6", "#22c55e", "#eab308", "#ef4444", "#a855f7"];

export default function TeamDetailPage() {
  const params = useParams();
  const teamId = params.id as string;

  const [team, setTeam] = useState<any>(null);
  const [igf, setIgf] = useState<IGFScore | null>(null);
  const [simProbs, setSimProbs] = useState<TeamStageProb | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!teamId) return;
    Promise.all([
      api.teams.get(teamId),
      api.rankings.igf().catch(() => [] as IGFScore[]),
      api.simulations.list().then((sims) => {
        if (sims.length > 0) {
          return api.simulations.probabilities(sims[0].id).catch(() => null);
        }
        return null;
      }).catch(() => null),
    ]).then(([t, igfList, sim]) => {
      setTeam(t);
      const match = igfList.find((s) => s.team_name === t.name);
      setIgf(match || null);
      if (sim) {
        const tp = sim.teams.find((s: TeamStageProb) => s.team_name === t.name);
        setSimProbs(tp || null);
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, [teamId]);

  const radarData = useMemo(() => {
    if (!igf?.components) return [];
    return Object.entries(igf.components).map(([key, value]) => ({
      metric: key.replace(/_/g, " "),
      value: Math.min(100, (value as number) * 100),
    }));
  }, [igf]);

  if (loading) return <SkeletonPage />;
  if (!team) return <div className="container-page"><p className="text-[hsl(var(--muted))]">Team not found.</p></div>;

  const probs = simProbs;
  const probChart = probs ? [
    { label: "R16", prob: probs.r16_prob },
    { label: "QF", prob: probs.qf_prob },
    { label: "SF", prob: probs.sf_prob },
    { label: "Final", prob: probs.final_prob },
    { label: "Win", prob: probs.win_prob },
  ] : [];

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary-100 text-xl font-bold text-primary-700">
          {team.fifa_code || team.name.slice(0, 2).toUpperCase()}
        </div>
        <div>
          <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider">Team Intelligence</div>
          <h1 className="page-title">{team.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge>{team.continent || "Unknown"}</Badge>
            <span className="text-xs text-[hsl(var(--muted))]">FIFA: {team.fifa_code || "—"}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Shield className="w-4 h-4 text-blue-500" />
              Strength Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {radarData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                    <Radar dataKey="value" fill="#3b82f6" fillOpacity={0.3} stroke="#3b82f6" />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-sm text-[hsl(var(--muted))] italic text-center pt-16">No IGF data available.</div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Stage Probabilities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-500" />
              Stage Probabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              {probChart.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={probChart} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                    <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                    <Bar dataKey="prob" radius={[4, 4, 0, 0]}>
                      {probChart.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-sm text-[hsl(var(--muted))] italic text-center pt-16">No simulation data.</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "IGF Score", value: igf?.igf_score?.toFixed(1) || "—", icon: BarChart3 },
          { label: "Elo Rating", value: team.elo_score?.toString() || "1500", icon: Activity },
          { label: "FIFA Rank", value: team.fifa_rank?.toString() || "—", icon: Shield },
          { label: "Group", value: simProbs?.group_name || "—", icon: TrendingUp },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <s.icon className="w-5 h-5 text-[hsl(var(--muted))]" />
              <div>
                <div className="stat-value text-base">{s.value}</div>
                <div className="stat-label text-xs">{s.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {igf?.components && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">IGF Component Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {Object.entries(igf.components).map(([key, value]) => (
                <div key={key} className="panel p-3">
                  <div className="text-xs text-[hsl(var(--muted))] mb-1 truncate">{key.replace(/_/g, " ")}</div>
                  <div className="text-lg font-bold font-mono">{(value as number * 100).toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
