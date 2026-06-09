"use client";

interface Props {
  value: number;
  label?: string;
  size?: "sm" | "md" | "lg";
}

export default function ConfidenceGauge({ value, label, size = "md" }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  const dims = size === "sm" ? 80 : size === "lg" ? 140 : 100;
  const strokeWidth = size === "sm" ? 6 : size === "lg" ? 10 : 8;
  const radius = (dims - strokeWidth) / 2;
  const circumference = Math.PI * radius;
  const progress = (clamped / 100) * circumference;

  const getColor = (v: number) => {
    if (v >= 80) return "#22c55e";
    if (v >= 65) return "#3b82f6";
    if (v >= 50) return "#eab308";
    if (v >= 35) return "#f97316";
    return "#ef4444";
  };

  const color = getColor(clamped);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={dims} height={dims / 2 + 8}>
        <path
          d={`M ${strokeWidth / 2} ${dims / 2} A ${radius} ${radius} 0 0 1 ${dims - strokeWidth / 2} ${dims / 2}`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        <path
          d={`M ${strokeWidth / 2} ${dims / 2} A ${radius} ${radius} 0 0 1 ${dims - strokeWidth / 2} ${dims / 2}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference - progress}`}
          className="transition-all duration-700"
        />
        <text
          x={dims / 2}
          y={dims / 2 - 2}
          textAnchor="middle"
          className={`font-bold ${size === "sm" ? "text-[10px]" : size === "lg" ? "text-sm" : "text-xs"}`}
          fill={color}
        >
          {Math.round(clamped)}
        </text>
      </svg>
      {label && <span className="text-xs text-gray-500">{label}</span>}
    </div>
  );
}
