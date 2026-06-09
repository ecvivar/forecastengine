"use client";

import { useEffect, useState } from "react";
import { api, Team } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getContinentColor } from "@/lib/utils";

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.teams.list(1, 100).then(setTeams).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="container-page">
      <h1 className="page-title">Teams</h1>
      <p className="page-subtitle mb-6">All 48 participating nations in the 2026 World Cup.</p>

      {loading ? (
        <p className="text-gray-500">Loading teams...</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {teams.map((team) => (
            <Card key={team.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center gap-3 pb-2">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700">
                  {team.fifa_code || team.name.slice(0, 3).toUpperCase()}
                </div>
                <div>
                  <CardTitle className="text-base">{team.name}</CardTitle>
                  <Badge className={getContinentColor(team.continent)}>
                    {team.continent || "Unknown"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="text-sm text-gray-500">
                <div>Code: {team.fifa_code || "—"}</div>
                {team.founded_year && <div>Founded: {team.founded_year}</div>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
