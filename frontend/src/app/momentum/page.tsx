"use client";

import { useEffect, useState } from "react";
import { api, MomentumResponse } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import {
  TrendingUp, TrendingDown, Activity, ArrowUpRight, ArrowDownRight,
} from "lucide-react";

export default function MomentumPage() {
  const [data, setData] = useState<MomentumResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.insights.momentum()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;
  if (!data) return null;

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Trends</div>
        <h1 className="page-title">Momentum Tracker</h1>
        <p className="page-subtitle">Detecta subidas y bajadas de probabilidades entre simulaciones consecutivas.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-green-600">
              <TrendingUp className="w-4 h-4" />
              Biggest Risers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.risers.length > 0 ? (
              <div className="space-y-2">
                {data.risers.map((r) => (
                  <div key={r.team_name} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
                    <div className="flex items-center gap-2">
                      <ArrowUpRight className="w-3 h-3 text-green-500" />
                      <span className="text-sm font-medium">{r.team_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-[hsl(var(--muted))]">{r.prev_win_prob.toFixed(1)}% → {r.win_prob.toFixed(1)}%</span>
                      <Badge className="bg-green-100 text-green-700">+{r.delta_win.toFixed(1)}%</Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-[hsl(var(--muted))] italic py-4 text-center">No risers detected.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-red-600">
              <TrendingDown className="w-4 h-4" />
              Biggest Fallers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.fallers.length > 0 ? (
              <div className="space-y-2">
                {data.fallers.map((r) => (
                  <div key={r.team_name} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
                    <div className="flex items-center gap-2">
                      <ArrowDownRight className="w-3 h-3 text-red-500" />
                      <span className="text-sm font-medium">{r.team_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-[hsl(var(--muted))]">{r.prev_win_prob.toFixed(1)}% → {r.win_prob.toFixed(1)}%</span>
                      <Badge className="bg-red-100 text-red-700">{r.delta_win.toFixed(1)}%</Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-[hsl(var(--muted))] italic py-4 text-center">No fallers detected.</div>
            )}
          </CardContent>
        </Card>
      </div>

      {data.momentum.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-blue-500" />
              All Changes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data.momentum.filter(m => m.direction !== "stable").slice(0, 20)}
                  layout="vertical"
                  margin={{ left: 100, right: 40 }}
                >
                  <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
                  <YAxis type="category" dataKey="team_name" tick={{ fontSize: 11 }} width={90} />
                  <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                  <Bar dataKey="delta_win" radius={[0, 4, 4, 0]} maxBarSize={20}>
                    {data.momentum.filter(m => m.direction !== "stable").slice(0, 20).map((entry, idx) => (
                      <Cell key={idx} fill={entry.delta_win >= 0 ? "#22c55e" : "#ef4444"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
