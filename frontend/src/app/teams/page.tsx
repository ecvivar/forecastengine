"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { api, Team, IGFScore } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import TeamRadarChart from "@/components/TeamRadarChart";
import { getContinentColor } from "@/lib/utils";
import { X, BarChart3, Shield, Search, Filter } from "lucide-react";

const CONTINENTS = ["UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"];

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [igfScores, setIgfScores] = useState<IGFScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [continentFilter, setContinentFilter] = useState<string | null>(null);
  const [view, setView] = useState<"grid" | "igf">("grid");

  useEffect(() => {
    Promise.all([
      api.teams.list(1, 100),
      api.rankings.igf().catch(() => []),
    ])
      .then(([t, igf]) => {
        setTeams(t);
        setIgfScores(igf);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load teams.");
      })
      .finally(() => setLoading(false));
  }, []);

  const igfMap = new Map(igfScores.map((s) => [s.team_name, s]));

  const filtered = useMemo(() => {
    return teams.filter((t) => {
      if (search && !t.name.toLowerCase().includes(search.toLowerCase())) return false;
      if (continentFilter && t.continent !== continentFilter) return false;
      return true;
    });
  }, [teams, search, continentFilter]);

  const topIgf = useMemo(() => {
    return [...igfScores]
      .filter((s) => search ? s.team_name.toLowerCase().includes(search.toLowerCase()) : true)
      .filter((s) => continentFilter ? teams.find((t) => t.name === s.team_name)?.continent === continentFilter : true)
      .sort((a, b) => b.igf_score - a.igf_score);
  }, [igfScores, search, continentFilter, teams]);

  if (loading) return <SkeletonPage />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Teams</h1>
          <p className="page-subtitle">All {teams.length} participating nations.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView(view === "grid" ? "igf" : "grid")}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              view === "igf" ? "bg-primary-50 border-primary-300 text-primary-700" : "border-gray-200 text-gray-500 hover:bg-gray-50"
            }`}
          >
            {view === "grid" ? "IGF Ranking" : "Grid View"}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--muted))]" />
          <input
            type="text"
            placeholder="Search teams..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-[hsl(var(--border))] rounded-lg text-sm bg-transparent focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div className="flex items-center gap-1">
          <Filter className="w-4 h-4 text-[hsl(var(--muted))]" />
          {CONTINENTS.map((c) => (
            <button
              key={c}
              onClick={() => setContinentFilter(continentFilter === c ? null : c)}
              className={`px-2 py-1 text-xs rounded-lg border transition-colors ${
                continentFilter === c
                  ? "bg-primary-50 border-primary-300 text-primary-700"
                  : "border-gray-200 text-gray-500 hover:bg-gray-50"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {selectedTeam && (
        <Card className="border-2 border-primary-200">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary-600" />
              IGF Profile: {selectedTeam}
            </CardTitle>
            <button onClick={() => setSelectedTeam(null)} className="p-1 hover:bg-gray-100 rounded transition-colors">
              <X className="w-4 h-4" />
            </button>
          </CardHeader>
          <CardContent>
            <TeamRadarChart teamName={selectedTeam} components={igfMap.get(selectedTeam)?.components || {}} />
          </CardContent>
        </Card>
      )}

      {view === "grid" ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((team) => {
            const igf = igfMap.get(team.name);
            return (
              <Link key={team.id} href={`/teams/${team.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader className="flex flex-row items-center gap-3 pb-2">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
                      {team.fifa_code || team.name.slice(0, 3).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-base truncate max-w-[160px]">{team.name}</CardTitle>
                      <Badge className={getContinentColor(team.continent)}>
                        {team.continent || "Unknown"}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="text-sm text-[hsl(var(--muted))]">
                    <div>Code: {team.fifa_code || "—"}</div>
                    {team.founded_year && <div>Founded: {team.founded_year}</div>}
                    {igf && (
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                          <div className="bg-primary-500 h-1.5 rounded-full" style={{ width: `${igf.igf_score}%` }} />
                        </div>
                        <span className="text-xs font-bold text-primary-600">IGF {igf.igf_score.toFixed(0)}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Shield className="w-4 h-4 text-purple-500" />
              IGF Power Ranking
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-0.5">
              {topIgf.map((s, i) => {
                const team = teams.find((t) => t.name === s.team_name);
                return (
                  <Link key={s.team_id} href={`/teams/${s.team_id}`}>
                    <div className="flex items-center gap-3 py-2 px-2 rounded-lg hover:bg-gray-50 transition-colors border-b border-[hsl(var(--border))] last:border-0">
                      <span className="text-xs font-bold text-[hsl(var(--muted))] w-6">{i + 1}</span>
                      <Badge className={getContinentColor(team?.continent || null)}>
                        {team?.continent || "?"}
                      </Badge>
                      <span className="text-sm font-medium flex-1 truncate">{s.team_name}</span>
                      <div className="w-24 bg-gray-100 rounded-full h-1.5">
                        <div className="bg-primary-500 h-1.5 rounded-full" style={{ width: `${s.igf_score}%` }} />
                      </div>
                      <span className="text-xs font-mono font-bold text-primary-600 w-8 text-right">
                        {s.igf_score.toFixed(0)}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {filtered.length === 0 && (
        <div className="text-center py-12 text-[hsl(var(--muted))]">
          No teams matching &ldquo;{search}&rdquo;
        </div>
      )}
    </div>
  );
}
