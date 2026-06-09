"use client";

import {
  ResponsiveContainer,
  Treemap,
  Tooltip,
} from "recharts";
import type { GroupProb } from "@/lib/api";

interface GroupHeatmapData {
  name: string;
  children: {
    name: string;
    size: number;
    prob: number;
  }[];
  [key: string]: any;
}

interface Props {
  groups: Record<string, GroupProb[]>;
}

function probColor(prob: number): string {
  if (prob >= 75) return "#22c55e";
  if (prob >= 50) return "#84cc16";
  if (prob >= 30) return "#eab308";
  if (prob >= 15) return "#f97316";
  return "#ef4444";
}

export default function GroupHeatmap({ groups }: Props) {
  const groupNames = Object.keys(groups).sort();

  if (groupNames.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-4 text-center">
        No simulation data available.
      </div>
    );
  }

  const data: GroupHeatmapData[] = groupNames.map((g) => ({
    name: g,
    children: (groups[g] || []).map((t) => ({
      name: t.team_name,
      size: Math.max(t.qualify_r32_prob, 1),
      prob: t.qualify_r32_prob,
    })),
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={400}>
        <Treemap
          data={data as any}
          dataKey="size"
          aspectRatio={4 / 3}
          stroke="#fff"
          content={<CustomizedContent />}
        >
          <Tooltip
            content={<CustomTooltip />}
          />
        </Treemap>
      </ResponsiveContainer>
      <div className="flex items-center justify-center gap-4 mt-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-green-500 inline-block" /> ≥75%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-lime-500 inline-block" /> ≥50%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-yellow-500 inline-block" /> ≥30%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-orange-500 inline-block" /> ≥15%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-red-500 inline-block" /> &lt;15%
        </span>
      </div>
    </div>
  );
}

function CustomizedContent({ root, depth, x, y, width, height, index, payload }: any) {
  if (depth === 0) return null;

  const isGroup = depth === 1;
  const padding = isGroup ? 4 : 2;
  const fill = isGroup ? "#f8fafc" : probColor(payload.prob);
  const fontSize = isGroup ? 11 : Math.min(Math.max(width * 0.08, 9), 13);
  const name = payload.name || (isGroup ? `Group ${payload.name}` : "");

  return (
    <g>
      <rect
        x={x + (isGroup ? 1 : 0)}
        y={y + (isGroup ? 1 : 0)}
        width={width - (isGroup ? 2 : 0)}
        height={height - (isGroup ? 2 : 0)}
        fill={fill}
        stroke={isGroup ? "#e2e8f0" : "#fff"}
        strokeWidth={isGroup ? 1 : 0.5}
        rx={4}
      />
      {width > 30 && height > 20 && (
        <text
          x={x + width / 2}
          y={y + height / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={isGroup ? "#64748b" : "#fff"}
          fontSize={fontSize}
          fontWeight={isGroup ? 600 : 500}
        >
          {name}
        </text>
      )}
      {!isGroup && width > 40 && height > 36 && (
        <text
          x={x + width / 2}
          y={y + height / 2 + fontSize + 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill="rgba(255,255,255,0.85)"
          fontSize={Math.max(fontSize - 2, 9)}
        >
          {payload.prob.toFixed(1)}%
        </text>
      )}
    </g>
  );
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload || payload.length === 0) return null;
  const entry = payload[0]?.payload;
  if (!entry || !entry.prob) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-bold">{entry.name}</p>
      <p className="text-gray-500 mt-1">
        R32 Probability: <span className="font-bold text-green-600">{entry.prob.toFixed(1)}%</span>
      </p>
    </div>
  );
}
