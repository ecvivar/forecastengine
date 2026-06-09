"use client";

import { useEffect, useState } from "react";
import { api, IGFScore } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function RankingsPage() {
  const [igf, setIgf] = useState<IGFScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.rankings.igf().then(setIgf).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="container-page">
      <h1 className="page-title">Global Strength Index (IGF)</h1>
      <p className="page-subtitle mb-6">
        Composite strength rating combining Elo, form, xG, xGA, opponent strength,
        World Cup experience, and squad quality.
      </p>

      {loading ? (
        <p className="text-gray-500">Loading rankings...</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left">
                <th className="px-4 py-3 font-medium text-gray-500">Rank</th>
                <th className="px-4 py-3 font-medium text-gray-500">Team</th>
                <th className="px-4 py-3 font-medium text-gray-500">IGF Score</th>
                <th className="px-4 py-3 font-medium text-gray-500">Elo</th>
                <th className="px-4 py-3 font-medium text-gray-500">Form</th>
                <th className="px-4 py-3 font-medium text-gray-500">xG</th>
                <th className="px-4 py-3 font-medium text-gray-500">xGA</th>
                <th className="px-4 py-3 font-medium text-gray-500">Squad</th>
              </tr>
            </thead>
            <tbody>
              {igf.map((r, i) => (
                <tr key={r.team_id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-bold text-gray-900">{i + 1}</td>
                  <td className="px-4 py-3 font-medium">{r.team_name}</td>
                  <td className="px-4 py-3">
                    <Badge variant="info">{r.igf_score.toFixed(4)}</Badge>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {r.components.elo?.toFixed(3) || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {r.components.form?.toFixed(3) || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {r.components.xg?.toFixed(3) || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {r.components.xga?.toFixed(3) || "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {r.components.squad_quality?.toFixed(3) || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
