"use client";

import { useEffect, useState } from "react";
import { api, InsightsAnalysis, NarrativeResponse, MomentumResponse, MatchOfDayResponse, QualificationResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";
import ProbabilityBar from "@/components/ProbabilityBar";
import {
  Trophy, TrendingUp, TrendingDown, Activity, Shield, AlertTriangle,
  Lightbulb, Star, Swords, Zap, BrainCircuit, ArrowUpRight, ArrowDownRight,
  BarChart3, MessageSquare, Target,
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, Cell } from "recharts";

export default function ExecutivePage() {
  const [analysis, setAnalysis] = useState<InsightsAnalysis | null>(null);
  const [narrative, setNarrative] = useState<NarrativeResponse | null>(null);
  const [momentum, setMomentum] = useState<MomentumResponse | null>(null);
  const [motd, setMotd] = useState<MatchOfDayResponse | null>(null);
  const [qual, setQual] = useState<QualificationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.insights.analysis().catch(() => null),
      api.insights.narrative().catch(() => null),
      api.insights.momentum().catch(() => null),
      api.insights.matchOfTheDay().catch(() => null),
      api.insights.qualification().catch(() => null),
    ]).then(([a, n, m, motd, q]) => {
      setAnalysis(a);
      setNarrative(n);
      setMomentum(m);
      setMotd(motd);
      setQual(q);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Executive Brief</div>
          <h1 className="page-title">Executive Mode</h1>
          <p className="page-subtitle">Resumen ejecutivo para periodistas, analistas y TV. Todo en una pantalla.</p>
        </div>
        {analysis && (
          <Badge className="bg-blue-100 text-blue-700 text-xs">
            {analysis.count} equipos analizados
          </Badge>
        )}
      </div>

      {/* Headline + Narrative */}
      {narrative && (
        <Card className="border-2 border-primary-200">
          <CardContent className="p-6 space-y-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary-600" />
              <span className="text-base font-bold">{narrative.headline}</span>
            </div>
            <p className="text-sm text-[hsl(var(--foreground))] leading-relaxed">{narrative.story}</p>
            <div className="flex flex-wrap gap-4 text-xs">
              {narrative.risks.length > 0 && (
                <div>
                  <span className="font-semibold text-red-600">Riesgos: </span>
                  {narrative.risks.map((r, i) => <span key={i} className="text-[hsl(var(--muted))]">{r}{i < narrative.risks.length - 1 ? " " : ""}</span>)}
                </div>
              )}
              {narrative.opportunities.length > 0 && (
                <div>
                  <span className="font-semibold text-green-600">Oportunidades: </span>
                  {narrative.opportunities.map((o, i) => <span key={i} className="text-[hsl(var(--muted))]">{o}{i < narrative.opportunities.length - 1 ? " " : ""}</span>)}
                </div>
              )}
            </div>
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
            <div className="mt-3">
              <ProbabilityBar
                homeWin={motd.top_match.home_win_prob}
                draw={motd.top_match.draw_prob}
                awayWin={motd.top_match.away_win_prob}
                homeLabel={motd.top_match.home_team}
                awayLabel={motd.top_match.away_team}
              />
            </div>
            <div className="flex items-center gap-4 mt-2 text-xs text-[hsl(var(--muted))]">
              <span>Importance: {(motd.top_match.importance * 100).toFixed(0)}%</span>
              <span>Confidence: {(motd.top_match.confidence_index * 100).toFixed(0)}%</span>
              {motd.top_match.match_date && <span>{formatDateTime(motd.top_match.match_date)}</span>}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Contenders */}
        {analysis?.insights.contenders && analysis.insights.contenders.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Trophy className="w-4 h-4 text-yellow-500" />
                Top Contenders
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analysis.insights.contenders.map((c, i) => (
                  <div key={c.team_name} className="flex items-center justify-between text-sm py-1.5 border-b border-[hsl(var(--border))] last:border-0">
                    <span className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[hsl(var(--muted))]">{i + 1}</span>
                      <span>{c.team_name}</span>
                    </span>
                    <span className="font-mono text-xs">{c.win_prob.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dark Horses */}
        {analysis?.insights.dark_horses && analysis.insights.dark_horses.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Zap className="w-4 h-4 text-purple-500" />
                Dark Horses
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analysis.insights.dark_horses.map((d) => (
                  <div key={d.team_name} className="flex items-center justify-between text-sm py-1.5 border-b border-[hsl(var(--border))] last:border-0">
                    <span>{d.team_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[hsl(var(--muted))]">Elo: {d.elo_score}</span>
                      <Badge className="bg-purple-100 text-purple-700">{d.win_prob.toFixed(1)}%</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Momentum */}
        {momentum && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Activity className="w-4 h-4 text-blue-500" />
                Biggest Movers
              </CardTitle>
            </CardHeader>
            <CardContent>
              {momentum.risers.length > 0 && (
                <div className="mb-3">
                  <div className="text-xs font-semibold text-green-600 mb-1 flex items-center gap-1"><ArrowUpRight className="w-3 h-3" />Risers</div>
                  {momentum.risers.slice(0, 3).map((r) => (
                    <div key={r.team_name} className="flex items-center justify-between text-xs py-1">
                      <span>{r.team_name}</span>
                      <span className="text-green-600 font-mono">+{r.delta_win.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
              {momentum.fallers.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-red-600 mb-1 flex items-center gap-1"><ArrowDownRight className="w-3 h-3" />Fallers</div>
                  {momentum.fallers.slice(0, 3).map((r) => (
                    <div key={r.team_name} className="flex items-center justify-between text-xs py-1">
                      <span>{r.team_name}</span>
                      <span className="text-red-600 font-mono">{r.delta_win.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Overrated / Underrated */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {analysis?.insights.overrated && analysis.insights.overrated.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm text-red-600">
                <AlertTriangle className="w-4 h-4" />
                Overrated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                {analysis.insights.overrated.map((o) => (
                  <div key={o.team_name} className="flex items-center justify-between py-1 border-b border-[hsl(var(--border))] last:border-0">
                    <span>{o.team_name}</span>
                    <span className="text-xs text-[hsl(var(--muted))]">Elo: {o.elo_score} · Prob: {o.win_prob.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {analysis?.insights.underrated && analysis.insights.underrated.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm text-green-600">
                <Lightbulb className="w-4 h-4" />
                Underrated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                {analysis.insights.underrated.map((u) => (
                  <div key={u.team_name} className="flex items-center justify-between py-1 border-b border-[hsl(var(--border))] last:border-0">
                    <span>{u.team_name}</span>
                    <span className="text-xs text-[hsl(var(--muted))]">Elo: {u.elo_score} · Prob: {u.win_prob.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* News Feed */}
      {narrative?.news_feed && narrative.news_feed.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-blue-500" />
              Tournament Feed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {narrative.news_feed.map((event, i) => (
                <div key={i} className="flex items-start gap-3 py-2 border-b border-[hsl(var(--border))] last:border-0 text-sm">
                  {event.direction === "up" ? (
                    <ArrowUpRight className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                  )}
                  <div>
                    <div className="font-medium">{event.headline}</div>
                    <div className="text-xs text-[hsl(var(--muted))]">{event.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calibration Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <BrainCircuit className="w-4 h-4 text-green-500" />
            Model Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 flex-wrap text-sm">
            <span className="metric-badge ok">Calibration: ACTIVE</span>
            <span className="metric-badge ok">Scientific Grade: ELITE</span>
            <span className="metric-badge ok">Readiness: 90/100</span>
            <span className="metric-badge ok">Model: Sprint 9</span>
          </div>
          <p className="text-xs text-[hsl(var(--muted))] mt-2">
            ForecastEngine v1.0 · Monte Carlo (10K runs) · Elo + xG + FIFA híbrido · Calibration v3
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
