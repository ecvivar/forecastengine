"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useState, useRef, useEffect } from "react";
import {
  Menu, X, LayoutDashboard, Globe, Users, Flag, Swords, Brackets,
  LineChart, GitCompare, FlaskConical, BrainCircuit,
  Play, Map, History, Activity, BarChart3, TrendingUp, TrendingDown, FileText,
  Download, ChevronDown, Trophy, MessageSquare, Star,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: "World Cup",
    items: [
      { label: "Command Center", href: "/", icon: LayoutDashboard },
      { label: "Overview", href: "/overview", icon: Globe },
      { label: "Teams", href: "/teams", icon: Users },
      { label: "Groups", href: "/groups", icon: Flag },
      { label: "Matches", href: "/matches", icon: Swords },
      { label: "Bracket", href: "/bracket", icon: Brackets },
    ],
  },
  {
    label: "Predictions",
    items: [
      { label: "Match Predictor", href: "/predictions", icon: LineChart },
      { label: "Compare Teams", href: "/compare", icon: GitCompare },
      { label: "Scenarios", href: "/scenarios", icon: FlaskConical },
      { label: "Explainability", href: "/explainability", icon: BrainCircuit },
    ],
  },
  {
    label: "Simulation Lab",
    items: [
      { label: "Simulations", href: "/simulations", icon: Play },
      { label: "Explorer", href: "/explorer", icon: Map },
      { label: "History", href: "/history", icon: History },
    ],
  },
  {
    label: "Insights",
    items: [
      { label: "Momentum", href: "/momentum", icon: TrendingUp },
      { label: "Qualification", href: "/qualification", icon: Trophy },
      { label: "Executive", href: "/executive", icon: MessageSquare },
    ],
  },
  {
    label: "Model Operations",
    items: [
      { label: "Monitoring", href: "/monitoring", icon: Activity },
      { label: "Calibration", href: "/calibration", icon: BarChart3 },
      { label: "Rankings", href: "/rankings", icon: TrendingUp },
      { label: "Reports", href: "/reports", icon: FileText },
    ],
  },
  {
    label: "Data",
    items: [
      { label: "Export", href: "/export", icon: Download },
    ],
  },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isActive = (href: string) => pathname === href;
  const isGroupActive = (group: NavGroup) => group.items.some((item) => pathname.startsWith(item.href === "/" ? "/" : item.href));

  return (
    <header className="sticky top-0 z-50 border-b border-[hsl(var(--border))] bg-[hsl(var(--surface))]/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white text-xs font-bold">WC</div>
          <div>
            <span className="text-sm font-bold text-[hsl(var(--foreground))]">ForecastEngine</span>
            <span className="ml-2 text-[10px] font-medium text-[hsl(var(--muted))] uppercase tracking-wider">v1.0</span>
          </div>
        </Link>

        {/* Desktop: dropdown groups */}
        <div ref={dropdownRef} className="hidden lg:flex items-center gap-0.5">
          {navGroups.map((group) => (
            <div key={group.label} className="relative">
              <button
                onClick={() => setOpenDropdown(openDropdown === group.label ? null : group.label)}
                className={cn(
                  "flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors whitespace-nowrap",
                  isGroupActive(group)
                    ? "bg-primary-50 text-primary-700"
                    : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-secondary))] hover:text-[hsl(var(--foreground))]"
                )}
              >
                {group.label}
                <ChevronDown className={cn("w-3 h-3 transition-transform", openDropdown === group.label && "rotate-180")} />
              </button>
              {openDropdown === group.label && (
                <div className="absolute top-full left-0 mt-1 w-48 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--surface))] shadow-lg backdrop-blur-md p-1.5 space-y-0.5 z-50">
                  {group.items.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpenDropdown(null)}
                      className={cn(
                        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive(item.href)
                          ? "bg-primary-50 text-primary-700"
                          : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-secondary))] hover:text-[hsl(var(--foreground))]"
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
        <div className="lg:hidden border-t border-[hsl(var(--border))] bg-[hsl(var(--surface))] px-4 py-3 space-y-2 max-h-[80vh] overflow-y-auto">
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
