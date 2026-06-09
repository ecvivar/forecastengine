"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface Props {
  teamName: string;
  components: Record<string, number>;
}

const COMPONENT_LABELS: Record<string, string> = {
  elo: "Elo",
  form: "Form",
  xg: "xG",
  xga: "xGA",
  opponent_strength: "Opponent",
  wc_experience: "WC Exp",
  squad_quality: "Squad",
  tournament_history: "History",
};

const COMPONENT_ORDER = [
  "elo",
  "form",
  "xg",
  "xga",
  "opponent_strength",
  "wc_experience",
  "squad_quality",
  "tournament_history",
];

export default function TeamRadarChart({ teamName, components }: Props) {
  if (!components || Object.keys(components).length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-4 text-center">
        No component data available.
      </div>
    );
  }

  const data = COMPONENT_ORDER.filter((k) => k in components).map((key) => ({
    component: COMPONENT_LABELS[key] || key,
    value: Math.min(components[key], 100),
    fullMark: 100,
  }));

  return (
    <div>
      <h4 className="font-medium text-gray-700 mb-2 text-sm text-center">
        {teamName} — IGF Component Breakdown
      </h4>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="component"
            tick={{ fontSize: 10, fill: "#6b7280" }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fontSize: 9, fill: "#9ca3af" }}
            tickCount={5}
          />
          <Tooltip
            formatter={(value: any) => [`${Number(value).toFixed(1)}`, "Score"]}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              fontSize: 12,
            }}
          />
          <Radar
            dataKey="value"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.2}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
