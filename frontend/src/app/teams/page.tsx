"use client";

import { useEffect, useState } from "react";
import { api, Team, IGFScore } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import TeamRadarChart from "@/components/TeamRadarChart";
import { getContinentColor } from "@/lib/utils";
import { X, BarChart3 } from "lucide-react";

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [igfScores, setIgfScores] = useState<IGFScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([
      api.teams.list(1, 100),
      api.rankings.igf().catch(() => []),
    ])
      .then(([t, igf]) => {
        setTeams(t);
        setIgfScores(igf);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;

  const igfMap = new Map(igfScores.map((s) => [s.team_name, s]));
  const filtered = teams.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Teams</h1>
          <p className="page-subtitle">All 48 participating nations in the 2026 World Cup.</p>
        </div>
        <input
          type="text"
          placeholder="Search teams..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-48"
        />
      </div>

      {selectedTeam && (
        <Card className="mb-6 border-2 border-primary-200">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary-600" />
              IGF Profile
            </CardTitle>
            <button
              onClick={() => setSelectedTeam(null)}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </CardHeader>
          <CardContent>
            <TeamRadarChart
              teamName={selectedTeam}
              components={igfMap.get(selectedTeam)?.components || {}}
            />
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((team) => {
          const igf = igfMap.get(team.name);
          return (
            <button
              key={team.id}
              onClick={() => setSelectedTeam(team.name)}
              className={`text-left transition-all ${
                selectedTeam === team.name ? "ring-2 ring-primary-500 rounded-xl" : ""
              }`}
            >
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                <CardHeader className="flex flex-row items-center gap-3 pb-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
                    {team.fifa_code || team.name.slice(0, 3).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <CardTitle className="text-base truncate max-w-[160px]">{team.name}</CardTitle>
                    <Badge className={getContinentColor(team.continent)}>
                      {team.continent || "Unknown"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-gray-500">
                  <div>Code: {team.fifa_code || "—"}</div>
                  {team.founded_year && <div>Founded: {team.founded_year}</div>}
                  {igf && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                        <div
                          className="bg-primary-500 h-1.5 rounded-full"
                          style={{ width: `${igf.igf_score}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-primary-600">
                        IGF {igf.igf_score.toFixed(0)}
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </button>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          No teams matching &ldquo;{search}&rdquo;
        </div>
      )}
    </div>
  );
}
