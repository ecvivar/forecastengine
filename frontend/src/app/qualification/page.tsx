"use client";

import { useEffect, useState, useMemo } from "react";
import { api, QualificationResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { Trophy, Shield, Target, Swords, Zap } from "lucide-react";

const STAGES = [
  { key: "r16", label: "R16", icon: Shield, color: "bg-blue-100 text-blue-700" },
  { key: "qf", label: "QF", icon: Target, color: "bg-yellow-100 text-yellow-700" },
  { key: "sf", label: "SF", icon: Swords, color: "bg-orange-100 text-orange-700" },
  { key: "final", label: "Final", icon: Zap, color: "bg-purple-100 text-purple-700" },
  { key: "champion", label: "Champion", icon: Trophy, color: "bg-green-100 text-green-700" },
] as const;

export default function QualificationPage() {
  const [data, setData] = useState<QualificationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<string>("champion");

  useEffect(() => {
    api.insights.qualification()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const sorted = useMemo(() => {
    if (!data) return [];
    return [...data.heatmap].sort((a, b) => (b as any)[sortBy] - (a as any)[sortBy]);
  }, [data, sortBy]);

  const getOpacity = (val: number, max: number) => Math.max(0.1, Math.min(1, val / (max || 1)));

  if (loading) return <SkeletonPage />;
  if (!data) return null;

  const maxes: Record<string, number> = {};
  for (const s of STAGES) {
    maxes[s.key] = Math.max(...data.heatmap.map((h) => (h as any)[s.key]), 1);
  }

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Visualization</div>
        <h1 className="page-title">Qualification Heatmap</h1>
        <p className="page-subtitle">Probabilidades de avance por etapa para los 48 equipos.</p>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-[hsl(var(--muted))]">Sort by:</span>
        {STAGES.map((s) => (
          <button
            key={s.key}
            onClick={() => setSortBy(s.key)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              sortBy === s.key ? s.color : "bg-[hsl(var(--surface-secondary))] text-[hsl(var(--muted))]"
            }`}
          >
            <s.icon className="w-3 h-3 inline mr-1" />
            {s.label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-[hsl(var(--muted))] border-b border-[hsl(var(--border))]">
              <th className="pb-2 pr-4 sticky left-0 bg-[hsl(var(--surface))] z-10">Team</th>
              {STAGES.map((s) => (
                <th key={s.key} className="pb-2 px-3 text-center">{s.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((team) => (
              <tr key={team.team_name} className="border-b border-[hsl(var(--border))] last:border-0 hover:bg-[hsl(var(--surface-secondary))]/50">
                <td className="py-2 pr-4 sticky left-0 bg-[hsl(var(--surface))] z-10 font-medium text-sm whitespace-nowrap">
                  {team.team_name}
                </td>
                {STAGES.map((s) => {
                  const val = (team as any)[s.key] as number;
                  const max = maxes[s.key];
                  return (
                    <td key={s.key} className="px-3 py-2 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <div
                          className="w-full h-6 rounded flex items-center justify-center text-xs font-mono font-bold transition-colors"
                          style={{
                            backgroundColor: `hsla(${s.key === "champion" ? 142 : s.key === "final" ? 270 : s.key === "sf" ? 30 : s.key === "qf" ? 45 : 210}, 70%, ${50 + (1 - getOpacity(val, max)) * 30}%, ${getOpacity(val, max) * 0.8 + 0.2})`,
                            color: getOpacity(val, max) > 0.5 ? "white" : "hsl(var(--foreground))",
                          }}
                        >
                          {val.toFixed(1)}%
                        </div>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-[hsl(var(--muted))] italic">
        Basado en la simulación Monte Carlo más reciente. Los colores más intensos indican mayor probabilidad.
      </div>
    </div>
  );
}
