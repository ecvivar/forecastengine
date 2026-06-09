"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type DashboardData } from "@/lib/api";
import { formatDate, formatPercent, getContinentColor, getConfidenceColor } from "@/lib/utils";
import ProbabilityBar from "@/components/ProbabilityBar";
import ConfidenceGauge from "@/components/ConfidenceGauge";
import { Trophy, Users, Swords, Target, TrendingUp, AlertTriangle } from "lucide-react";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard
      .get()
      .then(setData)
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

  if (error) {
    return (
      <div className="container-page">
        <Card>
          <CardContent className="p-8 text-center text-red-500">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
            <p>Failed to load dashboard: {error}</p>
            <p className="text-sm text-gray-400 mt-1">
              Ensure the backend API is running at{" "}
              {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="container-page space-y-8">
      {/* Hero */}
      <div className="bg-gradient-to-r from-primary-700 to-blue-800 rounded-2xl p-8 text-white">
        <h1 className="text-4xl font-bold">World Cup 2026</h1>
        <p className="text-blue-200 mt-2 text-lg">
          Tournament Forecasting &amp; Simulation Engine —{" "}
          {data.total_teams} teams, {data.total_groups} groups, {data.total_matches} matches
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Trophy, label: "Teams", value: data.total_teams, color: "text-yellow-500" },
          { icon: Users, label: "Groups", value: data.total_groups, color: "text-blue-500" },
          { icon: Swords, label: "Group Matches", value: data.group_matches, color: "text-green-500" },
          { icon: Target, label: "Knockout Matches", value: data.knockout_matches, color: "text-red-500" },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-6 flex items-center gap-4">
              <s.icon className={`w-8 h-8 ${s.color}`} />
              <div>
                <div className="stat-value">{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Top Teams */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-500" />
              Top 10 Teams (IGF Index)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.top_teams.slice(0, 10).map((t, i) => (
                <div
                  key={t.team_name}
                  className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0"
                >
                  <span className="text-lg font-bold text-gray-300 w-6">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{t.team_name}</span>
                      <Badge className={getContinentColor(t.continent)}>
                        {t.continent || "?"}
                      </Badge>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 mt-1">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-primary-600 h-2 rounded-full transition-all"
                        style={{ width: `${t.igf_score}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-lg font-bold text-primary-600">
                    {t.igf_score.toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
            <Link
              href="/rankings"
              className="text-sm text-primary-600 hover:underline mt-3 inline-block"
            >
              View full rankings →
            </Link>
          </CardContent>
        </Card>

        {/* Champion Probabilities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-500" />
              Champion Odds
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.winner_probs.length > 0 ? (
              <div className="space-y-2">
                {data.winner_probs.slice(0, 8).map((w) => (
                  <div
                    key={w.team_name}
                    className="flex items-center gap-2 py-1.5"
                  >
                    <span className="text-sm font-medium flex-1">
                      {w.team_name}
                    </span>
                    <span className="text-xs text-gray-400">
                      {w.final_prob.toFixed(0)}% F
                    </span>
                    <span className="text-xs text-gray-400">
                      {w.sf_prob.toFixed(0)}% SF
                    </span>
                    <span className="font-bold text-yellow-600 text-sm w-14 text-right">
                      {w.win_prob.toFixed(1)}%
                    </span>
                    <div className="w-16 bg-gray-100 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full"
                        style={{ width: `${w.win_prob}%` }}
                      />
                    </div>
                  </div>
                ))}
                <Link
                  href="/knockout"
                  className="text-sm text-primary-600 hover:underline mt-2 inline-block"
                >
                  Full knockout probabilities →
                </Link>
              </div>
            ) : (
              <div className="text-sm text-gray-400 italic py-4 text-center">
                No simulation data. Run a simulation first.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Groups Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Groups Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.groups.map((g) => (
              <Link key={g.name} href={`/groups/${g.name}`}>
                <div className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow cursor-pointer">
                  <h3 className="font-bold text-lg text-primary-700 mb-2">
                    Group {g.name}
                  </h3>
                  <div className="space-y-1">
                    {g.teams.map((t) => (
                      <div
                        key={t.team_name}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="flex items-center gap-1">
                          <span
                            className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                              t.position <= 2
                                ? "bg-green-500"
                                : "bg-gray-300"
                            }`}
                          >
                            {t.position}
                          </span>
                          {t.team_name}
                        </span>
                        <span className="text-gray-400">{t.points}pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Predictions */}
      {data.recent_predictions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Match Predictions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.recent_predictions.slice(0, 8).map((p) => (
                <div key={p.match_id} className="border-b border-gray-100 pb-3 last:border-0">
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                    <span>{p.stage ? p.stage.replace(/_/g, " ") : "?"}</span>
                    <span>{p.match_date ? formatDate(p.match_date) : "?"}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-medium w-28 text-right">{p.home_team}</span>
                    <div className="flex-1">
                      <ProbabilityBar
                        homeWin={p.home_win_prob}
                        draw={p.draw_prob}
                        awayWin={p.away_win_prob}
                        height={22}
                      />
                    </div>
                    <span className="font-medium w-28">{p.away_team}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span>
                      ML: <span className="font-bold">{p.most_likely_score || "?"}</span>
                    </span>
                    {p.confidence_index !== null && (
                      <Badge className={getConfidenceColor(p.confidence_index)}>
                        CI: {p.confidence_index?.toFixed(0)}
                      </Badge>
                    )}
                    {p.surprise_risk !== null && (
                      <Badge variant="warning">
                        Surprise: {(p.surprise_risk * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <Link
              href="/predictions"
              className="text-sm text-primary-600 hover:underline mt-2 inline-block"
            >
              All predictions →
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
