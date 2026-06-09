"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type PowerRanking, type PowerRankingTeam, type IGFScore } from "@/lib/api";
import { getContinentColor } from "@/lib/utils";
import Link from "next/link";
import { TrendingUp, BarChart3 } from "lucide-react";

type Tab = "igf" | "power";

export default function RankingsPage() {
  const [tab, setTab] = useState<Tab>("igf");
  const [scores, setScores] = useState<IGFScore[]>([]);
  const [power, setPower] = useState<PowerRanking | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.rankings.igf(),
      api.rankings.powerRanking().catch(() => null),
    ])
      .then(([igf, pr]) => {
        setScores(igf);
        setPower(pr);
      })
      .catch(() => {})
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

  const sorted = [...scores].sort((a, b) => b.igf_score - a.igf_score);

  return (
    <div className="container-page space-y-6">
      <h1 className="page-title">Rankings &amp; Power Rankings</h1>

      {/* Tab switcher */}
      <div className="flex gap-2">
        {[
          { key: "igf" as Tab, label: "IGF Rankings", icon: BarChart3 },
          { key: "power" as Tab, label: "Power Ranking", icon: TrendingUp },
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
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500 text-xs uppercase">
                    <th className="text-left py-2">Rank</th>
                    <th className="text-left py-2">Team</th>
                    <th className="text-center py-2">IGF Score</th>
                    <th className="text-center py-2">Elo</th>
                    <th className="text-center py-2">Form</th>
                    <th className="text-center py-2">xG</th>
                    <th className="text-center py-2">xGA</th>
                    <th className="text-center py-2">Squad</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((s, i) => (
                    <tr
                      key={s.team_id}
                      className="border-b border-gray-50 hover:bg-gray-50"
                    >
                      <td className="py-2">
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                            i < 3
                              ? "bg-yellow-500"
                              : i < 8
                                ? "bg-blue-500"
                                : "bg-gray-300"
                          }`}
                        >
                          {i + 1}
                        </span>
                      </td>
                      <td className="py-2 font-medium">{s.team_name}</td>
                      <td className="text-center py-2">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 bg-gray-100 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-primary-600 h-2 rounded-full"
                              style={{ width: `${s.igf_score}%` }}
                            />
                          </div>
                          <span className="font-bold text-primary-700">
                            {s.igf_score.toFixed(1)}
                          </span>
                        </div>
                      </td>
                      <td className="text-center py-2">
                        {s.components?.elo?.toFixed(0) || "—"}
                      </td>
                      <td className="text-center py-2">
                        {s.components?.form?.toFixed(0) || "—"}
                      </td>
                      <td className="text-center py-2">
                        {s.components?.xg?.toFixed(0) || "—"}
                      </td>
                      <td className="text-center py-2">
                        {s.components?.xga?.toFixed(0) || "—"}
                      </td>
                      <td className="text-center py-2">
                        {s.components?.squad_quality?.toFixed(0) || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-gray-500 text-xs uppercase">
                        <th className="text-left py-2">Rank</th>
                        <th className="text-left py-2">Team</th>
                        <th className="text-center py-2">IGF</th>
                        <th className="text-center py-2">Elo</th>
                        <th className="text-center py-2">FIFA Rank</th>
                      </tr>
                    </thead>
                    <tbody>
                      {section.teams.map((t: PowerRankingTeam) => (
                        <tr
                          key={t.team_name}
                          className="border-b border-gray-50 hover:bg-gray-50"
                        >
                          <td className="py-2">{t.rank}</td>
                          <td className="py-2 font-medium flex items-center gap-2">
                            {t.team_name}
                            <Badge className={getContinentColor(t.continent)}>
                              {t.continent || "?"}
                            </Badge>
                          </td>
                          <td className="text-center py-2 font-bold">
                            {t.igf_score.toFixed(1)}
                          </td>
                          <td className="text-center py-2">{t.elo_score}</td>
                          <td className="text-center py-2">#{t.fifa_rank}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
