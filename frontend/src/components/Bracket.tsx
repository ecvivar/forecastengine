"use client";
import { cn, getStageLabel } from "@/lib/utils";

interface BracketTeam {
  name: string;
  prob?: number;
  isWinner?: boolean;
}

interface BracketRound {
  name: string;
  matches: { top: BracketTeam; bottom: BracketTeam; score?: string }[];
}

interface Props {
  rounds: BracketRound[];
  className?: string;
}

export default function Bracket({ rounds, className }: Props) {
  if (!rounds || rounds.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic py-8 text-center">
        No bracket data available. Run a simulation first.
      </div>
    );
  }

  return (
    <div
      className={cn("flex gap-4 overflow-x-auto pb-4 min-h-[400px]", className)}
    >
      {rounds.map((round, ri) => (
        <div key={ri} className="flex flex-col justify-around min-w-[160px]">
          <div className="text-center text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
            {getStageLabel(round.name)}
          </div>
          {round.matches.map((match, mi) => (
            <div
              key={mi}
              className="border border-gray-200 rounded-lg px-3 py-2 mb-1 bg-white shadow-sm"
            >
              <div
                className={cn(
                  "text-sm py-1 border-b border-gray-100 flex justify-between",
                  match.top.isWinner && "font-bold text-green-700"
                )}
              >
                <span className="truncate max-w-[80px]">{match.top.name}</span>
                {match.top.prob !== undefined && (
                  <span className="text-xs text-gray-400 ml-1">
                    {match.top.prob.toFixed(0)}%
                  </span>
                )}
              </div>
              <div
                className={cn(
                  "text-sm py-1 flex justify-between",
                  match.bottom.isWinner && "font-bold text-green-700"
                )}
              >
                <span className="truncate max-w-[80px]">
                  {match.bottom.name}
                </span>
                {match.bottom.prob !== undefined && (
                  <span className="text-xs text-gray-400 ml-1">
                    {match.bottom.prob.toFixed(0)}%
                  </span>
                )}
              </div>
              {match.score && (
                <div className="text-xs text-center font-bold text-gray-600 mt-1">
                  {match.score}
                </div>
              )}
            </div>
          ))}
          {ri < rounds.length - 1 && (
            <div className="flex justify-center my-2">
              <div className="w-px h-4 bg-gray-300" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
