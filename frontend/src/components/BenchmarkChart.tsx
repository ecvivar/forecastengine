"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { BenchmarkEntry } from "@/lib/api";

interface Props {
  before: Record<string, BenchmarkEntry>;
  after: Record<string, BenchmarkEntry> | null;
  metric?: "brier_score" | "ece" | "accuracy";
  title?: string;
}

const METRIC_LABELS: Record<string, string> = {
  brier_score: "Brier Score (↓)",
  ece: "ECE (↓)",
  accuracy: "Accuracy (↑)",
};

const MODEL_COLORS: Record<string, string> = {
  elo: "#6b7280",
  poisson: "#ef4444",
  dixon_coles: "#f59e0b",
  full: "#3b82f6",
};

export default function BenchmarkChart({
  before,
  after,
  metric = "brier_score",
  title,
}: Props) {
  const modelOrder = ["elo", "poisson", "dixon_coles", "full"];
  const data = modelOrder
    .filter((m) => before[m])
    .map((m) => ({
      name: m.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      before: before[m][metric],
      after: after && after[m] ? after[m][metric] : undefined,
    }));

  const label = METRIC_LABELS[metric] || metric;

  return (
    <div>
      {title && <h4 className="font-medium text-gray-700 mb-2 text-sm">{title}</h4>}
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            axisLine={{ stroke: "#e5e7eb" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            axisLine={{ stroke: "#e5e7eb" }}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: any) => [Number(value).toFixed(4), label]}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
          <Bar
            dataKey="before"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
            name="Before Calibration"
          />
          {after && (
            <Bar
              dataKey="after"
              fill="#22c55e"
              radius={[4, 4, 0, 0]}
              maxBarSize={28}
              name="After Calibration"
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
