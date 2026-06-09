"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import type { CalibrationBin } from "@/lib/api";

interface Props {
  curve: CalibrationBin[];
}

export default function CalibrationCurveChart({ curve }: Props) {
  if (!curve || curve.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-4 text-center">
        No calibration curve data available.
      </div>
    );
  }

  const data = curve.map((b) => ({
    bin: `${(b.bin_lower * 100).toFixed(0)}-${(b.bin_upper * 100).toFixed(0)}%`,
    predicted: +(b.mean_predicted * 100).toFixed(1),
    actual: +(b.mean_actual * 100).toFixed(1),
    count: b.count,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="bin"
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
            formatter={(value: any, name: any) => [
              `${Number(value).toFixed(1)}%`,
              name === "predicted" ? "Predicted" : "Actual",
            ]}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11, paddingTop: 4 }} />
          <ReferenceLine
            y={0}
            stroke="#e5e7eb"
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4, fill: "#3b82f6" }}
            name="Predicted"
          />
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#22c55e"
            strokeWidth={2}
            dot={{ r: 4, fill: "#22c55e" }}
            name="Actual"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
