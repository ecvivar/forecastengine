"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useState } from "react";
import {
  Menu, X, LayoutDashboard, Shield, Swords, GitCompare,
  BarChart3, FlaskConical, BrainCircuit, Activity, History,
  Brackets, ChevronDown,
} from "lucide-react";

const navGroups = [
  {
    label: "Overview",
    items: [
      { label: "Command Center", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    label: "Tournament",
    items: [
      { label: "Overview", href: "/overview", icon: Shield },
      { label: "Teams", href: "/teams", icon: BarChart3 },
      { label: "Matches", href: "/matches", icon: Swords },
      { label: "Bracket", href: "/bracket", icon: Brackets },
    ],
  },
  {
    label: "Analysis",
    items: [
      { label: "Compare", href: "/compare", icon: GitCompare },
      { label: "Scenarios", href: "/scenarios", icon: FlaskConical },
      { label: "Explainability", href: "/explainability", icon: BrainCircuit },
    ],
  },
  {
    label: "Operations",
    items: [
      { label: "Monitoring", href: "/monitoring", icon: Activity },
      { label: "History", href: "/history", icon: History },
    ],
  },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

  const isActive = (href: string) => pathname === href;

  return (
    <header className="sticky top-0 z-50 border-b border-[hsl(var(--border))] bg-[hsl(var(--surface))]/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white text-xs font-bold">
            WC
          </div>
          <div>
            <span className="text-sm font-bold text-[hsl(var(--foreground))]">ForecastEngine</span>
            <span className="ml-2 text-[10px] font-medium text-[hsl(var(--muted))] uppercase tracking-wider">v1.0</span>
          </div>
        </Link>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-4">
          {navGroups.map((group) => (
            <div key={group.label} className="flex items-center gap-1">
              {group.items.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
                    isActive(item.href)
                      ? "bg-primary-50 text-primary-700"
                      : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-secondary))] hover:text-[hsl(var(--foreground))]"
                  )}
                >
                  <item.icon className="w-3.5 h-3.5" />
                  {item.label}
                </Link>
              ))}
            </div>
          ))}
        </div>

        {/* Mobile toggle */}
        <button
          className="lg:hidden p-2 text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-[hsl(var(--border))] bg-[hsl(var(--surface))] px-4 py-3 space-y-2">
          {navGroups.map((group) => (
            <div key={group.label}>
              <button
                onClick={() => setExpandedGroup(expandedGroup === group.label ? null : group.label)}
                className="flex items-center justify-between w-full px-2 py-1.5 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted))]"
              >
                {group.label}
                <ChevronDown className={cn("w-3 h-3 transition-transform", expandedGroup === group.label && "rotate-180")} />
              </button>
              {expandedGroup === group.label && (
                <div className="ml-2 space-y-1 mt-1">
                  {group.items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      className={cn(
                        "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive(item.href)
                          ? "bg-primary-50 text-primary-700"
                          : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-secondary))]"
                      )}
                    >
                      <item.icon className="w-4 h-4" />
                      {item.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </header>
  );
}
