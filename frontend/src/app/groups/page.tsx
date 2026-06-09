"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import GroupHeatmap from "@/components/GroupHeatmap";
import { api, type GroupDetail, type SimulationProbabilities } from "@/lib/api";
import { getContinentColor } from "@/lib/utils";

export default function GroupsPage() {
  const [groups, setGroups] = useState<GroupDetail[]>([]);
  const [probs, setProbs] = useState<SimulationProbabilities | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.groups.list(),
      api.simulations.list().then((sims) => {
        const completed = sims.find((s) => s.status === "completed");
        return completed ? api.simulations.probabilities(completed.id) : null;
      }),
    ])
      .then(([g, p]) => {
        setGroups(g);
        setProbs(p);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {sorted.map((group) => (
          <Link key={group.id} href={`/groups/${group.name}`}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Group {group.name}</span>
                  <Badge variant="info" className="text-xs">
                    {group.standings?.length || 0} teams
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {group.standings && group.standings.length > 0 ? (
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
    </div>
  );
}
