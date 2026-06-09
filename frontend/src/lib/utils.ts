import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatProbability(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function getStageLabel(stage: string): string {
  const labels: Record<string, string> = {
    group_stage: "Group Stage",
    round_of_16: "Round of 16",
    quarter_final: "Quarter Final",
    semi_final: "Semi Final",
    third_place: "Third Place",
    final: "Final",
  };
  return labels[stage] || stage;
}

export function getContinentColor(continent: string | null): string {
  const colors: Record<string, string> = {
    "South America": "bg-green-100 text-green-800",
    "Europe": "bg-blue-100 text-blue-800",
    "Africa": "bg-yellow-100 text-yellow-800",
    "Asia": "bg-red-100 text-red-800",
    "North America": "bg-purple-100 text-purple-800",
    "Oceania": "bg-cyan-100 text-cyan-800",
  };
  return colors[continent || ""] || "bg-gray-100 text-gray-800";
}
