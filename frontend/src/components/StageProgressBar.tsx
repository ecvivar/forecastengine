"use client";

interface Stage {
  label: string;
  prob: number;
  color: string;
}

interface Props {
  stages: Stage[];
}

export default function StageProgressBar({ stages }: Props) {
  if (stages.length === 0) return null;

  const maxProb = Math.max(...stages.map((s) => s.prob), 1);

  return (
    <div className="space-y-1.5">
      {stages.map((s) => (
        <div key={s.label} className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-20 text-right shrink-0">
            {s.label}
          </span>
          <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${Math.max((s.prob / maxProb) * 100, 1)}%`,
                backgroundColor: s.color,
              }}
            />
          </div>
          <span className="text-xs font-medium w-12 text-right shrink-0">
            {s.prob.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}
