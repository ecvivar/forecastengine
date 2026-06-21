"use client";

import { useEffect, useState, useMemo } from "react";
import { api, Team, IGFScore, PowerRanking, PowerRankingTeam } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import TeamRadarChart from "@/components/TeamRadarChart";
import { getContinentColor } from "@/lib/utils";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";
import { ArrowRightLeft, Shield, TrendingUp, BarChart3 } from "lucide-react";

export default function ComparePage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [igfScores, setIgfScores] = useState<IGFScore[]>([]);
  const [powerRanking, setPowerRanking] = useState<PowerRanking | null>(null);
  const [loading, setLoading] = useState(true);
  const [teamA, setTeamA] = useState<string>("");
  const [teamB, setTeamB] = useState<string>("");

  useEffect(() => {
    Promise.all([
      api.teams.list(1, 100),
      api.rankings.igf().catch(() => [] as IGFScore[]),
      api.rankings.powerRanking().catch(() => null),
    ])
      .then(([t, igf, pr]) => {
        setTeams(t);
        setIgfScores(igf);
        setPowerRanking(pr);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const igfMap = useMemo(() => new Map(igfScores.map((s) => [s.team_name, s])), [igfScores]);
  const teamMap = useMemo(() => new Map(teams.map((t) => [t.name, t])), [teams]);

  const teamNames = useMemo(() => teams.map((t) => t.name).sort(), [teams]);

  const componentsA = useMemo(() => {
    if (!teamA) return {};
    return igfMap.get(teamA)?.components || {};
  }, [teamA, igfMap]);

  const componentsB = useMemo(() => {
    if (!teamB) return {};
    return igfMap.get(teamB)?.components || {};
  }, [teamB, igfMap]);

  const radarComparison = useMemo(() => {
    const keys = new Set([...Object.keys(componentsA), ...Object.keys(componentsB)]);
    return Array.from(keys).map((key) => ({
      component: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      [teamA || "Team A"]: (componentsA[key] || 0) * 100,
      [teamB || "Team B"]: (componentsB[key] || 0) * 100,
    }));
  }, [componentsA, componentsB, teamA, teamB]);

  const igfA = teamA ? igfMap.get(teamA) : null;
  const igfB = teamB ? igfMap.get(teamB) : null;

  if (loading) return <SkeletonPage />;

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Analysis</div>
        <h1 className="page-title">Team Comparison</h1>
        <p className="page-subtitle">Compare IGF profiles, stage probabilities, and attributes side by side.</p>
      </div>

      <div className="flex items-end gap-4">
        <div className="flex-1">
          <label className="text-xs text-[hsl(var(--muted))] mb-1 block">Team A</label>
          <select
            value={teamA}
            onChange={(e) => setTeamA(e.target.value)}
            className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg text-sm bg-transparent"
          >
            <option value="">Select team...</option>
            {teamNames.filter((n) => n !== teamB).map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
        <div className="pb-2">
          <ArrowRightLeft className="w-5 h-5 text-[hsl(var(--muted))]" />
        </div>
        <div className="flex-1">
          <label className="text-xs text-[hsl(var(--muted))] mb-1 block">Team B</label>
          <select
            value={teamB}
            onChange={(e) => setTeamB(e.target.value)}
            className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg text-sm bg-transparent"
          >
            <option value="">Select team...</option>
            {teamNames.filter((n) => n !== teamA).map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {teamA && teamB && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BarChart3 className="w-4 h-4 text-blue-500" />
                  IGF Profile — {teamA}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TeamRadarChart teamName={teamA} components={componentsA} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BarChart3 className="w-4 h-4 text-green-500" />
                  IGF Profile — {teamB}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TeamRadarChart teamName={teamB} components={componentsB} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Shield className="w-4 h-4 text-purple-500" />
                Direct Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarComparison}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="component" tick={{ fontSize: 10 }} />
                    <Radar dataKey={teamA} fill="#3b82f6" fillOpacity={0.2} stroke="#3b82f6" strokeWidth={2} />
                    <Radar dataKey={teamB} fill="#22c55e" fillOpacity={0.2} stroke="#22c55e" strokeWidth={2} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "IGF Score", a: igfA?.igf_score?.toFixed(1) || "—", b: igfB?.igf_score?.toFixed(1) || "—" },
              { label: "Elo Rating", a: teamMap.get(teamA)?.fifa_code || "—", b: teamMap.get(teamB)?.fifa_code || "—" },
              { label: "Continent", a: teamMap.get(teamA)?.continent || "—", b: teamMap.get(teamB)?.continent || "—" },
            ].map((s) => (
              <Card key={s.label}>
                <CardContent className="p-3 flex items-center justify-between text-sm">
                  <span className="text-[hsl(var(--muted))]">{s.label}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-blue-600">{s.a}</span>
                    <span className="text-[hsl(var(--muted))] text-xs">vs</span>
                    <span className="font-medium text-green-600">{s.b}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {(!teamA || !teamB) && (
        <Card>
          <CardContent className="p-8 text-center text-[hsl(var(--muted))]">
            <ArrowRightLeft className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Select two teams above to compare their IGF profiles.</p>
          </CardContent>
        </Card>
      )}

      {powerRanking && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-green-500" />
              Power Ranking Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Title Contenders", teams: powerRanking.title_contenders.length },
                { label: "SF Candidates", teams: powerRanking.semi_final_candidates.length },
                { label: "QF Candidates", teams: powerRanking.quarter_final_candidates.length },
                { label: "Early Exit", teams: powerRanking.early_exit_candidates.length },
              ].map((c) => (
                <div key={c.label} className="panel p-3 text-center">
                  <div className="text-2xl font-bold font-mono text-primary-600">{c.teams}</div>
                  <div className="text-xs text-[hsl(var(--muted))]">{c.label}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
