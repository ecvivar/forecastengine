"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { SimulationResult } from "@/lib/api";

interface Props {
  results: SimulationResult[];
  numSimulations: number;
}

function barColor(prob: number): string {
  if (prob >= 10) return "#8b5cf6";
  if (prob >= 5) return "#3b82f6";
  if (prob >= 2) return "#22c55e";
  if (prob >= 1) return "#eab308";
  return "#94a3b8";
}

export default function DistributionHistogram({ results, numSimulations }: Props) {
  if (!results || results.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-4 text-center">
        No simulation results available.
      </div>
    );
  }

  const n = Math.max(numSimulations, 1);
  const data = [...results]
    .sort((a, b) => b.won_tournament - a.won_tournament)
    .map((r) => ({
      name: r.team_name,
      prob: (r.won_tournament / n) * 100,
      final: (r.reached_final / n) * 100,
    }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 9 }}
            angle={-45}
            textAnchor="end"
            height={80}
            axisLine={{ stroke: "#e5e7eb" }}
            tickLine={false}
            interval={0}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => `${v}%`}
            axisLine={{ stroke: "#e5e7eb" }}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: any, name: any) => [
              `${Number(value).toFixed(2)}%`,
              name === "prob" ? "Champion" : "Final",
            ]}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              fontSize: 12,
            }}
          />
          <Bar dataKey="prob" radius={[3, 3, 0, 0]} maxBarSize={14}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={barColor(entry.prob)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex items-center justify-center gap-4 mt-1 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-violet-500 inline-block" /> ≥10%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-blue-500 inline-block" /> ≥5%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-green-500 inline-block" /> ≥2%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-yellow-500 inline-block" /> ≥1%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gray-400 inline-block" /> &lt;1%
        </span>
      </div>
    </div>
  );
}
