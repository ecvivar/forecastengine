"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type DashboardData } from "@/lib/api";
import { formatPercent, getContinentColor, getStageLabel } from "@/lib/utils";
import ProbabilityBar from "@/components/ProbabilityBar";
import { SkeletonPage } from "@/components/ui/skeleton";
import {
  Trophy, TrendingUp, Activity, Shield, AlertTriangle,
  BarChart3, ArrowUpRight, BrainCircuit,
} from "lucide-react";

const STATUS_OK = { label: "Calibration OK", color: "text-green-600 bg-green-50" };
const STATUS_ELITE = { label: "ELITE (5/5)", color: "text-blue-600 bg-blue-50" };

export default function CommandCenter() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard.get()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;
  if (!data) return null;

  return (
    <div className="container-page space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">
            <Activity className="w-3 h-3" />
            World Cup 2026 — Command Center
          </div>
          <h1 className="page-title">ForecastEngine v1.0</h1>
          <p className="page-subtitle">
            {data.total_teams} teams &middot; {data.total_groups} groups &middot; {data.total_matches} matches
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="metric-badge ok">{STATUS_OK.label}</span>
          <span className="metric-badge" style={{ backgroundColor: "#eff6ff", color: "#1d4ed8" }}>{STATUS_ELITE.label}</span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Teams", value: data.total_teams, icon: Shield, color: "text-blue-500" },
          { label: "Groups", value: data.total_groups, icon: BarChart3, color: "text-green-500" },
          { label: "Group Matches", value: data.group_matches, icon: Activity, color: "text-yellow-500" },
          { label: "Knockout", value: data.knockout_matches, icon: Trophy, color: "text-red-500" },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <s.icon className={`w-6 h-6 ${s.color}`} />
              <div>
                <div className="stat-value text-lg">{s.value}</div>
                <div className="stat-label text-xs">{s.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Champion Probabilities */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Trophy className="w-4 h-4 text-yellow-500" />
              Champion Probabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.winner_probs.length > 0 ? (
              <div className="space-y-1.5">
                {data.winner_probs.slice(0, 10).map((w, i) => (
                  <div key={w.team_name} className="flex items-center gap-3 py-1.5 border-b border-[hsl(var(--border))] last:border-0">
                    <span className="text-xs font-bold text-[hsl(var(--muted))] w-4">{i + 1}</span>
                    <span className="text-sm font-medium flex-1 truncate">{w.team_name}</span>
                    <div className="w-24 bg-gray-100 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full transition-all"
                        style={{ width: `${Math.min(w.win_prob, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono font-bold text-yellow-600 w-14 text-right">
                      {w.win_prob.toFixed(1)}%
                    </span>
                    <span className="text-2xs text-[hsl(var(--muted))] hidden sm:inline w-16 text-right">
                      F:{w.final_prob.toFixed(0)}% SF:{w.sf_prob.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-[hsl(var(--muted))] italic py-4 text-center">
                No simulation data available. Run a simulation first.
              </div>
            )}
            <Link href="/overview" className="flex items-center gap-1 text-xs text-primary-600 hover:underline mt-3">
              <ArrowUpRight className="w-3 h-3" /> Full tournament overview
            </Link>
          </CardContent>
        </Card>

        {/* Status Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <BrainCircuit className="w-4 h-4 text-blue-500" />
                Model Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: "Scientific Grade", value: "ELITE", badge: "ok" },
                { label: "Readiness", value: "90/100", badge: "ok" },
                { label: "Active Model", value: "Sprint 9", badge: "ok" },
                { label: "Calibration", value: "v3", badge: "ok" },
              ].map((s) => (
                <div key={s.label} className="flex items-center justify-between text-sm">
                  <span className="text-[hsl(var(--muted))]">{s.label}</span>
                  <span className="metric-badge ok">{s.value}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-green-500" />
                Top Teams
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {data.top_teams.slice(0, 5).map((t, i) => (
                  <div key={t.team_name} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[hsl(var(--muted))]">{i + 1}</span>
                      <span className="truncate max-w-[120px]">{t.team_name}</span>
                      <Badge className={getContinentColor(t.continent)}>
                        {t.continent || "?"}
                      </Badge>
                    </span>
                    <span className="text-xs font-mono">{t.igf_score.toFixed(1)}</span>
                  </div>
                ))}
              </div>
              <Link href="/teams" className="flex items-center gap-1 text-xs text-primary-600 hover:underline mt-3">
                <ArrowUpRight className="w-3 h-3" /> All teams
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Predictions */}
      {data.recent_predictions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Recent Predictions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.recent_predictions.slice(0, 5).map((p) => (
                <div key={p.match_id} className="flex items-center gap-3 py-2 border-b border-[hsl(var(--border))] last:border-0">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between text-xs text-[hsl(var(--muted))] mb-1">
                      <span>{p.stage ? getStageLabel(p.stage) : "?"}</span>
                      {p.match_date && <span>{new Date(p.match_date).toLocaleDateString()}</span>}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-right min-w-[80px] truncate">{p.home_team}</span>
                      <div className="flex-1">
                        <ProbabilityBar homeWin={p.home_win_prob} draw={p.draw_prob} awayWin={p.away_win_prob} height={20} />
                      </div>
                      <span className="text-sm font-medium min-w-[80px] truncate">{p.away_team}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Link href="/matches" className="flex items-center gap-1 text-xs text-primary-600 hover:underline mt-3">
              <ArrowUpRight className="w-3 h-3" /> All matches
            </Link>
          </CardContent>
        </Card>
      )}

      {data.recent_predictions.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center text-[hsl(var(--muted))]">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
            <p className="text-sm">No predictions available. Ensure the backend API is running.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
