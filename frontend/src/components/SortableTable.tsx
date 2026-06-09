"use client";

import { useState, useMemo, ReactNode } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  align?: "left" | "center" | "right";
  render: (row: T, index: number) => ReactNode;
  sortValue?: (row: T) => number | string;
}

interface Props<T> {
  columns: Column<T>[];
  data: T[];
  defaultSort?: { key: string; dir: "asc" | "desc" };
  mobileBreakpoint?: "sm" | "md" | "lg";
}

export default function SortableTable<T extends Record<string, any>>({
  columns,
  data,
  defaultSort,
}: Props<T>) {
  const [sortKey, setSortKey] = useState<string>(defaultSort?.key || columns[0]?.key || "");
  const [sortDir, setSortDir] = useState<"asc" | "desc">(defaultSort?.dir || "asc");

  const sorted = useMemo(() => {
    if (!sortKey) return data;
    const col = columns.find((c) => c.key === sortKey);
    return [...data].sort((a, b) => {
      const aVal = col?.sortValue ? col.sortValue(a) : a[sortKey];
      const bVal = col?.sortValue ? col.sortValue(b) : b[sortKey];
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "asc" ? aVal - bVal : bVal - aVal;
      }
      const aStr = String(aVal ?? "");
      const bStr = String(bVal ?? "");
      return sortDir === "asc" ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
    });
  }, [data, sortKey, sortDir, columns]);

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm whitespace-nowrap">
        <thead>
          <tr className="border-b text-gray-500 text-xs uppercase">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`py-2 px-2 ${
                  col.align === "right"
                    ? "text-right"
                    : col.align === "center"
                      ? "text-center"
                      : "text-left"
                } ${col.sortable !== false ? "cursor-pointer select-none hover:text-gray-700" : ""}`}
                onClick={() => col.sortable !== false && toggleSort(col.key)}
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {col.sortable !== false && (
                    sortKey === col.key ? (
                      sortDir === "asc" ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )
                    ) : (
                      <ChevronsUpDown className="w-3 h-3 text-gray-300" />
                    )
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr
              key={i}
              className="border-b border-gray-50 hover:bg-gray-50 transition-colors"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`py-2 px-2 ${
                    col.align === "right"
                      ? "text-right"
                      : col.align === "center"
                        ? "text-center"
                        : "text-left"
                  }`}
                >
                  {col.render(row, i)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
