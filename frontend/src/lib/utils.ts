import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatProbability(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getStageLabel(stage: string): string {
  const labels: Record<string, string> = {
    group_stage: "Group Stage",
    round_of_32: "Round of 32",
    round_of_16: "Round of 16",
    quarter_final: "Quarter-Final",
    semi_final: "Semi-Final",
    third_place: "Third Place",
    final: "Final",
  };
  return labels[stage] || stage.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function getContinentColor(continent: string | null): string {
  const colors: Record<string, string> = {
    UEFA: "bg-blue-100 text-blue-800",
    CONMEBOL: "bg-green-100 text-green-800",
    CONCACAF: "bg-orange-100 text-orange-800",
    CAF: "bg-yellow-100 text-yellow-800",
    AFC: "bg-red-100 text-red-800",
    OFC: "bg-purple-100 text-purple-800",
  };
  return colors[continent || ""] || "bg-gray-100 text-gray-800";
}

export function getConfidenceColor(index: number | null): string {
  if (index === null || index === undefined) return "bg-gray-200 text-gray-700";
  if (index >= 80) return "bg-green-100 text-green-800";
  if (index >= 65) return "bg-blue-100 text-blue-800";
  if (index >= 50) return "bg-yellow-100 text-yellow-800";
  if (index >= 35) return "bg-orange-100 text-orange-800";
  return "bg-red-100 text-red-800";
}

export function getConfidenceLabel(index: number | null): string {
  if (index === null || index === undefined) return "N/A";
  if (index >= 80) return "Very High";
  if (index >= 65) return "High";
  if (index >= 50) return "Medium";
  if (index >= 35) return "Low";
  return "Very Low";
}

export function getProbColor(value: number): string {
  if (value >= 0.6) return "text-green-600";
  if (value >= 0.4) return "text-yellow-600";
  return "text-red-500";
}

export function getWinColor(value: number): string {
  if (value >= 50) return "text-green-600 font-bold";
  if (value >= 20) return "text-green-500";
  if (value >= 10) return "text-yellow-500";
  return "text-gray-400";
}
