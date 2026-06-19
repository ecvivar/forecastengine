"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import GroupHeatmap from "@/components/GroupHeatmap";
import { api, getApiErrorMessage, type GroupDetail, type SimulationProbabilities } from "@/lib/api";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function GroupsPage() {
  const [groups, setGroups] = useState<GroupDetail[]>([]);
  const [probs, setProbs] = useState<SimulationProbabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.groups.list(),
      api.simulations.list().then((sims) => {
        const completed = sims.find((s) => s.status === "completed");
        return completed ? api.simulations.probabilities(completed.id) : null;
      }),
    ])
      .then(([g, p]) => {
        if (!Array.isArray(g)) {
          setError("Invalid response: expected an array of groups");
          return;
        }
        setGroups(g);
        setProbs(p);
      })
      .catch((err) => {
        setError(getApiErrorMessage(err));
        setGroups([]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) return <SkeletonPage />;

  if (error) {
    return (
      <div className="container-page flex items-center justify-center min-h-[60vh]">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Failed to load groups</h2>
            <p className="text-sm text-gray-500 mb-6">{error}</p>
            <button
              onClick={load}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Try again
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const sorted = [...groups].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="container-page space-y-6">
      <h1 className="page-title">Groups</h1>
      <p className="page-subtitle">
        12 groups of 4 — click any group for detailed standings and qualification probabilities
      </p>

      {probs && (
        <Card>
          <CardHeader>
            <CardTitle>Qualification Heatmap</CardTitle>
          </CardHeader>
          <CardContent>
            <GroupHeatmap groups={probs.groups} />
          </CardContent>
        </Card>
      )}

      {sorted.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400 italic">No groups found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sorted.map((group) => (
            <Link key={group.id} href={`/groups/${group.name}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Group {group.name}</span>
                    <Badge variant="info" className="text-xs">
                      {Array.isArray(group.standings) ? group.standings.length : 0} teams
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {Array.isArray(group.standings) && group.standings.length > 0 ? (
                    <div className="space-y-2">
                      {[...group.standings]
                        .sort((a, b) => a.position - b.position)
                        .map((s) => (
                          <div
                            key={s.id}
                            className="flex items-center justify-between text-sm py-1 border-b border-gray-50 last:border-0"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white ${
                                  s.position <= 2
                                    ? "bg-green-500"
                                    : "bg-gray-300"
                                }`}
                              >
                                {s.position}
                              </span>
                              <span
                                className={
                                  s.qualified ? "font-semibold" : "text-gray-600"
                                }
                              >
                                {s.team_name}
                              </span>
                              {s.qualified && (
                                <Badge
                                  variant="success"
                                  className="text-[9px] px-1"
                                >
                                  Q
                                </Badge>
                              )}
                            </div>
                            <span className="text-gray-400 font-medium">
                              {s.points} pts
                            </span>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-400 italic">
                      No standings data
                    </p>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
