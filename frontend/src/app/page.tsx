"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type DashboardData, type NarrativeResponse, type MomentumResponse, type MatchOfDayResponse } from "@/lib/api";
import { formatPercent, getContinentColor, getStageLabel } from "@/lib/utils";
import ProbabilityBar from "@/components/ProbabilityBar";
import { SkeletonPage } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import {
  Trophy, TrendingUp, Activity, Shield, AlertTriangle,
  BarChart3, ArrowUpRight, ArrowDownRight, BrainCircuit, RefreshCw, Globe,
  Star, Zap, MessageSquare, ArrowUpCircle, ArrowDownCircle,
} from "lucide-react";

const STATUS_OK = { label: "Calibration OK", color: "text-green-600 bg-green-50" };
const STATUS_ELITE = { label: "ELITE (5/5)", color: "text-blue-600 bg-blue-50" };

export default function CommandCenter() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [narrative, setNarrative] = useState<NarrativeResponse | null>(null);
  const [momentum, setMomentum] = useState<MomentumResponse | null>(null);
  const [motd, setMotd] = useState<MatchOfDayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.dashboard.get(),
      api.insights.narrative().catch(() => null),
      api.insights.momentum().catch(() => null),
      api.insights.matchOfTheDay().catch(() => null),
    ]).then(([d, n, m, motd]) => {
      setData(d);
      setNarrative(n);
      setMomentum(m);
      setMotd(motd);
    }).catch((err) => {
      console.error(err);
      setError("Unable to load dashboard data.");
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!data) return <ErrorState message="Dashboard data is unavailable." />;

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

      {/* Groups Overview */}
      {data.groups && data.groups.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Globe className="w-4 h-4 text-blue-500" />
              Group Standings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {data.groups.map((g) => (
                <div key={g.name} className="panel p-3">
                  <div className="text-xs font-semibold mb-2 uppercase tracking-wider">Group {g.name}</div>
                  <div className="space-y-1">
                    {g.teams.slice(0, 4).map((t) => (
                      <div key={t.team_name} className="flex items-center justify-between text-xs py-0.5">
                        <span className="flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${t.qualified ? "bg-green-500" : "bg-gray-300"}`} />
                          <span className="truncate max-w-[100px]">{t.team_name}</span>
                        </span>
                        <span className="font-mono">{t.points}pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <Link href="/groups" className="flex items-center gap-1 text-xs text-primary-600 hover:underline mt-3">
              <ArrowUpRight className="w-3 h-3" /> Full group analysis
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Match of the Day */}
      {motd?.top_match && (
        <Card className="border-2 border-yellow-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-yellow-700">
              <Star className="w-4 h-4" />
              Today&apos;s Most Important Match
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">{motd.top_match.home_team}</div>
              <div className="text-center">
                <div className="text-lg font-bold font-mono">{motd.top_match.most_likely_score}</div>
                <Badge className={motd.top_match.contender_involved ? "bg-green-100 text-green-700" : "bg-gray-100"}>{motd.top_match.stage}</Badge>
              </div>
              <div className="text-sm font-medium">{motd.top_match.away_team}</div>
            </div>
            <div className="mt-2">
              <ProbabilityBar
                homeWin={motd.top_match.home_win_prob}
                draw={motd.top_match.draw_prob}
                awayWin={motd.top_match.away_win_prob}
                homeLabel={motd.top_match.home_team}
                awayLabel={motd.top_match.away_team}
                height={24}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Narrative Headline */}
      {narrative?.headline && (
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <MessageSquare className="w-5 h-5 text-primary-500 shrink-0" />
            <div>
              <div className="text-sm font-semibold">{narrative.headline}</div>
              <div className="text-xs text-[hsl(var(--muted))] mt-0.5">{narrative.story}</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Insights Widgets Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Biggest Risers */}
        {momentum && momentum.risers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xs text-green-600">
                <ArrowUpCircle className="w-3 h-3" />
                Biggest Risers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {momentum.risers.slice(0, 3).map((r) => (
                  <div key={r.team_name} className="flex items-center justify-between text-xs py-0.5">
                    <span>{r.team_name}</span>
                    <span className="text-green-600 font-mono">+{r.delta_win.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Biggest Fallers */}
        {momentum && momentum.fallers.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xs text-red-600">
                <ArrowDownCircle className="w-3 h-3" />
                Biggest Fallers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {momentum.fallers.slice(0, 3).map((r) => (
                  <div key={r.team_name} className="flex items-center justify-between text-xs py-0.5">
                    <span>{r.team_name}</span>
                    <span className="text-red-600 font-mono">{r.delta_win.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dark Horses / Tourney Headlines */}
        {narrative && narrative.news_feed.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xs text-purple-600">
                <Zap className="w-3 h-3" />
                Tournament Headlines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {narrative.news_feed.slice(0, 3).map((event, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs">
                    {event.direction === "up" ? (
                      <ArrowUpRight className="w-3 h-3 text-green-500 shrink-0" />
                    ) : (
                      <ArrowDownRight className="w-3 h-3 text-red-500 shrink-0" />
                    )}
                    <span>{event.headline}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { href: "/predictions", label: "Predict Match", icon: Activity },
          { href: "/simulations", label: "Run Simulation", icon: RefreshCw },
          { href: "/compare", label: "Compare Teams", icon: BarChart3 },
          { href: "/momentum", label: "Momentum", icon: TrendingUp },
        ].map((action) => (
          <Link key={action.href} href={action.href}>
            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex items-center gap-3">
                <action.icon className="w-5 h-5 text-primary-500" />
                <span className="text-sm font-medium">{action.label}</span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
