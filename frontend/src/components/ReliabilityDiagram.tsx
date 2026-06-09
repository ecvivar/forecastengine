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
import type { ReliabilityCurve } from "@/lib/api";

interface Props {
  curve: ReliabilityCurve;
  title?: string;
}

export default function ReliabilityDiagram({ curve, title }: Props) {
  if (!curve || !curve.buckets || curve.buckets.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-4 text-center">
        No reliability data
      </div>
    );
  }

  const data = curve.buckets.map((b) => ({
    bucket: b.bucket_label,
    predicted: +(b.mean_predicted * 100).toFixed(1),
    observed: +(b.observed_frequency * 100).toFixed(1),
    count: b.count,
  }));

  return (
    <div>
      {title && <h4 className="font-medium text-gray-700 mb-2 text-sm">{title}</h4>}
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="bucket"
            tick={{ fontSize: 10 }}
            axisLine={{ stroke: "#e5e7eb" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v: number) => `${v}%`}
            domain={[0, 100]}
            axisLine={{ stroke: "#e5e7eb" }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
          <Bar
            dataKey="predicted"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
            maxBarSize={24}
            name="Predicted"
          />
          <Bar
            dataKey="observed"
            fill="#22c55e"
            radius={[4, 4, 0, 0]}
            maxBarSize={24}
            name="Observed"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
