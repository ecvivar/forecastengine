"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { api, type PowerRanking, type PowerRankingTeam, type IGFScore } from "@/lib/api";
import { getContinentColor } from "@/lib/utils";
import SortableTable, { type Column } from "@/components/SortableTable";
import TeamRadarChart from "@/components/TeamRadarChart";
import Link from "next/link";
import { TrendingUp, BarChart3, Radar } from "lucide-react";

type Tab = "igf" | "power" | "radar";

export default function RankingsPage() {
  const [tab, setTab] = useState<Tab>("igf");
  const [scores, setScores] = useState<IGFScore[]>([]);
  const [power, setPower] = useState<PowerRanking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [radarTeam, setRadarTeam] = useState<string>("");

  useEffect(() => {
    Promise.all([
      api.rankings.igf(),
      api.rankings.powerRanking().catch(() => null),
    ])
      .then(([igf, pr]) => {
        setScores(igf);
        setPower(pr);
        if (igf.length > 0) setRadarTeam(igf[0].team_name);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load rankings data.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  const sorted = [...scores].sort((a, b) => b.igf_score - a.igf_score);
  const radarData = scores.find((s) => s.team_name === radarTeam);

  const igfColumns: Column<IGFScore>[] = [
    {
      key: "rank",
      label: "#",
      sortable: false,
      render: (_s, i) => (
        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
          i < 3 ? "bg-yellow-500" : i < 8 ? "bg-blue-500" : "bg-gray-300"
        }`}>
          {i + 1}
        </span>
      ),
    },
    {
      key: "team_name",
      label: "Team",
      render: (s) => <span className="font-medium">{s.team_name}</span>,
    },
    {
      key: "igf_score",
      label: "IGF Score",
      align: "center",
      render: (s) => (
        <div className="flex items-center justify-center gap-2">
          <div className="w-16 bg-gray-100 rounded-full h-2">
            <div className="bg-gradient-to-r from-blue-500 to-primary-600 h-2 rounded-full" style={{ width: `${s.igf_score}%` }} />
          </div>
          <span className="font-bold text-primary-700">{s.igf_score.toFixed(1)}</span>
        </div>
      ),
      sortValue: (s) => s.igf_score,
    },
    {
      key: "components.elo",
      label: "Elo",
      align: "center",
      render: (s) => <span>{s.components?.elo?.toFixed(0) || "—"}</span>,
      sortValue: (s) => s.components?.elo || 0,
    },
    {
      key: "components.form",
      label: "Form",
      align: "center",
      render: (s) => <span>{s.components?.form?.toFixed(0) || "—"}</span>,
      sortValue: (s) => s.components?.form || 0,
    },
    {
      key: "components.xg",
      label: "xG",
      align: "center",
      render: (s) => <span>{s.components?.xg?.toFixed(0) || "—"}</span>,
      sortValue: (s) => s.components?.xg || 0,
    },
    {
      key: "components.xga",
      label: "xGA",
      align: "center",
      render: (s) => <span>{s.components?.xga?.toFixed(0) || "—"}</span>,
      sortValue: (s) => s.components?.xga || 0,
    },
    {
      key: "components.squad_quality",
      label: "Squad",
      align: "center",
      render: (s) => <span>{s.components?.squad_quality?.toFixed(0) || "—"}</span>,
      sortValue: (s) => s.components?.squad_quality || 0,
    },
  ];

  const powerColumns: Column<PowerRankingTeam>[] = [
    { key: "rank", label: "Rank", render: (t) => <span>{t.rank}</span> },
    {
      key: "team_name",
      label: "Team",
      render: (t) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{t.team_name}</span>
          <Badge className={getContinentColor(t.continent)}>{t.continent || "?"}</Badge>
        </div>
      ),
    },
    { key: "igf_score", label: "IGF", align: "center", render: (t) => <span className="font-bold">{t.igf_score.toFixed(1)}</span>, sortValue: (t) => t.igf_score },
    { key: "elo_score", label: "Elo", align: "center", render: (t) => <span>{t.elo_score}</span>, sortValue: (t) => t.elo_score },
    { key: "fifa_rank", label: "FIFA Rank", align: "center", render: (t) => <span>#{t.fifa_rank}</span>, sortValue: (t) => t.fifa_rank },
  ];

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Standings</div>
        <h1 className="page-title">Rankings &amp; Power Rankings</h1>
        <p className="page-subtitle">IGF scores, Elo ratings, and tier-based power rankings for all 48 teams.</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[
          { key: "igf" as Tab, label: "IGF Rankings", icon: BarChart3 },
          { key: "power" as Tab, label: "Power Ranking", icon: TrendingUp },
          { key: "radar" as Tab, label: "Radar View", icon: Radar },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-primary-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {tab === "igf" && (
        <Card>
          <CardHeader>
            <CardTitle>IGF (Integrated Global Strength) Index</CardTitle>
          </CardHeader>
          <CardContent>
            <SortableTable columns={igfColumns} data={sorted} defaultSort={{ key: "igf_score", dir: "desc" }} />
          </CardContent>
        </Card>
      )}

      {tab === "radar" && (
        <Card>
          <CardHeader>
            <CardTitle>IGF Component Radar — Compare Teams</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <select
                value={radarTeam}
                onChange={(e) => setRadarTeam(e.target.value)}
                className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {sorted.map((s) => (
                  <option key={s.team_id} value={s.team_name}>{s.team_name}</option>
                ))}
              </select>
            </div>
            {radarData && (
              <TeamRadarChart teamName={radarData.team_name} components={radarData.components} />
            )}
          </CardContent>
        </Card>
      )}

      {tab === "power" && power && (
        <div className="space-y-6">
          {[
            { title: "Title Contenders", teams: power.title_contenders, color: "yellow" },
            { title: "Semi-Final Candidates", teams: power.semi_final_candidates, color: "blue" },
            { title: "Quarter-Final Candidates", teams: power.quarter_final_candidates, color: "green" },
            { title: "Early Exit Candidates", teams: power.early_exit_candidates, color: "red" },
          ].map((section) => (
            <Card key={section.title}>
              <CardHeader>
                <CardTitle>{section.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <SortableTable columns={powerColumns} data={section.teams} defaultSort={{ key: "rank", dir: "asc" }} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
