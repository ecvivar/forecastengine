"use client";

import { useEffect, useState } from "react";
import { api, GroupDetail } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function GroupsPage() {
  const [groups, setGroups] = useState<GroupDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.groups.list().then(setGroups).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="container-page">
      <h1 className="page-title">Groups</h1>
      <p className="page-subtitle mb-6">Group stage standings for World Cup 2026.</p>

      {loading ? (
        <p className="text-gray-500">Loading groups...</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {groups.map((group) => (
            <Card key={group.id}>
              <CardHeader>
                <CardTitle>Group {group.name}</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-gray-500">
                      <th className="px-4 pb-2 font-medium">Pos</th>
                      <th className="px-4 pb-2 font-medium">Team</th>
                      <th className="px-4 pb-2 font-medium">Pts</th>
                      <th className="px-4 pb-2 font-medium">GD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.standings.map((s) => (
                      <tr key={s.id} className="border-b last:border-0">
                        <td className="px-4 py-2 text-gray-500">{s.position}</td>
                        <td className="px-4 py-2 font-medium">
                          {s.team_name}
                          {s.qualified && (
                            <Badge variant="success" className="ml-2">Q</Badge>
                          )}
                        </td>
                        <td className="px-4 py-2 font-mono font-bold">{s.points}</td>
                        <td className="px-4 py-2 font-mono">{s.goal_difference}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
