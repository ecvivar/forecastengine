"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  scores: [string, number][] | null;
}

export default function ScorelineChart({ scores }: Props) {
  if (!scores || scores.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-4 text-center">
        No scoreline data available
      </div>
    );
  }

  const data = scores.map(([score, prob]) => ({
    score,
    probability: +(prob * 100).toFixed(1),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="score"
          tick={{ fontSize: 11 }}
          axisLine={{ stroke: "#e5e7eb" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={(v: any) => `${v}%`}
          axisLine={{ stroke: "#e5e7eb" }}
          tickLine={false}
        />
        <Tooltip
          formatter={(value: any) => [`${Number(value).toFixed(1)}%`, "Probability"]}
          contentStyle={{
            borderRadius: 8,
            border: "1px solid #e5e7eb",
            fontSize: 12,
          }}
        />
        <Bar
          dataKey="probability"
          fill="#3b82f6"
          radius={[4, 4, 0, 0]}
          maxBarSize={32}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
