"use client";

interface Props {
  homeWin: number;
  draw: number;
  awayWin: number;
  homeLabel?: string;
  awayLabel?: string;
  height?: number;
}

export default function ProbabilityBar({
  homeWin,
  draw,
  awayWin,
  homeLabel = "Home",
  awayLabel = "Away",
  height = 28,
}: Props) {
  const total = homeWin + draw + awayWin;
  const hw = total > 0 ? (homeWin / total) * 100 : 0;
  const dw = total > 0 ? (draw / total) * 100 : 0;
  const aw = total > 0 ? (awayWin / total) * 100 : 0;

  return (
    <div className="w-full">
      <div
        className="w-full rounded-full overflow-hidden flex"
        style={{ height }}
      >
        <div
          className="bg-blue-500 transition-all duration-500 flex items-center justify-center text-xs font-bold text-white"
          style={{ width: `${hw}%`, minWidth: hw > 8 ? undefined : 0 }}
        >
          {hw > 8 ? `${Math.round(hw)}%` : ""}
        </div>
        <div
          className="bg-gray-400 transition-all duration-500 flex items-center justify-center text-xs font-bold text-white"
          style={{ width: `${dw}%`, minWidth: dw > 8 ? undefined : 0 }}
        >
          {dw > 8 ? `${Math.round(dw)}%` : ""}
        </div>
        <div
          className="bg-red-500 transition-all duration-500 flex items-center justify-center text-xs font-bold text-white"
          style={{ width: `${aw}%`, minWidth: aw > 8 ? undefined : 0 }}
        >
          {aw > 8 ? `${Math.round(aw)}%` : ""}
        </div>
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span className="text-blue-600 font-medium">{homeLabel}</span>
        <span className="text-gray-500 font-medium">Draw</span>
        <span className="text-red-600 font-medium">{awayLabel}</span>
      </div>
    </div>
  );
}
